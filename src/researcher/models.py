"""Data models for papers and repositories."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Paper(BaseModel):
    """Model for a research paper."""
    id: str
    title: str
    authors: List[str]
    abstract: str
    arxiv_id: Optional[str] = None
    url: str
    published_date: Optional[datetime] = None
    summary: str
    tags: List[str] = Field(default_factory=list)
    questions_answered: List[str] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    relevancy_score: float = Field(ge=0, le=10)
    interesting_score: float = Field(ge=0, le=10)
    embedding: Optional[List[float]] = None
    ingested_at: datetime = Field(default_factory=datetime.now)
    content: Optional[str] = None  # Full paper text if downloaded


class Repository(BaseModel):
    """Model for a research repository."""
    id: str
    name: str
    owner: str
    description: str
    url: str
    github_url: Optional[str] = None
    language: Optional[str] = None
    stars: int = 0
    summary: str
    tags: List[str] = Field(default_factory=list)
    questions_answered: List[str] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    relevancy_score: float = Field(ge=0, le=10)
    interesting_score: float = Field(ge=0, le=10)
    embedding: Optional[List[float]] = None
    ingested_at: datetime = Field(default_factory=datetime.now)
    readme_content: Optional[str] = None


class SearchResult(BaseModel):
    """Search result containing papers and repositories."""
    papers: List[Paper] = Field(default_factory=list)
    repositories: List[Repository] = Field(default_factory=list)
    total: int = 0


class TheoryResult(BaseModel):
    """Result from theory mode query."""
    supporting_papers: List[Paper] = Field(default_factory=list)
    opposing_papers: List[Paper] = Field(default_factory=list)
    supporting_repos: List[Repository] = Field(default_factory=list)
    opposing_repos: List[Repository] = Field(default_factory=list)
    related_theories: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class StatusUpdate(BaseModel):
    """Status update for realtime feedback."""
    mode: str  # "papers", "repos", "idle"
    status: str  # "running", "stopped", "error"
    current_item: Optional[str] = None
    progress: Optional[dict] = None
    message: str = ""

