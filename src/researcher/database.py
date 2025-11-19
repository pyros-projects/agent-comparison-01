"""Database layer with GraphRAG capabilities."""
import json
import os
from typing import List, Optional, Dict, Any
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
import networkx as nx
from datetime import datetime

from .models import Paper, Repository
from .config import settings


class GraphRAGDatabase:
    """Database with graph capabilities for finding relationships."""
    
    def __init__(self):
        """Initialize the database and graph."""
        db_dir = os.path.dirname(settings.database_path) or '.'
        graph_dir = os.path.dirname(settings.graph_db_path) or '.'
        os.makedirs(db_dir, exist_ok=True)
        os.makedirs(graph_dir, exist_ok=True)
        
        self.db = TinyDB(settings.database_path, storage=CachingMiddleware(JSONStorage))
        self.papers_table = self.db.table('papers')
        self.repos_table = self.db.table('repositories')
        
        self.graph = nx.Graph()
        self._load_graph()
    
    def _load_graph(self):
        """Load graph from file if it exists."""
        if os.path.exists(settings.graph_db_path):
            try:
                with open(settings.graph_db_path, 'r') as f:
                    data = json.load(f)
                    # Handle both old and new format
                    if 'links' in data:
                        self.graph = nx.node_link_graph(data, edges="links")
                    else:
                        self.graph = nx.node_link_graph(data)
            except Exception:
                self.graph = nx.Graph()
    
    def _save_graph(self):
        """Save graph to file."""
        data = nx.node_link_data(self.graph, edges="links")
        with open(settings.graph_db_path, 'w') as f:
            json.dump(data, f)
    
    def add_paper(self, paper: Paper) -> None:
        """Add a paper to the database and graph."""
        # Use model_dump_json and parse to ensure proper serialization
        paper_dict = json.loads(paper.model_dump_json())
        
        self.papers_table.upsert(paper_dict, Query().id == paper.id)
        # For graph, convert datetime to strings manually
        graph_data = {}
        for key, value in paper.model_dump(exclude={'embedding', 'content'}).items():
            if isinstance(value, datetime):
                graph_data[key] = value.isoformat()
            elif value is not None:
                graph_data[key] = value
        self.graph.add_node(paper.id, type='paper', **graph_data)
        self._save_graph()
    
    def add_repository(self, repo: Repository) -> None:
        """Add a repository to the database and graph."""
        # Use model_dump_json and parse to ensure proper serialization
        repo_dict = json.loads(repo.model_dump_json())
        
        self.repos_table.upsert(repo_dict, Query().id == repo.id)
        # For graph, convert datetime to strings manually
        graph_data = {}
        for key, value in repo.model_dump(exclude={'embedding', 'readme_content'}).items():
            if isinstance(value, datetime):
                graph_data[key] = value.isoformat()
            elif value is not None:
                graph_data[key] = value
        self.graph.add_node(repo.id, type='repository', **graph_data)
        self._save_graph()
    
    def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Get a paper by ID."""
        result = self.papers_table.search(Query().id == paper_id)
        if result:
            return self._paper_from_dict(result[0])
        return None
    
    def get_repository(self, repo_id: str) -> Optional[Repository]:
        """Get a repository by ID."""
        result = self.repos_table.search(Query().id == repo_id)
        if result:
            return self._repo_from_dict(result[0])
        return None
    
    def _paper_from_dict(self, d: Dict[str, Any]) -> Paper:
        """Convert dict to Paper model."""
        d = d.copy()
        if isinstance(d.get('published_date'), str):
            d['published_date'] = datetime.fromisoformat(d['published_date'])
        if isinstance(d.get('ingested_at'), str):
            d['ingested_at'] = datetime.fromisoformat(d['ingested_at'])
        return Paper(**d)
    
    def _repo_from_dict(self, d: Dict[str, Any]) -> Repository:
        """Convert dict to Repository model."""
        d = d.copy()
        if isinstance(d.get('ingested_at'), str):
            d['ingested_at'] = datetime.fromisoformat(d['ingested_at'])
        return Repository(**d)
    
    def search_papers(self, query: str, limit: int = 50) -> List[Paper]:
        """Search papers by title, abstract, or tags."""
        query_lower = query.lower()
        results = []
        
        for paper_dict in self.papers_table.all():
            paper = self._paper_from_dict(paper_dict)
            if (query_lower in paper.title.lower() or 
                query_lower in paper.abstract.lower() or
                any(query_lower in tag.lower() for tag in paper.tags)):
                results.append(paper)
        
        return results[:limit]
    
    def search_repositories(self, query: str, limit: int = 50) -> List[Repository]:
        """Search repositories by name, description, or tags."""
        query_lower = query.lower()
        results = []
        
        for repo_dict in self.repos_table.all():
            repo = self._repo_from_dict(repo_dict)
            if (query_lower in repo.name.lower() or 
                query_lower in repo.description.lower() or
                any(query_lower in tag.lower() for tag in repo.tags)):
                results.append(repo)
        
        return results[:limit]
    
    def find_similar(self, item_id: str, limit: int = 10) -> Dict[str, List]:
        """Find similar papers/repos using graph structure and tags."""
        if item_id not in self.graph:
            return {"papers": [], "repositories": []}
        
        node_data = self.graph.nodes[item_id]
        item_tags = set(node_data.get('tags', []))
        item_type = node_data.get('type')
        
        similar_papers = []
        similar_repos = []
        
        # Find items with similar tags
        for other_id, other_data in self.graph.nodes(data=True):
            if other_id == item_id:
                continue
            
            other_tags = set(other_data.get('tags', []))
            overlap = len(item_tags & other_tags)
            
            if overlap > 0:
                similarity_score = overlap / max(len(item_tags), len(other_tags), 1)
                
                if other_data.get('type') == 'paper':
                    paper = self.get_paper(other_id)
                    if paper:
                        similar_papers.append((similarity_score, paper))
                elif other_data.get('type') == 'repository':
                    repo = self.get_repository(other_id)
                    if repo:
                        similar_repos.append((similarity_score, repo))
        
        # Sort by similarity and return top results
        similar_papers.sort(key=lambda x: x[0], reverse=True)
        similar_repos.sort(key=lambda x: x[0], reverse=True)
        
        return {
            "papers": [p[1] for p in similar_papers[:limit]],
            "repositories": [r[1] for r in similar_repos[:limit]]
        }
    
    def get_all_papers(self) -> List[Paper]:
        """Get all papers."""
        return [self._paper_from_dict(p) for p in self.papers_table.all()]
    
    def get_all_repositories(self) -> List[Repository]:
        """Get all repositories."""
        return [self._repo_from_dict(r) for r in self.repos_table.all()]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        papers = self.papers_table.all()
        repos = self.repos_table.all()
        
        return {
            "total_papers": len(papers),
            "total_repositories": len(repos),
            "graph_nodes": self.graph.number_of_nodes(),
            "graph_edges": self.graph.number_of_edges(),
            "avg_relevancy_papers": sum(p.get('relevancy_score', 0) for p in papers) / max(len(papers), 1),
            "avg_interesting_papers": sum(p.get('interesting_score', 0) for p in papers) / max(len(papers), 1),
            "avg_relevancy_repos": sum(r.get('relevancy_score', 0) for r in repos) / max(len(repos), 1),
            "avg_interesting_repos": sum(r.get('interesting_score', 0) for r in repos) / max(len(repos), 1),
        }
    
    def get_graph_data(self) -> Dict[str, Any]:
        """Get graph data for visualization."""
        nodes = []
        edges = []
        
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "type": data.get("type", "unknown"),
                "label": data.get("title") or data.get("name", node_id),
                **{k: v for k, v in data.items() if k not in ["title", "name", "type"]}
            })
        
        for source, target in self.graph.edges():
            edges.append({"source": source, "target": target})
        
        return {"nodes": nodes, "edges": edges}


# Global database instance
db = GraphRAGDatabase()

