"""Configuration helpers for the research catalog backend."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM / embeddings
    default_model: str = "gpt-4.1"
    default_embedding_model: str = "text-embedding-3-small"

    # Data and network
    data_path: Path = Path(".data/db.json")
    graph_similarity_threshold: float = 0.45

    # Ingestion
    arxiv_query: str = "cat:cs.AI"
    arxiv_batch_size: int = 6
    github_query: str = "topic:ai language model"
    github_batch_size: int = 6
    poll_interval_seconds: int = 900  # 15 minutes default

    # Optional tokens
    github_token: Optional[str] = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


__all__ = ["get_settings", "Settings"]
