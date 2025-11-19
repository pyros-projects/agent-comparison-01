"""TinyDB + NetworkX backed store with simple graph rag helpers."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import networkx as nx
import numpy as np
from tinydb import Query, TinyDB

from .config import get_settings
from .models import (
    AnalysisResult,
    CatalogItem,
    DashboardStats,
    GraphEdge,
    GraphNode,
    GraphResponse,
    ItemKind,
)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


class GraphStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = TinyDB(path)
        self.items_table = self.db.table("items")
        self.edges_table = self.db.table("edges")
        self.graph = nx.Graph()
        self._load_graph()
        self.settings = get_settings()

    def _load_graph(self) -> None:
        for doc in self.items_table.all():
            item = CatalogItem.model_validate(doc)
            self.graph.add_node(item.id, item=item)
        for edge in self.edges_table.all():
            self.graph.add_edge(edge["source"], edge["target"], weight=edge["weight"])

    def _persist_edge(self, source: str, target: str, weight: float) -> None:
        self.edges_table.upsert(
            {"source": source, "target": target, "weight": weight},
            (Query().source == source) & (Query().target == target),
        )

    def add_item(self, item: CatalogItem) -> CatalogItem:
        # ensure id uniqueness and idempotency
        existing = self.get(item.id)
        if existing:
            return existing
        if not item.id:
            item.id = str(uuid.uuid4())
        payload = json.loads(item.model_dump_json())
        self.items_table.upsert(payload, Query().id == item.id)
        self.graph.add_node(item.id, item=item)
        self._link_similar(item)
        return item

    def _link_similar(self, item: CatalogItem) -> None:
        if not item.analysis.embedding:
            return
        new_vec = np.array(item.analysis.embedding)
        for node_id, data in self.graph.nodes(data=True):
            if node_id == item.id:
                continue
            other: CatalogItem = data["item"]
            if not other.analysis.embedding:
                continue
            sim = _cosine(new_vec, np.array(other.analysis.embedding))
            if sim >= self.settings.graph_similarity_threshold:
                self.graph.add_edge(item.id, node_id, weight=sim)
                self._persist_edge(item.id, node_id, sim)

    def get(self, item_id: str) -> Optional[CatalogItem]:
        doc = self.items_table.get(Query().id == item_id)
        return CatalogItem.model_validate(doc) if doc else None

    def search(
        self, query: str, limit: int = 10, kind: Optional[ItemKind] = None, embedding: Optional[List[float]] = None
    ) -> List[CatalogItem]:
        # naive full text filter then rerank with embedding cosine
        docs = self.items_table.all()
        matches: List[Tuple[float, CatalogItem]] = []
        for doc in docs:
            item = CatalogItem.model_validate(doc)
            if kind and item.kind != kind:
                continue
            text_score = self._text_score(query, item)
            if embedding and item.analysis.embedding:
                sim = _cosine(np.array(embedding), np.array(item.analysis.embedding))
            else:
                sim = 0.0
            score = text_score * 0.4 + sim * 0.6
            matches.append((score, item))
        matches.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matches[:limit]]

    def _text_score(self, query: str, item: CatalogItem) -> float:
        q = query.lower()
        haystack = " ".join(
            [
                item.title,
                item.abstract or "",
                item.analysis.summary,
                " ".join([t.tag for t in item.analysis.tags]),
            ]
        ).lower()
        return min(1.0, haystack.count(q) / max(len(haystack), 1) * 80)

    def graph_snapshot(self, limit: int = 200) -> GraphResponse:
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        for i, (node_id, data) in enumerate(self.graph.nodes(data=True)):
            if i >= limit:
                break
            item: CatalogItem = data["item"]
            nodes.append(
                GraphNode(
                    id=node_id,
                    title=item.title,
                    kind=item.kind,
                    score=(item.analysis.relevance_score + item.analysis.interesting_score) / 2,
                )
            )
        for u, v, data in self.graph.edges(data=True):
            edges.append(GraphEdge(source=u, target=v, weight=float(data["weight"])))
        return GraphResponse(nodes=nodes, edges=edges)

    def dashboard_stats(self) -> DashboardStats:
        docs = self.items_table.all()
        total = len(docs)
        papers = sum(1 for d in docs if str(d.get("kind")) == ItemKind.paper.value)
        repos = total - papers
        avg_rel = (
            sum(d["analysis"]["relevance_score"] for d in docs) / total if total else 0.0
        )
        avg_interest = (
            sum(d["analysis"]["interesting_score"] for d in docs) / total if total else 0.0
        )
        last_ingest = None
        if docs:
            latest_raw = max(d["created_at"] for d in docs)
            if isinstance(latest_raw, str):
                try:
                    last_ingest = datetime.fromisoformat(latest_raw)
                except ValueError:
                    last_ingest = None
            else:
                last_ingest = latest_raw
        return DashboardStats(
            total_items=total,
            papers=papers,
            repos=repos,
            avg_relevance=round(avg_rel, 2),
            avg_interesting=round(avg_interest, 2),
            last_ingested=last_ingest,
        )

    def items_for_theory(self, theory: str, embedding: Optional[List[float]], limit: int = 10) -> List[CatalogItem]:
        kind = None
        return self.search(theory, limit=limit, kind=kind, embedding=embedding)


__all__ = ["GraphStore"]
