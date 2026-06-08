"""High-level knowledge operations shared by the MCP server and the CLI agent.

This is the single source of truth for "what the Batcomputer can do": search the
web, ingest pages into the local knowledge base, and query that knowledge base.
Both surfaces (MCP + CLI) are thin wrappers over this class.
"""

from __future__ import annotations

from typing import Any

from .config import Config
from .fetch import FetchError, fetch_url
from .search import SearchError, web_search
from .store import KnowledgeStore


class Knowledge:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.from_env()
        self.store = KnowledgeStore(db_path=self.config.db_path)

    # -- web ---------------------------------------------------------------

    def search_web(self, query: str, max_results: int | None = None) -> list[dict[str, Any]]:
        n = max_results or self.config.search_max_results
        results = web_search(query, max_results=n)
        return [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in results]

    def ingest_url(self, url: str, source: str = "web") -> dict[str, Any]:
        page = fetch_url(
            url,
            timeout=self.config.request_timeout,
            user_agent=self.config.user_agent,
            max_chars=self.config.ingest_max_chars,
        )
        return self.store.add_document(
            title=page.title, content=page.text, url=page.url, source=source
        )

    def ingest_search(
        self, query: str, num_results: int | None = None
    ) -> dict[str, Any]:
        """Search the web and ingest the top results into the knowledge base."""
        n = num_results or self.config.search_max_results
        results = web_search(query, max_results=n)
        ingested: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        for r in results:
            try:
                doc = self.ingest_url(r.url, source="web_search")
                ingested.append(doc)
            except FetchError as exc:
                errors.append({"url": r.url, "error": str(exc)})
        return {
            "query": query,
            "found": len(results),
            "ingested": ingested,
            "errors": errors,
        }

    # -- knowledge base ----------------------------------------------------

    def search_knowledge(self, query: str, limit: int | None = None) -> list[dict[str, Any]]:
        return self.store.search(query, limit=limit or self.config.search_max_results)

    def get_document(self, doc_id: int) -> dict[str, Any] | None:
        return self.store.get_document(doc_id)

    def list_documents(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.store.list_documents(limit=limit)

    def delete_document(self, doc_id: int) -> bool:
        return self.store.delete_document(doc_id)

    def stats(self) -> dict[str, Any]:
        return self.store.stats()


__all__ = ["Knowledge", "FetchError", "SearchError"]
