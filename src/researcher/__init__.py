from fastapi import FastAPI, APIRouter

def create_app() -> FastAPI:
    # Import here to avoid circular imports if any, or just for clean structure
    from .main import app
    return app

# For uv run researcher
def main():
    from .main import main as run_main
    run_main()