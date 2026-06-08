"""Fetch a URL and extract clean, readable text.

Uses ``httpx`` for the request (so we control timeouts and the user agent) and
``trafilatura`` for main-content extraction — it strips nav/boilerplate and is
well suited to articles and research papers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx
import trafilatura

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


@dataclass
class FetchedPage:
    url: str
    title: str
    text: str


class FetchError(RuntimeError):
    """Raised when a URL cannot be fetched or no readable text is found."""


def _fallback_title(html: str, url: str) -> str:
    match = _TITLE_RE.search(html)
    if match:
        title = re.sub(r"\s+", " ", match.group(1)).strip()
        if title:
            return title
    return url


def fetch_url(
    url: str,
    *,
    timeout: float = 30.0,
    user_agent: str = "ai-knowledge-agent/0.1",
    max_chars: int | None = None,
) -> FetchedPage:
    """Download ``url`` and return its title and main text content."""
    try:
        response = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": user_agent},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise FetchError(f"Could not fetch {url}: {exc}") from exc

    html = response.text
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        favor_recall=True,
    )
    if not text or not text.strip():
        raise FetchError(f"No readable text extracted from {url}")

    metadata = trafilatura.extract_metadata(html)
    title = (metadata.title if metadata and metadata.title else None) or _fallback_title(
        html, str(response.url)
    )

    text = text.strip()
    if max_chars is not None and len(text) > max_chars:
        text = text[:max_chars].rstrip() + "\n\n[... truncated ...]"

    return FetchedPage(url=str(response.url), title=title.strip(), text=text)
