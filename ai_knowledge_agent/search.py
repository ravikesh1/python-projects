"""Keyless web search via DuckDuckGo (the ``ddgs`` package).

Returns lightweight result records (title, url, snippet). Fetching/ingesting the
underlying pages is handled separately in :mod:`ai_knowledge_agent.ingest`.
"""

from __future__ import annotations

from dataclasses import dataclass

from ddgs import DDGS


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchError(RuntimeError):
    """Raised when a web search cannot be completed."""


def web_search(query: str, *, max_results: int = 5) -> list[SearchResult]:
    """Run a web search and return up to ``max_results`` results."""
    try:
        raw = list(DDGS().text(query, max_results=max_results))
    except Exception as exc:  # noqa: BLE001 - ddgs raises a variety of errors
        raise SearchError(f"Web search failed for {query!r}: {exc}") from exc

    results: list[SearchResult] = []
    for item in raw:
        url = item.get("href") or item.get("url") or ""
        if not url:
            continue
        results.append(
            SearchResult(
                title=(item.get("title") or url).strip(),
                url=url,
                snippet=(item.get("body") or "").strip(),
            )
        )
    return results
