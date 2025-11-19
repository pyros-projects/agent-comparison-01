from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ItemType(str, Enum):
    PAPER = "paper"
    REPOSITORY = "repository"

class ResearchItem(BaseModel):
    id: str
    type: ItemType
    title: str
    url: str
    source: str  # arxiv, github, etc.
    summary: str = ""
    tags: List[str] = []
    questions_answered: List[str] = []
    key_findings: List[str] = []
    relevancy_score: float = 0.0
    interesting_score: float = 0.0
    authors: List[str] = []
    published_date: Optional[datetime] = None
    ingested_date: datetime = Field(default_factory=datetime.now)
    content_text: Optional[str] = None # Full text or readme content
    embedding: Optional[List[float]] = None # Vector embedding for similarity search

class Relationship(BaseModel):
    source_id: str
    target_id: str
    type: str # e.g., "related_to", "cites", "implements"
    description: str = ""
    weight: float = 1.0

class GraphData(BaseModel):
    nodes: List[ResearchItem]
    edges: List[Relationship]
