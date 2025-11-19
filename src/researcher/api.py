"""FastAPI backend for the research catalog application."""
import asyncio
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .models import Paper, Repository, SearchResult, TheoryResult, StatusUpdate
from .database import db
from .paper_cataloguer import paper_cataloguer
from .repo_cataloguer import repo_cataloguer
from .llm_service import llm_service


app = FastAPI(title="Research Catalog API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections for status updates
websocket_connections: List[WebSocket] = []


async def broadcast_status(status: StatusUpdate):
    """Broadcast status update to all connected clients."""
    disconnected = []
    for connection in websocket_connections:
        try:
            await connection.send_json(status.model_dump(mode='json'))
        except:
            disconnected.append(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        if conn in websocket_connections:
            websocket_connections.remove(conn)


# Set up status callbacks
def create_broadcast_callback():
    def callback(status: StatusUpdate):
        asyncio.create_task(broadcast_status(status))
    return callback

paper_cataloguer.set_status_callback(create_broadcast_callback())
repo_cataloguer.set_status_callback(create_broadcast_callback())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for realtime status updates."""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    # Send current status
    current_status = StatusUpdate(
        mode="idle",
        status="stopped",
        message="System idle"
    )
    await websocket.send_json(current_status.model_dump(mode='json'))
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


# API Models
class SearchRequest(BaseModel):
    query: str
    limit: int = 50


class TheoryRequest(BaseModel):
    theory: str


class ProcessURLRequest(BaseModel):
    url: str


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Research Catalog API"}


@app.get("/api/status")
async def get_status():
    """Get current system status."""
    return {
        "papers_running": paper_cataloguer.is_running,
        "repos_running": repo_cataloguer.is_running
    }


@app.post("/api/cataloguing/papers/start")
async def start_paper_cataloguing():
    """Start paper cataloguing."""
    if paper_cataloguer.is_running:
        raise HTTPException(status_code=400, detail="Paper cataloguing already running")
    
    asyncio.create_task(paper_cataloguer.start())
    return {"status": "started"}


@app.post("/api/cataloguing/papers/stop")
async def stop_paper_cataloguing():
    """Stop paper cataloguing."""
    paper_cataloguer.stop()
    return {"status": "stopped"}


@app.post("/api/cataloguing/repos/start")
async def start_repo_cataloguing():
    """Start repository cataloguing."""
    if repo_cataloguer.is_running:
        raise HTTPException(status_code=400, detail="Repository cataloguing already running")
    
    asyncio.create_task(repo_cataloguer.start())
    return {"status": "started"}


@app.post("/api/cataloguing/repos/stop")
async def stop_repo_cataloguing():
    """Stop repository cataloguing."""
    repo_cataloguer.stop()
    return {"status": "stopped"}


@app.post("/api/search", response_model=SearchResult)
async def search(request: SearchRequest):
    """Search papers and repositories."""
    papers = db.search_papers(request.query, request.limit)
    repos = db.search_repositories(request.query, request.limit)
    
    return SearchResult(
        papers=papers,
        repositories=repos,
        total=len(papers) + len(repos)
    )


@app.get("/api/papers/{paper_id}", response_model=Paper)
async def get_paper(paper_id: str):
    """Get a specific paper."""
    paper = db.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@app.get("/api/repositories/{repo_id}", response_model=Repository)
async def get_repository(repo_id: str):
    """Get a specific repository."""
    repo = db.get_repository(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@app.get("/api/papers", response_model=List[Paper])
async def list_papers(limit: int = 100):
    """List all papers."""
    papers = db.get_all_papers()
    return papers[:limit]


@app.get("/api/repositories", response_model=List[Repository])
async def list_repositories(limit: int = 100):
    """List all repositories."""
    repos = db.get_all_repositories()
    return repos[:limit]


@app.post("/api/process-url")
async def process_url(request: ProcessURLRequest):
    """Process a paper or repository URL."""
    url = request.url
    
    # Try paper first
    if 'arxiv.org' in url:
        paper = await paper_cataloguer.process_url(url)
        if paper:
            return {"type": "paper", "item": paper.model_dump(mode='json')}
    
    # Try repository
    if 'github.com' in url:
        repo = await repo_cataloguer.process_url(url)
        if repo:
            return {"type": "repository", "item": repo.model_dump(mode='json')}
    
    raise HTTPException(status_code=400, detail="URL not recognized as paper or repository")


@app.get("/api/similar/{item_id}")
async def get_similar(item_id: str):
    """Get similar papers and repositories."""
    similar = db.find_similar(item_id)
    return {
        "papers": [p.model_dump(mode='json') for p in similar["papers"]],
        "repositories": [r.model_dump(mode='json') for r in similar["repositories"]]
    }


@app.post("/api/theory", response_model=TheoryResult)
async def analyze_theory(request: TheoryRequest):
    """Analyze a theory or question."""
    theory = request.theory
    
    # Search for related papers and repos
    papers = db.search_papers(theory, limit=20)
    repos = db.search_repositories(theory, limit=20)
    
    # Use LLM to categorize and analyze
    papers_dict = [p.model_dump(mode='json') for p in papers]
    repos_dict = [r.model_dump(mode='json') for r in repos]
    
    analysis = llm_service.analyze_theory(theory, papers_dict, repos_dict)
    
    # For now, split papers/repos based on scores (simplified)
    # In a real implementation, the LLM would categorize them
    supporting_papers = papers[:len(papers)//2] if papers else []
    opposing_papers = papers[len(papers)//2:] if papers else []
    supporting_repos = repos[:len(repos)//2] if repos else []
    opposing_repos = repos[len(repos)//2:] if repos else []
    
    suggestions = analysis.get('suggestions', [])
    if len(papers) + len(repos) < 5:
        suggestions.append("Consider starting cataloguing mode to gather more data")
    
    return TheoryResult(
        supporting_papers=supporting_papers,
        opposing_papers=opposing_papers,
        supporting_repos=supporting_repos,
        opposing_repos=opposing_repos,
        related_theories=analysis.get('related_theories', []),
        suggestions=suggestions
    )


@app.get("/api/stats")
async def get_stats():
    """Get database statistics."""
    return db.get_stats()


@app.get("/api/graph")
async def get_graph():
    """Get graph data for visualization."""
    return db.get_graph_data()

