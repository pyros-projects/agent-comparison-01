from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import get_settings
from .db import CatalogStore, NodeKind
from .ingest import IngestManager
from .llm import classify_theory_against_items, embed_text


settings = get_settings()
store = CatalogStore()
ingest_manager = IngestManager(store=store)

app = FastAPI(
    title="Research Catalog Database",
    description="Catalog and explore AI research papers and repositories.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str
    kind: Optional[NodeKind] = None
    limit: int = 20


class TheoryRequest(BaseModel):
    theory: str
    max_items: int = 25


class LinkAnalyzeRequest(BaseModel):
    url: str


@app.get("/api/status")
async def status() -> Dict[str, Any]:
    return {
        "ingest": {
            "papers": {
                "running": ingest_manager.paper_status.running,
                "last_error": ingest_manager.paper_status.last_error,
                "last_message": ingest_manager.paper_status.last_message,
            },
            "repositories": {
                "running": ingest_manager.repo_status.running,
                "last_error": ingest_manager.repo_status.last_error,
                "last_message": ingest_manager.repo_status.last_message,
            },
        },
        "stats": store.stats(),
    }


@app.get("/api/graph")
async def graph() -> Dict[str, Any]:
    """
    Lightweight graph view for the frontend.
    Nodes are papers/repos; edges capture similarity relationships.
    """
    nodes = store.all_nodes()
    node_payload = [
        {
            "id": node.id,
            "kind": node.kind,
            "title": node.title,
            "source_url": node.source_url,
            "real_world_relevancy": node.real_world_relevancy,
            "interestingness": node.interestingness,
        }
        for node in nodes
    ]

    # Collect edges via neighbors; deduplicate by (source, target)
    seen = set()
    edges_payload: List[Dict[str, Any]] = []
    for node in nodes:
        neighbors = store.neighbors(node.id)
        for neighbor, weight in neighbors:
            key = tuple(sorted((node.id, neighbor.id)))
            if key in seen:
                continue
            seen.add(key)
            edges_payload.append(
                {
                    "source": node.id,
                    "target": neighbor.id,
                    "weight": weight,
                }
            )

    return {"nodes": node_payload, "edges": edges_payload}


@app.post("/api/catalog/papers/start")
async def start_papers() -> Dict[str, Any]:
    ingest_manager.start_papers()
    return {"ok": True, "message": "Paper cataloguing mode started"}


@app.post("/api/catalog/papers/stop")
async def stop_papers() -> Dict[str, Any]:
    ingest_manager.stop_papers()
    return {"ok": True, "message": "Paper cataloguing mode stopped"}


@app.post("/api/catalog/repos/start")
async def start_repos() -> Dict[str, Any]:
    ingest_manager.start_repos()
    return {"ok": True, "message": "Repository cataloguing mode started"}


@app.post("/api/catalog/repos/stop")
async def stop_repos() -> Dict[str, Any]:
    ingest_manager.stop_repos()
    return {"ok": True, "message": "Repository cataloguing mode stopped"}


@app.post("/api/search")
async def search(req: SearchRequest) -> Dict[str, Any]:
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    query_embedding = await embed_text(req.query)
    results = store.search_by_embedding(
        query_embedding, limit=req.limit, kind=req.kind
    )

    return {
        "query": req.query,
        "results": [
            {
                "id": node.id,
                "kind": node.kind,
                "title": node.title,
                "source_url": node.source_url,
                "summary": node.summary,
                "tags": node.tags,
                "questions_answered": node.questions_answered,
                "key_findings": node.key_findings,
                "real_world_relevancy": node.real_world_relevancy,
                "interestingness": node.interestingness,
                "score": score,
            }
            for node, score in results
        ],
    }


@app.post("/api/theory")
async def theory(req: TheoryRequest) -> Dict[str, Any]:
    if not req.theory.strip():
        raise HTTPException(status_code=400, detail="theory must not be empty")

    # Use semantic search to find relevant items, then ask LLM to label stance.
    query_embedding = await embed_text(req.theory)
    scored = store.search_by_embedding(query_embedding, limit=req.max_items)

    if not scored:
        return {
            "theory": req.theory,
            "summary": "Too few relevant items in the catalog. Consider starting cataloguing mode.",
            "totals": {"agree": 0, "disagree": 0, "uncertain": 0},
            "items": [],
            "suggestions": [
                "Start cataloguing mode for papers and repositories.",
                "Try a broader or related wording for the theory.",
            ],
        }

    items = [
        {
            "id": node.id,
            "kind": node.kind,
            "title": node.title,
            "summary": node.summary,
        }
        for node, _ in scored
    ]
    labels = await classify_theory_against_items(req.theory, items)

    totals = {"agree": 0, "disagree": 0, "uncertain": 0}
    labeled_items: List[Dict[str, Any]] = []
    for node, score in scored:
        label = labels.get(node.id, "uncertain")
        totals[label] = totals.get(label, 0) + 1
        labeled_items.append(
            {
                "id": node.id,
                "kind": node.kind,
                "title": node.title,
                "source_url": node.source_url,
                "summary": node.summary,
                "stance": label,
                "score": score,
            }
        )

    suggestions: List[str] = []
    total_items = len(labeled_items)
    if total_items < 5:
        suggestions.append(
            "Too few items matched this theory. Try starting cataloguing mode or broadening the theory."
        )
    if totals["agree"] == 0 and totals["disagree"] == 0:
        suggestions.append("No clear agreement or disagreement; try phrasing the theory differently.")

    return {
        "theory": req.theory,
        "totals": totals,
        "items": labeled_items,
        "suggestions": suggestions,
    }


@app.post("/api/analyze/link")
async def analyze_link(req: LinkAnalyzeRequest) -> Dict[str, Any]:
    """
    Analyze a single paper or repository by URL, add it to the catalog,
    and return similar items.
    """
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="url must not be empty")

    # Simple heuristic routing based on URL
    if "arxiv.org" in url:
        kind: NodeKind = "paper"
        node = await _analyze_single_paper(url)
    elif "github.com" in url:
        kind = "repo"
        node = await _analyze_single_repo(url)
    else:
        raise HTTPException(
            status_code=400,
            detail="Only arXiv and GitHub URLs are supported in this PoC.",
        )

    # Find similar nodes
    embedding = node.embedding
    neighbors = store.search_by_embedding(embedding, limit=15, kind=None)
    neighbors = [(n, s) for n, s in neighbors if n.id != node.id]

    return {
        "node": {
            "id": node.id,
            "kind": node.kind,
            "title": node.title,
            "source_url": node.source_url,
            "summary": node.summary,
            "tags": node.tags,
            "questions_answered": node.questions_answered,
            "key_findings": node.key_findings,
            "real_world_relevancy": node.real_world_relevancy,
            "interestingness": node.interestingness,
        },
        "similar": [
            {
                "id": n.id,
                "kind": n.kind,
                "title": n.title,
                "source_url": n.source_url,
                "summary": n.summary,
                "score": score,
            }
            for n, score in neighbors
        ],
    }


async def _analyze_single_paper(url: str):
    import httpx
    from xml.etree import ElementTree

    # arXiv exposes an API where id: https://arxiv.org/abs/<id>
    # We fall back to a generic title if anything goes wrong.
    client = httpx.AsyncClient(timeout=20)
    try:
        # Extract ID from URL
        if "/abs/" in url:
            arxiv_id = url.split("/abs/")[-1]
        else:
            arxiv_id = url.rsplit("/", 1)[-1]
        api_url = "http://export.arxiv.org/api/query"
        params = {"id_list": arxiv_id}
        resp = await client.get(api_url, params=params)
        resp.raise_for_status()
        feed = ElementTree.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entry = feed.find("atom:entry", ns)
        if entry is None:
            raise RuntimeError("Could not find arXiv entry for given URL")

        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
        abstract = (
            entry.findtext("atom:summary", default="", namespaces=ns) or ""
        ).strip()
    finally:
        await client.aclose()

    from .db import make_node
    from .llm import summarize_paper

    llm_summary, tags, key_findings, relevance, interestingness = await summarize_paper(
        title=title, abstract=abstract, url=url
    )
    embedding = await embed_text(f"{title}\n\n{llm_summary}")
    node = make_node(
        kind="paper",
        title=title,
        source_url=url,
        summary=llm_summary,
        tags=tags,
        questions_answered=[],
        key_findings=key_findings,
        real_world_relevancy=relevance,
        interestingness=interestingness,
        embedding=embedding,
    )
    store.upsert_node(node)
    store.connect_similar(node)
    return node


async def _analyze_single_repo(url: str):
    import httpx

    parts = url.rstrip("/").split("/")
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")
    owner_repo = "/".join(parts[-2:])

    from .config import get_settings

    settings = get_settings()
    headers = {}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    client = httpx.AsyncClient(timeout=20, headers=headers)
    try:
        api_url = f"https://api.github.com/repos/{owner_repo}"
        resp = await client.get(api_url)
        resp.raise_for_status()
        data = resp.json()
        name = data.get("full_name") or owner_repo
        description = data.get("description") or ""

        readme_text = None
        try:
            readme_resp = await client.get(
                f"https://raw.githubusercontent.com/{owner_repo}/HEAD/README.md"
            )
            if readme_resp.status_code == 200:
                readme_text = readme_resp.text
        except Exception:  # noqa: BLE001
            readme_text = None
    finally:
        await client.aclose()

    from .llm import summarize_repository
    from .db import make_node

    llm_summary, tags, key_findings, relevance, interestingness = await summarize_repository(
        name=name,
        description=description,
        url=url,
        readme_text=readme_text,
    )
    embedding = await embed_text(f"{name}\n\n{llm_summary}")
    node = make_node(
        kind="repo",
        title=name,
        source_url=url,
        summary=llm_summary,
        tags=tags,
        questions_answered=[],
        key_findings=key_findings,
        real_world_relevancy=relevance,
        interestingness=interestingness,
        embedding=embedding,
    )
    store.upsert_node(node)
    store.connect_similar(node)
    return node
