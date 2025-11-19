"""Data models for catalog items and responses."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, HttpUrl, Field


class ItemKind(str, Enum):
    paper = "paper"
    repo = "repo"


class ScoredTag(BaseModel):
    tag: str
    weight: float = Field(ge=0, le=1)


class AnalysisResult(BaseModel):
    summary: str
    tags: List[ScoredTag]
    questions_answered: List[str]
    key_findings: List[str]
    relevance_score: float = Field(ge=0, le=10)
    interesting_score: float = Field(ge=0, le=10)
    embedding: Optional[List[float]] = None


class CatalogItem(BaseModel):
    id: str
    kind: ItemKind
    source_url: HttpUrl
    title: str
    abstract: Optional[str] = None
    created_at: datetime
    analysis: AnalysisResult
    similar_items: List[str] = []


class StatusPayload(BaseModel):
    mode: str
    message: str
    progress: float
    timestamp: datetime


class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    kind: Optional[ItemKind] = None


class TheoryRequest(BaseModel):
    theory: str
    limit: int = 10


class LinkAnalysisRequest(BaseModel):
    url: HttpUrl


class GraphNode(BaseModel):
    id: str
    title: str
    kind: ItemKind
    score: float


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class DashboardStats(BaseModel):
    total_items: int
    papers: int
    repos: int
    avg_relevance: float
    avg_interesting: float
    last_ingested: Optional[datetime]

