import asyncio
import os
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query as FastQuery, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .database import ResearchDatabase
from .ingestor import Ingestor
from .llm import LLMClient
from .models import ResearchItem, Relationship

# Singleton instances
db = ResearchDatabase()
llm = LLMClient()
ingestor = Ingestor(db, llm)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Start ingestor in background
    asyncio.create_task(ingestor.start())
    yield
    # Shutdown
    ingestor.stop()

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Research Catalog API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class SearchQuery(BaseModel):
    query: str
    mode: str = "text" # text or semantic

class TheoryQuery(BaseModel):
    theory: str

class StatsResponse(BaseModel):
    total_items: int
    total_papers: int
    total_repos: int
    total_relationships: int

# --- Endpoints ---

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    return db.get_stats()

@app.get("/api/status")
async def get_status():
    return {"ingesting": ingestor.running}

@app.post("/api/control/ingest")
async def control_ingest(enable: bool):
    if enable and not ingestor.running:
        asyncio.create_task(ingestor.start())
    elif not enable and ingestor.running:
        ingestor.stop()
    return {"ingesting": ingestor.running}

@app.get("/api/items", response_model=List[ResearchItem])
async def get_items(skip: int = 0, limit: int = 50):
    items = db.get_all_items()
    # Simple pagination in memory (TinyDB doesn't support native skip/limit well)
    return items[skip : skip + limit]

@app.get("/api/items/{item_id}", response_model=Optional[ResearchItem])
async def get_item(item_id: str):
    return db.get_item(item_id)

@app.get("/api/graph")
async def get_graph():
    # Return nodes and edges in format suitable for react-force-graph
    nodes = db.get_all_items()
    edges = db.get_relationships()
    
    # Format for frontend
    # react-force-graph expects { nodes: [{id, ...}], links: [{source, target, ...}] }
    return {
        "nodes": [item.model_dump() for item in nodes],
        "links": [edge.model_dump() for edge in edges]
    }

@app.post("/api/search", response_model=List[ResearchItem])
async def search(query: SearchQuery):
    if query.mode == "semantic":
        # Generate embedding
        emb = llm.get_embedding(query.query)
        results_with_score = db.search_similar(emb, top_k=20)
        return [item for item, _ in results_with_score]
    else:
        # Hybrid search (Text + optional semantic boost inside db.search logic if we wired it fully)
        # For now, db.search does text match.
        # Let's enhance db.search to support semantic if we want to pass it down?
        # But here we just use the methods we have.
        
        # If we want "smart" search, we should probably always try semantic or hybrid.
        # Let's use the database.search which does text matching.
        return db.search(query.query)

@app.post("/api/theory")
async def analyze_theory(query: TheoryQuery):
    # 1. Find relevant items
    emb = llm.get_embedding(query.theory)
    relevant_items_scores = db.search_similar(emb, top_k=10)
    relevant_items = [item.model_dump() for item, _ in relevant_items_scores]
    
    if not relevant_items:
        return {
            "answer": "Not enough data found to analyze this theory.",
            "related_items": []
        }

    # 2. Ask LLM
    answer = llm.answer_theory(query.theory, relevant_items)
    
    return {
        "answer": answer,
        "related_items": relevant_items
    }

from fastapi.responses import FileResponse

# Mount assets
if os.path.exists("frontend/dist/assets"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@app.get("/")
async def serve_root():
    print("Serving root...")
    if os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    return {"error": "Frontend not built (index.html missing)"}

# Catch-all for SPA (serve index.html for any other route)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="API endpoint not found")
        
    if os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    return {"error": "Frontend not built"}

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
