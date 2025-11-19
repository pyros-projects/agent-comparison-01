from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Iterable, List, Literal, Optional, Tuple
from urllib.parse import urlparse, urlunparse

import numpy as np
from tinydb import TinyDB, Query

from .config import get_settings


NodeKind = Literal["paper", "repo"]


@dataclass
class Node:
    id: str
    kind: NodeKind
    title: str
    source_url: str
    summary: str
    tags: List[str]
    questions_answered: List[str]
    key_findings: List[str]
    real_world_relevancy: float
    interestingness: float
    embedding: List[float]
    created_at: str


@dataclass
class Edge:
    id: str
    source_id: str
    target_id: str
    weight: float


class CatalogStore:
    """
    TinyDB-backed graph-ish store for papers and repositories.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._db = TinyDB(settings.db_path)
        self._nodes = self._db.table("nodes")
        self._edges = self._db.table("edges")

    # --- node helpers -------------------------------------------------

    def get_node_by_source(self, kind: NodeKind, source_url: str) -> Optional[Node]:
        source_url = normalize_source_url(kind, source_url)
        q = Query()
        doc = self._nodes.get((q.kind == kind) & (q.source_url == source_url))
        return Node(**doc) if doc else None

    def get_node(self, node_id: str) -> Optional[Node]:
        q = Query()
        doc = self._nodes.get(q.id == node_id)
        return Node(**doc) if doc else None

    def all_nodes(self) -> List[Node]:
        return [Node(**doc) for doc in self._nodes.all()]

    def upsert_node(self, node: Node) -> None:
        q = Query()
        if self._nodes.contains(q.id == node.id):
            self._nodes.update(asdict(node), q.id == node.id)
        else:
            self._nodes.insert(asdict(node))

    # --- edge helpers -------------------------------------------------

    def add_edge(self, edge: Edge) -> None:
        q = Query()
        if self._edges.contains(
            (q.source_id == edge.source_id) & (q.target_id == edge.target_id)
        ):
            self._edges.update(
                {"weight": edge.weight},
                (q.source_id == edge.source_id) & (q.target_id == edge.target_id),
            )
        else:
            self._edges.insert(asdict(edge))

    def neighbors(self, node_id: str) -> List[Tuple[Node, float]]:
        q = Query()
        docs = self._edges.search(q.source_id == node_id)
        results: List[Tuple[Node, float]] = []
        for doc in docs:
            target = self.get_node(doc["target_id"])
            if target:
                results.append((target, float(doc["weight"])))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    # --- similarity / graph building ---------------------------------

    def _cosine_similarity(self, a: Iterable[float], b: Iterable[float]) -> float:
        va = np.array(list(a), dtype="float32")
        vb = np.array(list(b), dtype="float32")
        denom = (np.linalg.norm(va) * np.linalg.norm(vb))
        if denom == 0:
            return 0.0
        return float(np.dot(va, vb) / denom)

    def connect_similar(self, node: Node) -> None:
        """
        For a newly added/updated node, create similarity edges to
        existing nodes. This is a minimal GraphRAG-style graph.
        """
        settings = get_settings()
        others = [n for n in self.all_nodes() if n.id != node.id]
        scored: List[Tuple[Node, float]] = []
        for other in others:
            score = self._cosine_similarity(node.embedding, other.embedding)
            if math.isnan(score):
                continue
            scored.append((other, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        for other, score in scored[: settings.max_neighbors]:
            if score < settings.similarity_threshold:
                break
            edge_id = f"{node.id}__{other.id}"
            self.add_edge(Edge(id=edge_id, source_id=node.id, target_id=other.id, weight=score))
            # store symmetric edge to simplify traversal
            edge_id_rev = f"{other.id}__{node.id}"
            self.add_edge(
                Edge(id=edge_id_rev, source_id=other.id, target_id=node.id, weight=score)
            )

    # --- search -------------------------------------------------------

    def search_by_embedding(
        self, query_embedding: List[float], limit: int = 20, kind: Optional[NodeKind] = None
    ) -> List[Tuple[Node, float]]:
        nodes = self.all_nodes()
        if kind:
            nodes = [n for n in nodes if n.kind == kind]

        scored: List[Tuple[Node, float]] = []
        for node in nodes:
            score = self._cosine_similarity(query_embedding, node.embedding)
            if math.isnan(score):
                continue
            scored.append((node, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    # --- stats --------------------------------------------------------

    def stats(self) -> dict:
        nodes = self.all_nodes()
        num_papers = sum(1 for n in nodes if n.kind == "paper")
        num_repos = sum(1 for n in nodes if n.kind == "repo")
        return {
            "total_nodes": len(nodes),
            "papers": num_papers,
            "repositories": num_repos,
        }


def new_node_id(kind: NodeKind, source_url: str) -> str:
    # Simple deterministic ID – stable across runs for a canonicalized URL.
    from hashlib import sha1

    source_url = normalize_source_url(kind, source_url)
    digest = sha1(f"{kind}:{source_url}".encode("utf8")).hexdigest()[:16]
    return f"{kind}_{digest}"


def normalize_source_url(kind: NodeKind, source_url: str) -> str:
    """
    Normalize external URLs so that we consistently recognize
    already-seen papers and repositories.
    """
    url = source_url.strip()
    if not url:
        return url

    parsed = urlparse(url)

    if kind == "paper" and "arxiv.org" in parsed.netloc:
        # Canonical form: https://arxiv.org/abs/<id>[vN]
        path = parsed.path or ""
        if "/abs/" in path:
            after = path.split("/abs/", 1)[1]
        else:
            after = path.lstrip("/")
        after = after.strip("/")
        path = f"/abs/{after}" if after else "/abs"
        parsed = parsed._replace(
            scheme="https",
            netloc="arxiv.org",
            path=path,
            params="",
            query="",
            fragment="",
        )
        return urlunparse(parsed)

    if kind == "repo" and "github.com" in parsed.netloc:
        # Canonical form: https://github.com/<owner>/<repo>
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 2:
            owner, repo = parts[0], parts[1]
            parsed = parsed._replace(
                scheme="https",
                netloc="github.com",
                path=f"/{owner}/{repo}",
                params="",
                query="",
                fragment="",
            )
            return urlunparse(parsed)

    return url


def make_node(
    *,
    kind: NodeKind,
    title: str,
    source_url: str,
    summary: str,
    tags: List[str],
    questions_answered: List[str],
    key_findings: List[str],
    real_world_relevancy: float,
    interestingness: float,
    embedding: List[float],
) -> Node:
    source_url = normalize_source_url(kind, source_url)
    return Node(
        id=new_node_id(kind, source_url),
        kind=kind,
        title=title,
        source_url=source_url,
        summary=summary,
        tags=tags,
        questions_answered=questions_answered,
        key_findings=key_findings,
        real_world_relevancy=real_world_relevancy,
        interestingness=interestingness,
        embedding=embedding,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
