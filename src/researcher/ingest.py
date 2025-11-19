"""Background ingestion loops for papers and repositories."""

from __future__ import annotations

import asyncio
import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import httpx

from .config import get_settings
from .llm import analyze_payload, embed_text
from .models import CatalogItem, ItemKind, StatusPayload
from .store import GraphStore

log = logging.getLogger(__name__)


class IngestionManager:
    def __init__(self, store: GraphStore):
        self.store = store
        self.settings = get_settings()
        self.running: Dict[str, bool] = {"papers": False, "repos": False}
        self.status: Dict[str, StatusPayload] = {}
        self.history: List[StatusPayload] = []
        self._tasks: Dict[str, asyncio.Task] = {}

    async def start(self, mode: ItemKind) -> None:
        key = "papers" if mode == ItemKind.paper else "repos"
        if self.running.get(key):
            return
        self.running[key] = True
        task = asyncio.create_task(self._runner(mode))
        self._tasks[key] = task

    async def stop(self, mode: Optional[ItemKind] = None) -> None:
        targets = ["papers", "repos"] if mode is None else ([mode.value + "s"])
        for key in targets:
            self.running[key] = False
            if key in self._tasks:
                self._tasks[key].cancel()

    async def _runner(self, mode: ItemKind) -> None:
        poll = self.settings.poll_interval_seconds
        try:
            while self.running["papers" if mode == ItemKind.paper else "repos"]:
                started = time.time()
                try:
                    if mode == ItemKind.paper:
                        await self._ingest_papers()
                    else:
                        await self._ingest_repos()
                except Exception as exc:  # noqa: BLE001
                    log.exception("Ingest loop error: %s", exc)
                elapsed = time.time() - started
                sleep_for = max(1, poll - elapsed)
                await asyncio.sleep(sleep_for)
        finally:
            self.running["papers" if mode == ItemKind.paper else "repos"] = False

    async def _ingest_papers(self) -> None:
        query = quote_plus(self.settings.arxiv_query)
        url = f"http://export.arxiv.org/api/query?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results={self.settings.arxiv_batch_size}"
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, headers={"User-Agent": "research-catalog/0.1"})
        resp.raise_for_status()
        entries = self._parse_arxiv(resp.text)
        for entry in entries:
            analysis = analyze_payload(entry["title"], entry["summary"], "paper")
            if not analysis.embedding:
                analysis.embedding = embed_text(entry["title"] + "\n" + entry["summary"])
            item = CatalogItem(
                id=entry["id"],
                kind=ItemKind.paper,
                source_url=entry["link"],
                title=entry["title"],
                abstract=entry["summary"],
                created_at=entry["published"],
                analysis=analysis,
            )
            self.store.add_item(item)
            self._update_status("papers", f"Ingested paper: {item.title}")

    async def _ingest_repos(self) -> None:
        headers = {"Accept": "application/vnd.github+json"}
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"
        q = quote_plus(self.settings.github_query)
        url = f"https://api.github.com/search/repositories?q={q}&sort=updated&per_page={self.settings.github_batch_size}"
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        for repo in data.get("items", []):
            desc = repo.get("description") or ""
            title = repo["full_name"]
            analysis = analyze_payload(title, desc, "repository")
            if not analysis.embedding:
                analysis.embedding = embed_text(title + "\n" + desc)
            item = CatalogItem(
                id=str(repo["id"]),
                kind=ItemKind.repo,
                source_url=repo["html_url"],
                title=title,
                abstract=desc,
                created_at=datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00")),
                analysis=analysis,
            )
            self.store.add_item(item)
            self._update_status("repos", f"Ingested repo: {item.title}")

    def _update_status(self, mode: str, message: str) -> None:
        payload = StatusPayload(
            mode=mode,
            message=message,
            progress=1.0,
            timestamp=datetime.utcnow(),
        )
        self.status[mode] = payload
        self.history.append(payload)

    def get_status(self) -> List[StatusPayload]:
        return list(self.status.values())

    def get_history(self, limit: int = 50) -> List[StatusPayload]:
        return self.history[-limit:]

    def _parse_arxiv(self, xml_text: str) -> List[Dict]:
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries: List[Dict] = []
        for entry in root.findall("atom:entry", ns):
            title = (entry.find("atom:title", ns).text or "").strip()
            summary = (entry.find("atom:summary", ns).text or "").strip()
            link_el = entry.find('atom:link[@type="text/html"]', ns)
            link = link_el.attrib.get("href") if link_el is not None else ""
            id_text = (entry.find("atom:id", ns).text or "").split("/")[-1]
            published = entry.find("atom:published", ns).text
            entries.append(
                {
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "id": id_text,
                    "published": datetime.fromisoformat(published.replace("Z", "+00:00")),
                }
            )
        return entries


__all__ = ["IngestionManager"]
