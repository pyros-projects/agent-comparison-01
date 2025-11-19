"""Main entry point for the researcher application."""
import uvicorn
from .api import app

def main() -> None:
    """Run the FastAPI server."""
    uvicorn.run(app, host="0.0.0.0", port=8000)
