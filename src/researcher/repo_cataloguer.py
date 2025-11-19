"""Repository cataloguing service for discovering and analyzing repositories."""
import asyncio
from datetime import datetime
from typing import Optional, Callable
import hashlib
import requests
from github import Github
import os

from .models import Repository, StatusUpdate
from .database import db
from .llm_service import llm_service


class RepositoryCataloguer:
    """Service for cataloguing research repositories from GitHub."""
    
    def __init__(self):
        """Initialize the repository cataloguer."""
        self.is_running = False
        self.status_callback: Optional[Callable[[StatusUpdate], None]] = None
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.github = Github(self.github_token) if self.github_token else None
    
    def set_status_callback(self, callback: Callable[[StatusUpdate], None]):
        """Set callback for status updates."""
        self.status_callback = callback
    
    def _update_status(self, message: str, current_item: Optional[str] = None):
        """Update status."""
        if self.status_callback:
            self.status_callback(StatusUpdate(
                mode="repos",
                status="running" if self.is_running else "stopped",
                current_item=current_item,
                message=message
            ))
    
    async def start(self):
        """Start cataloguing repositories."""
        self.is_running = True
        self._update_status("Starting repository cataloguing...")
        
        # Search queries for AI/ML repositories
        search_queries = [
            "machine learning",
            "deep learning",
            "neural network",
            "transformer",
            "LLM",
            "large language model",
            "AI research",
            "pytorch",
            "tensorflow"
        ]
        
        seen_ids = set()
        
        while self.is_running:
            try:
                if not self.github:
                    self._update_status("GitHub token not configured, using public API...")
                    # Fallback to public API without authentication (rate limited)
                    for query in search_queries:
                        if not self.is_running:
                            break
                        
                        self._update_status(f"Searching GitHub for: {query}")
                        
                        # Use GitHub REST API
                        url = f"https://api.github.com/search/repositories"
                        params = {
                            "q": f"{query} language:python stars:>10",
                            "sort": "updated",
                            "order": "desc",
                            "per_page": 10
                        }
                        
                        try:
                            response = requests.get(url, params=params, timeout=10)
                            if response.status_code == 200:
                                data = response.json()
                                
                                for repo_data in data.get('items', []):
                                    if not self.is_running:
                                        break
                                    
                                    repo_id = hashlib.md5(repo_data['full_name'].encode()).hexdigest()
                                    
                                    if repo_id in seen_ids:
                                        continue
                                    
                                    existing = db.get_repository(repo_id)
                                    if existing:
                                        seen_ids.add(repo_id)
                                        continue
                                    
                                    seen_ids.add(repo_id)
                                    
                                    self._update_status(f"Processing: {repo_data['full_name']}", 
                                                      current_item=repo_data['full_name'])
                                    
                                    await self._process_repository(repo_data)
                                    
                        except Exception as e:
                            print(f"Error searching GitHub: {e}")
                            self._update_status(f"Error searching: {str(e)}")
                        
                        await asyncio.sleep(10)  # Rate limiting
                else:
                    # Use PyGithub with authentication
                    for query in search_queries:
                        if not self.is_running:
                            break
                        
                        self._update_status(f"Searching GitHub for: {query}")
                        
                        try:
                            repos = self.github.search_repositories(
                                query=f"{query} language:python stars:>10",
                                sort="updated",
                                order="desc"
                            )
                            
                            count = 0
                            for repo in repos:
                                if not self.is_running or count >= 10:
                                    break
                                
                                repo_id = hashlib.md5(repo.full_name.encode()).hexdigest()
                                
                                if repo_id in seen_ids:
                                    continue
                                
                                existing = db.get_repository(repo_id)
                                if existing:
                                    seen_ids.add(repo_id)
                                    continue
                                
                                seen_ids.add(repo_id)
                                count += 1
                                
                                self._update_status(f"Processing: {repo.full_name}", 
                                                  current_item=repo.full_name)
                                
                                repo_data = {
                                    'full_name': repo.full_name,
                                    'name': repo.name,
                                    'description': repo.description or "",
                                    'html_url': repo.html_url,
                                    'language': repo.language,
                                    'stargazers_count': repo.stargazers_count,
                                    'owner': {'login': repo.owner.login}
                                }
                                
                                await self._process_repository(repo_data)
                                
                        except Exception as e:
                            print(f"Error searching GitHub: {e}")
                            self._update_status(f"Error searching: {str(e)}")
                        
                        await asyncio.sleep(2)  # Rate limiting
                
                # Wait before next round
                if self.is_running:
                    self._update_status("Waiting before next search cycle...")
                    await asyncio.sleep(300)  # 5 minutes between cycles
                    
            except Exception as e:
                print(f"Error in repository cataloguing: {e}")
                self._update_status(f"Error: {str(e)}")
                await asyncio.sleep(60)
        
        self._update_status("Repository cataloguing stopped")
    
    async def _process_repository(self, repo_data: dict):
        """Process a single repository."""
        try:
            # Get README content
            readme_content = None
            try:
                readme_url = f"https://raw.githubusercontent.com/{repo_data['full_name']}/main/README.md"
                response = requests.get(readme_url, timeout=5)
                if response.status_code == 200:
                    readme_content = response.text[:5000]  # Limit size
            except:
                pass
            
            # Analyze with LLM
            analysis = llm_service.analyze_repository(
                name=repo_data['name'],
                description=repo_data.get('description', ''),
                readme=readme_content
            )
            
            # Create repository object
            repo = Repository(
                id=hashlib.md5(repo_data['full_name'].encode()).hexdigest(),
                name=repo_data['name'],
                owner=repo_data['owner']['login'],
                description=repo_data.get('description', ''),
                url=repo_data.get('html_url', ''),
                github_url=repo_data.get('html_url', ''),
                language=repo_data.get('language'),
                stars=repo_data.get('stargazers_count', 0),
                summary=analysis['summary'],
                tags=analysis['tags'],
                questions_answered=analysis['questions_answered'],
                key_findings=analysis['key_findings'],
                relevancy_score=analysis['relevancy_score'],
                interesting_score=analysis['interesting_score'],
                readme_content=readme_content
            )
            
            # Add to database
            db.add_repository(repo)
            
            self._update_status(f"Added repository: {repo_data['full_name']}")
            
        except Exception as e:
            print(f"Error processing repository {repo_data.get('full_name', 'unknown')}: {e}")
            self._update_status(f"Error processing: {repo_data.get('full_name', 'unknown')}")
    
    def stop(self):
        """Stop cataloguing repositories."""
        self.is_running = False
        self._update_status("Stopping repository cataloguing...")
    
    async def process_url(self, url: str) -> Optional[Repository]:
        """Process a repository URL and add it to the database."""
        try:
            # Extract repo info from URL
            if 'github.com' in url:
                parts = url.replace('https://github.com/', '').replace('http://github.com/', '').split('/')
                if len(parts) >= 2:
                    owner = parts[0]
                    repo_name = parts[1].split('#')[0].split('?')[0]
                    full_name = f"{owner}/{repo_name}"
                    
                    # Check if already exists
                    repo_id = hashlib.md5(full_name.encode()).hexdigest()
                    existing = db.get_repository(repo_id)
                    if existing:
                        return existing
                    
                    # Fetch repo data
                    if self.github:
                        repo = self.github.get_repo(full_name)
                        repo_data = {
                            'full_name': repo.full_name,
                            'name': repo.name,
                            'description': repo.description or "",
                            'html_url': repo.html_url,
                            'language': repo.language,
                            'stargazers_count': repo.stargazers_count,
                            'owner': {'login': repo.owner.login}
                        }
                    else:
                        # Use REST API
                        api_url = f"https://api.github.com/repos/{full_name}"
                        response = requests.get(api_url, timeout=10)
                        if response.status_code != 200:
                            return None
                        repo_data = response.json()
                    
                    await self._process_repository(repo_data)
                    return db.get_repository(repo_id)
                    
        except Exception as e:
            print(f"Error processing repository URL: {e}")
            return None


repo_cataloguer = RepositoryCataloguer()

