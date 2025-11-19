"""Entry point for the research catalog backend."""

from __future__ import annotations

import uvicorn

from .api import app


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
