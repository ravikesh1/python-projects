"""Environment-driven configuration for the AI Knowledge Agent.

Mirrors the ``Config.from_env()`` dataclass pattern used by
``mcp_mysql_server.server`` so both projects in this repo feel consistent.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DB_PATH = "~/.ai_knowledge_agent/knowledge.db"
DEFAULT_MODEL = "claude-opus-4-8"


@dataclass(frozen=True)
class Config:
    db_path: Path
    search_max_results: int
    ingest_max_chars: int
    request_timeout: float
    user_agent: str
    model: str

    @classmethod
    def from_env(cls) -> "Config":
        raw_path = os.getenv("KNOWLEDGE_DB_PATH", DEFAULT_DB_PATH)
        return cls(
            db_path=Path(raw_path).expanduser(),
            search_max_results=int(os.getenv("KNOWLEDGE_SEARCH_MAX_RESULTS", "5")),
            ingest_max_chars=int(os.getenv("KNOWLEDGE_INGEST_MAX_CHARS", "50000")),
            request_timeout=float(os.getenv("KNOWLEDGE_REQUEST_TIMEOUT", "30")),
            user_agent=os.getenv(
                "KNOWLEDGE_USER_AGENT",
                "ai-knowledge-agent/0.1 (+https://github.com/)",
            ),
            model=os.getenv("KNOWLEDGE_MODEL", DEFAULT_MODEL),
        )
