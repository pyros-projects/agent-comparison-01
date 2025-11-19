from __future__ import annotations

import uvicorn


def main() -> None:
    """
    Entry point for `uv run researcher`.

    Starts the FastAPI backend that powers the research catalog.
    """
    uvicorn.run(
        "researcher.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
