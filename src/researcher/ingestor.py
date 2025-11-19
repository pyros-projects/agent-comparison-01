import asyncio
import arxiv
import httpx
from datetime import datetime
from typing import List
import random
from .database import ResearchDatabase
from .models import ResearchItem, ItemType, Relationship
from .llm import LLMClient

class Ingestor:
    def __init__(self, db: ResearchDatabase, llm: LLMClient):
        self.db = db
        self.llm = llm
        self.running = False
        self.arxiv_client = arxiv.Client()
        self.processed_ids = set()

    async def start(self):
        self.running = True
        print("Starting ingestion...")
        while self.running:
            await self.ingest_papers()
            await self.ingest_repos()
            await asyncio.sleep(60) # Wait 1 minute between cycles

    def stop(self):
        self.running = False
        print("Stopping ingestion...")

    async def ingest_papers(self):
        print("Ingesting papers...")
        search = arxiv.Search(
            query="cat:cs.AI OR cat:cs.LG OR cat:cs.CL", 
            max_results=5,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )

        results = list(self.arxiv_client.results(search))
        
        for result in results:
            if not self.running: break
            if result.entry_id in self.processed_ids:
                continue
            
            existing = self.db.get_item(result.entry_id)
            if existing:
                self.processed_ids.add(result.entry_id)
                continue

            print(f"Analyzing paper: {result.title}")
            
            analysis = self.llm.analyze_paper(result.summary)
            # Generate embedding for title + summary
            text_for_embedding = f"{result.title}\n{analysis.get('summary', result.summary)}"
            embedding = self.llm.get_embedding(text_for_embedding)
            
            item = ResearchItem(
                id=result.entry_id,
                type=ItemType.PAPER,
                title=result.title,
                url=result.pdf_url,
                source="arxiv",
                summary=analysis.get("summary", result.summary),
                tags=analysis.get("tags", []),
                questions_answered=analysis.get("questions_answered", []),
                key_findings=analysis.get("key_findings", []),
                relevancy_score=analysis.get("relevancy_score", 0),
                interesting_score=analysis.get("interesting_score", 0),
                authors=[a.name for a in result.authors],
                published_date=result.published,
                content_text=result.summary,
                embedding=embedding
            )
            
            self.db.add_item(item)
            self.processed_ids.add(result.entry_id)
            
            await self.find_relationships(item)

    async def ingest_repos(self):
        print("Ingesting repos...")
        topics = ["machine-learning", "artificial-intelligence", "llm", "generative-ai"]
        topic = random.choice(topics)
        url = f"https://api.github.com/search/repositories?q=topic:{topic}&sort=updated&order=desc&per_page=5"
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers={"User-Agent": "Research-Catalog-Bot"})
                if resp.status_code == 200:
                    data = resp.json()
                    for repo in data.get("items", []):
                        if not self.running: break
                        repo_id = str(repo["id"])
                        repo_url = repo["html_url"]
                        
                        if self.db.get_item(repo_id):
                            continue

                        print(f"Analyzing repo: {repo['full_name']}")
                        
                        readme_url = f"https://raw.githubusercontent.com/{repo['full_name']}/{repo['default_branch']}/README.md"
                        readme_resp = await client.get(readme_url)
                        readme_text = readme_resp.text if readme_resp.status_code == 200 else "No README"
                        
                        file_structure = "src/\n  main.py\nREADME.md" 
                        
                        analysis = self.llm.analyze_repository(readme_text, file_structure)
                        
                        # Generate embedding
                        text_for_embedding = f"{repo['full_name']}\n{analysis.get('summary', '')}"
                        embedding = self.llm.get_embedding(text_for_embedding)

                        item = ResearchItem(
                            id=repo_id,
                            type=ItemType.REPOSITORY,
                            title=repo["full_name"],
                            url=repo_url,
                            source="github",
                            summary=analysis.get("summary", repo["description"] or ""),
                            tags=analysis.get("tags", []),
                            questions_answered=analysis.get("questions_answered", []),
                            key_findings=analysis.get("key_findings", []),
                            relevancy_score=analysis.get("relevancy_score", 0),
                            interesting_score=analysis.get("interesting_score", 0),
                            authors=[repo["owner"]["login"]],
                            published_date=datetime.strptime(repo["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                            content_text=readme_text,
                            embedding=embedding
                        )
                        
                        self.db.add_item(item)
                        await self.find_relationships(item)
            except Exception as e:
                print(f"Error ingesting repos: {e}")

    async def find_relationships(self, new_item: ResearchItem):
        # Production: Use similarity search to find candidates
        if not new_item.embedding:
            return

        # Find items that are semantically similar
        similar_items = self.db.search_similar(new_item.embedding, top_k=5, threshold=0.75)
        
        for existing, score in similar_items:
            if existing.id == new_item.id: continue
            
            print(f"Checking relationship between {new_item.title} and {existing.title} (Score: {score:.2f})")
            
            relation = self.llm.find_relationships(
                new_item.model_dump(), existing.model_dump()
            )
            
            if relation and relation.get("is_related"):
                rel = Relationship(
                    source_id=new_item.id,
                    target_id=existing.id,
                    type=relation.get("type", "related"),
                    description=relation.get("description", ""),
                    weight=relation.get("weight", float(score)) # Use similarity score as base weight? Or LLM weight?
                )
                self.db.add_relationship(rel)
                print(f"Found relationship: {new_item.title} <-> {existing.title}")