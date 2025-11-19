from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


@lru_cache(maxsize=1)
def get_settings() -> "Settings":
    load_dotenv()
    return Settings()  # type: ignore[call-arg]


class Settings:
    """
    Central configuration loaded from environment / .env.

    This stays intentionally small – enough for the PoC.
    """

    def __init__(self) -> None:
        self.base_dir = Path(os.getenv("RESEARCHER_BASE_DIR", Path.cwd()))
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.data_dir / "catalog.json"

        # LLM / embedding models – provided via .env
        self.default_model = os.getenv("DEFAULT_MODEL")
        self.embedding_model = os.getenv("DEFAULT_EMBEDDING_MODEL")

        if not self.default_model or not self.embedding_model:
            # Fail fast – the PoC relies on these being configured.
            raise RuntimeError(
                "DEFAULT_MODEL and DEFAULT_EMBEDDING_MODEL must be set in the environment/.env"
            )

        # Ingestion settings
        self.paper_poll_interval_seconds: int = int(
            os.getenv("PAPER_POLL_INTERVAL_SECONDS", "600")
        )
        self.repo_poll_interval_seconds: int = int(
            os.getenv("REPO_POLL_INTERVAL_SECONDS", "900")
        )

        # Similarity / graph settings
        self.similarity_threshold: float = float(
            os.getenv("SIMILARITY_THRESHOLD", "0.8")
        )
        self.max_neighbors: int = int(os.getenv("MAX_NEIGHBORS", "15"))

        # GitHub token is optional but avoids strict rate limits
        self.github_token: str | None = os.getenv("GITHUB_TOKEN")

