from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

import httpx

from .db import CatalogStore, Node, make_node
from .llm import embed_text, summarize_paper, summarize_repository


@dataclass
class IngestStatus:
    running: bool = False
    last_error: Optional[str] = None
    last_message: Optional[str] = None


class IngestManager:
    """
    Owns background loops for cataloguing papers and repositories.
    """

    def __init__(self, store: CatalogStore) -> None:
        self.store = store
        self.paper_status = IngestStatus()
        self.repo_status = IngestStatus()
        self._paper_task: Optional[asyncio.Task] = None
        self._repo_task: Optional[asyncio.Task] = None

    # --- public API ---------------------------------------------------

    def start_papers(self) -> None:
        if self._paper_task and not self._paper_task.done():
            return
        self._paper_task = asyncio.create_task(self._paper_loop())

    def stop_papers(self) -> None:
        if self._paper_task:
            self._paper_task.cancel()
        self.paper_status.running = False

    def start_repos(self) -> None:
        if self._repo_task and not self._repo_task.done():
            return
        self._repo_task = asyncio.create_task(self._repo_loop())

    def stop_repos(self) -> None:
        if self._repo_task:
            self._repo_task.cancel()
        self.repo_status.running = False

    # --- internal loops ----------------------------------------------

    async def _paper_loop(self) -> None:
        from .config import get_settings

        settings = get_settings()
        self.paper_status.running = True
        # Follow redirects so that arXiv HTTP endpoints seamlessly upgrade to HTTPS.
        client = httpx.AsyncClient(timeout=20, follow_redirects=True)
        try:
            while True:
                try:
                    await self._ingest_recent_papers(client)
                    self.paper_status.last_error = None
                except Exception as exc:  # noqa: BLE001
                    self.paper_status.last_error = str(exc)
                await asyncio.sleep(settings.paper_poll_interval_seconds)
        finally:
            self.paper_status.running = False
            await client.aclose()

    async def _repo_loop(self) -> None:
        from .config import get_settings

        settings = get_settings()
        self.repo_status.running = True
        headers = {}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        client = httpx.AsyncClient(timeout=20, headers=headers)
        try:
            while True:
                try:
                    await self._ingest_recent_repos(client)
                    self.repo_status.last_error = None
                except Exception as exc:  # noqa: BLE001
                    self.repo_status.last_error = str(exc)
                await asyncio.sleep(settings.repo_poll_interval_seconds)
        finally:
            self.repo_status.running = False
            await client.aclose()

    # --- ingestion implementations -----------------------------------

    async def _ingest_recent_papers(self, client: httpx.AsyncClient) -> None:
        """
        Minimal arXiv ingestion:
        - query recent cs.AI papers
        - for each, analyze abstract with the LLM and store in the graph
        """
        from xml.etree import ElementTree

        from .config import get_settings

        settings = get_settings()
        base_url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": "cat:cs.AI",
            "sortBy": "lastUpdatedDate",
            "sortOrder": "descending",
            "max_results": 5,
        }
        resp = await client.get(base_url, params=params)
        resp.raise_for_status()
        feed = ElementTree.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = feed.findall("atom:entry", ns)

        for entry in entries:
            title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
            link = ""
            for link_el in entry.findall("atom:link", ns):
                if link_el.attrib.get("rel") == "alternate":
                    link = link_el.attrib.get("href", "")
                    break
            if not link:
                continue

            if self.store.get_node_by_source("paper", link):
                continue

            self.paper_status.last_message = f"Analyzing paper: {title}"
            (
                llm_summary,
                tags,
                key_findings,
                relevancy,
                interestingness,
            ) = await summarize_paper(title=title, abstract=summary, url=link)

            embedding = await embed_text(f"{title}\n\n{llm_summary}")
            node = make_node(
                kind="paper",
                title=title,
                source_url=link,
                summary=llm_summary,
                tags=tags,
                questions_answered=[],
                key_findings=key_findings,
                real_world_relevancy=relevancy,
                interestingness=interestingness,
                embedding=embedding,
            )
            self.store.upsert_node(node)
            self.store.connect_similar(node)

    async def _ingest_recent_repos(self, client: httpx.AsyncClient) -> None:
        """
        Minimal GitHub ingestion:
        - search for popular AI-related research repos
        - analyze repository metadata and README
        """
        search_url = "https://api.github.com/search/repositories"
        params = {
            "q": "topic:ai+language+model",
            "sort": "stars",
            "order": "desc",
            "per_page": 5,
        }
        resp = await client.get(search_url, params=params)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])

        for repo in items:
            html_url = repo.get("html_url")
            if not html_url:
                continue

            if self.store.get_node_by_source("repo", html_url):
                continue

            name = repo.get("full_name") or repo.get("name") or "Unknown"
            description = repo.get("description") or ""

            # Try to fetch README (best effort; ignore failures)
            readme_text: Optional[str] = None
            try:
                readme_resp = await client.get(
                    f"https://raw.githubusercontent.com/{repo['full_name']}/HEAD/README.md"
                )
                if readme_resp.status_code == 200:
                    readme_text = readme_resp.text
            except Exception:  # noqa: BLE001
                readme_text = None

            self.repo_status.last_message = f"Analyzing repo: {name}"
            (
                llm_summary,
                tags,
                key_findings,
                relevancy,
                interestingness,
            ) = await summarize_repository(
                name=name,
                description=description,
                url=html_url,
                readme_text=readme_text,
            )

            embedding = await embed_text(f"{name}\n\n{llm_summary}")
            node = make_node(
                kind="repo",
                title=name,
                source_url=html_url,
                summary=llm_summary,
                tags=tags,
                questions_answered=[],
                key_findings=key_findings,
                real_world_relevancy=relevancy,
                interestingness=interestingness,
                embedding=embedding,
            )
            self.store.upsert_node(node)
            self.store.connect_similar(node)
