"""FastAPI app wiring routes together."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .ingest import IngestionManager
from .llm import analyze_payload, embed_text
from .models import (
    CatalogItem,
    GraphResponse,
    ItemKind,
    LinkAnalysisRequest,
    SearchRequest,
    TheoryRequest,
)
from .store import GraphStore


def create_app() -> FastAPI:
    settings = get_settings()
    store = GraphStore(settings.data_path)
    ingestion = IngestionManager(store)

    app = FastAPI(title="Research Catalog")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict:
        return {"ok": True, "time": datetime.utcnow().isoformat()}

    @app.post("/ingest/{kind}/start")
    async def start_ingest(kind: ItemKind):
        await ingestion.start(kind)
        return {"status": "started", "mode": kind}

    @app.post("/ingest/{kind}/stop")
    async def stop_ingest(kind: ItemKind):
        await ingestion.stop(kind)
        return {"status": "stopped", "mode": kind}

    @app.get("/status")
    async def status():
        return ingestion.get_status()

    @app.get("/ingestion/history")
    async def ingestion_history(limit: int = 100):
        return ingestion.get_history(limit=limit)

    @app.post("/search")
    async def search(payload: SearchRequest):
        query_vec = embed_text(payload.query)
        results = store.search(payload.query, limit=payload.limit, kind=payload.kind, embedding=query_vec)
        return results

    @app.post("/theory")
    async def theory(payload: TheoryRequest):
        vec = embed_text(payload.theory)
        results = store.items_for_theory(payload.theory, embedding=vec, limit=payload.limit)
        agree = [item for item in results if item.analysis.relevance_score >= 5.5]
        disagree = [item for item in results if item.analysis.relevance_score < 5.5]
        return {
            "theory": payload.theory,
            "support": agree,
            "oppose": disagree,
            "suggestions": _suggest_followups(payload.theory, results),
        }

    @app.get("/items/{item_id}")
    async def fetch_item(item_id: str):
        item = store.get(item_id)
        if not item:
            raise HTTPException(404, "item not found")
        neighbors = store.graph.neighbors(item_id) if item_id in store.graph else []
        return {"item": item, "neighbors": list(neighbors)}

    @app.post("/analyze-link")
    async def analyze_link(payload: LinkAnalysisRequest):
        # lightweight classifier: repo vs paper
        kind = ItemKind.repo if "github.com" in payload.url.host else ItemKind.paper
        analysis = analyze_payload(str(payload.url), "Fetched from link", kind.value)
        if not analysis.embedding:
            analysis.embedding = embed_text(str(payload.url))
        item = CatalogItem(
            id=str(hash(payload.url)),
            kind=kind,
            source_url=payload.url,
            title=str(payload.url),
            abstract="Link provided by user",
            created_at=datetime.utcnow(),
            analysis=analysis,
        )
        store.add_item(item)
        similar = store.search(item.title, limit=5, kind=None, embedding=analysis.embedding)
        return {"item": item, "similar": similar}

    @app.get("/graph")
    async def graph(limit: int = 200) -> GraphResponse:
        return store.graph_snapshot(limit=limit)

    @app.get("/items")
    async def list_items(kind: Optional[ItemKind] = None, limit: int = 200):
        docs = store.items_table.all()
        items = [CatalogItem.model_validate(d) for d in docs if not kind or d["kind"] == kind]
        return items[:limit]

    @app.get("/dashboard")
    async def dashboard():
        return store.dashboard_stats()

    return app


def _suggest_followups(theory: str, results: list[CatalogItem]) -> list[str]:
    if not results:
        return [
            "Broaden the scope or start cataloguing mode to gather more data.",
            f"Try related phrasing such as '{theory} in practice' or 'real-world evidence about {theory}'.",
        ]
    return [
        "Look for contrasting methods in adjacent subfields.",
        "Search for recent replications or benchmarks.",
    ]


app = create_app()
