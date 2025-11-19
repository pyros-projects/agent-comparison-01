"""Paper cataloguing service for discovering and analyzing papers."""
import asyncio
import arxiv
from datetime import datetime
from typing import Optional, Callable
import hashlib

from .models import Paper, StatusUpdate
from .database import db
from .llm_service import llm_service


class PaperCataloguer:
    """Service for cataloguing research papers from arXiv."""
    
    def __init__(self):
        """Initialize the paper cataloguer."""
        self.is_running = False
        self.status_callback: Optional[Callable[[StatusUpdate], None]] = None
    
    def set_status_callback(self, callback: Callable[[StatusUpdate], None]):
        """Set callback for status updates."""
        self.status_callback = callback
    
    def _update_status(self, message: str, current_item: Optional[str] = None):
        """Update status."""
        if self.status_callback:
            self.status_callback(StatusUpdate(
                mode="papers",
                status="running" if self.is_running else "stopped",
                current_item=current_item,
                message=message
            ))
    
    async def start(self):
        """Start cataloguing papers."""
        self.is_running = True
        self._update_status("Starting paper cataloguing...")
        
        # Search for AI/ML related papers
        search_queries = [
            "cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.CV OR cat:cs.NE",
            "machine learning",
            "deep learning",
            "neural networks",
            "transformer",
            "LLM",
            "large language model"
        ]
        
        seen_ids = set()
        
        while self.is_running:
            try:
                for query in search_queries:
                    if not self.is_running:
                        break
                    
                    self._update_status(f"Searching arXiv for: {query}")
                    
                    search = arxiv.Search(
                        query=query,
                        max_results=10,
                        sort_by=arxiv.SortCriterion.SubmittedDate,
                        sort_order=arxiv.SortOrder.Descending
                    )
                    
                    results = list(search.results())
                    
                    for result in results:
                        if not self.is_running:
                            break
                        
                        # Create unique ID
                        paper_id = hashlib.md5(result.entry_id.encode()).hexdigest()
                        
                        if paper_id in seen_ids:
                            continue
                        
                        # Check if already in database
                        existing = db.get_paper(paper_id)
                        if existing:
                            seen_ids.add(paper_id)
                            continue
                        
                        seen_ids.add(paper_id)
                        
                        self._update_status(f"Processing: {result.title}", current_item=result.title)
                        
                        # Download paper content (abstract only for now, full PDF would require more work)
                        try:
                            # Analyze with LLM
                            analysis = llm_service.analyze_paper(
                                title=result.title,
                                abstract=result.summary,
                                content=None  # Could download PDF here if needed
                            )
                            
                            # Create paper object
                            paper = Paper(
                                id=paper_id,
                                title=result.title,
                                authors=[author.name for author in result.authors],
                                abstract=result.summary,
                                arxiv_id=result.entry_id.split('/')[-1],
                                url=result.entry_id,
                                published_date=result.published,
                                summary=analysis['summary'],
                                tags=analysis['tags'],
                                questions_answered=analysis['questions_answered'],
                                key_findings=analysis['key_findings'],
                                relevancy_score=analysis['relevancy_score'],
                                interesting_score=analysis['interesting_score']
                            )
                            
                            # Add to database
                            db.add_paper(paper)
                            
                            self._update_status(f"Added paper: {result.title}")
                            
                        except Exception as e:
                            print(f"Error processing paper {result.title}: {e}")
                            self._update_status(f"Error processing: {result.title}")
                    
                    # Wait between searches
                    await asyncio.sleep(30)
                
                # Wait before next round
                if self.is_running:
                    self._update_status("Waiting before next search cycle...")
                    await asyncio.sleep(300)  # 5 minutes between cycles
                    
            except Exception as e:
                print(f"Error in paper cataloguing: {e}")
                self._update_status(f"Error: {str(e)}")
                await asyncio.sleep(60)
        
        self._update_status("Paper cataloguing stopped")
    
    def stop(self):
        """Stop cataloguing papers."""
        self.is_running = False
        self._update_status("Stopping paper cataloguing...")
    
    async def process_url(self, url: str) -> Optional[Paper]:
        """Process a paper URL and add it to the database."""
        try:
            # Extract arXiv ID from URL
            if 'arxiv.org' in url:
                arxiv_id = url.split('/')[-1].replace('.pdf', '').replace('.html', '')
                
                # Search for the paper
                search = arxiv.Search(id_list=[arxiv_id])
                results = list(search.results())
                
                if not results:
                    return None
                
                result = results[0]
                paper_id = hashlib.md5(result.entry_id.encode()).hexdigest()
                
                # Check if already exists
                existing = db.get_paper(paper_id)
                if existing:
                    return existing
                
                # Analyze
                analysis = llm_service.analyze_paper(
                    title=result.title,
                    abstract=result.summary
                )
                
                paper = Paper(
                    id=paper_id,
                    title=result.title,
                    authors=[author.name for author in result.authors],
                    abstract=result.summary,
                    arxiv_id=arxiv_id,
                    url=result.entry_id,
                    published_date=result.published,
                    summary=analysis['summary'],
                    tags=analysis['tags'],
                    questions_answered=analysis['questions_answered'],
                    key_findings=analysis['key_findings'],
                    relevancy_score=analysis['relevancy_score'],
                    interesting_score=analysis['interesting_score']
                )
                
                db.add_paper(paper)
                return paper
                
        except Exception as e:
            print(f"Error processing paper URL: {e}")
            return None


paper_cataloguer = PaperCataloguer()

