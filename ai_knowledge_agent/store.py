"""SQLite-backed knowledge store with full-text search (FTS5).

The store keeps ingested documents (web pages, search results, etc.) and makes
them keyword-searchable. FTS5 is used when the local SQLite build supports it;
otherwise the store transparently falls back to ``LIKE`` matching.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _fts5_available() -> bool:
    """Detect whether the running SQLite build includes the FTS5 extension."""
    try:
        conn = sqlite3.connect(":memory:")
        try:
            conn.execute("CREATE VIRTUAL TABLE _probe USING fts5(x)")
            return True
        finally:
            conn.close()
    except sqlite3.OperationalError:
        return False


@dataclass
class KnowledgeStore:
    """A handle to the knowledge database.

    A new connection is opened per operation (SQLite is cheap to connect to and
    this keeps the store safe to share across threads / async tasks).
    """

    db_path: Path
    use_fts: bool = True

    def __post_init__(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.use_fts = self.use_fts and _fts5_available()
        self._init_db()

    # -- connection helpers ------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    url         TEXT UNIQUE,
                    title       TEXT NOT NULL DEFAULT '',
                    source      TEXT NOT NULL DEFAULT 'web',
                    fetched_at  TEXT NOT NULL,
                    content     TEXT NOT NULL DEFAULT ''
                )
                """
            )
            if self.use_fts:
                conn.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
                    USING fts5(
                        title, content,
                        content='documents', content_rowid='id'
                    )
                    """
                )
                conn.executescript(
                    """
                    CREATE TRIGGER IF NOT EXISTS documents_ai
                    AFTER INSERT ON documents BEGIN
                        INSERT INTO documents_fts(rowid, title, content)
                        VALUES (new.id, new.title, new.content);
                    END;
                    CREATE TRIGGER IF NOT EXISTS documents_ad
                    AFTER DELETE ON documents BEGIN
                        INSERT INTO documents_fts(documents_fts, rowid, title, content)
                        VALUES ('delete', old.id, old.title, old.content);
                    END;
                    CREATE TRIGGER IF NOT EXISTS documents_au
                    AFTER UPDATE ON documents BEGIN
                        INSERT INTO documents_fts(documents_fts, rowid, title, content)
                        VALUES ('delete', old.id, old.title, old.content);
                        INSERT INTO documents_fts(rowid, title, content)
                        VALUES (new.id, new.title, new.content);
                    END;
                    """
                )
            conn.commit()
        finally:
            conn.close()

    # -- writes ------------------------------------------------------------

    def add_document(
        self,
        *,
        title: str,
        content: str,
        url: str | None = None,
        source: str = "web",
    ) -> dict[str, Any]:
        """Insert a document, or update it in place if ``url`` already exists."""
        fetched_at = _now_iso()
        conn = self._connect()
        try:
            if url:
                cur = conn.execute(
                    """
                    INSERT INTO documents (url, title, source, fetched_at, content)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(url) DO UPDATE SET
                        title = excluded.title,
                        source = excluded.source,
                        fetched_at = excluded.fetched_at,
                        content = excluded.content
                    """,
                    (url, title, source, fetched_at, content),
                )
                conn.commit()
                row = conn.execute(
                    "SELECT id FROM documents WHERE url = ?", (url,)
                ).fetchone()
                doc_id = int(row["id"])
            else:
                cur = conn.execute(
                    """
                    INSERT INTO documents (url, title, source, fetched_at, content)
                    VALUES (NULL, ?, ?, ?, ?)
                    """,
                    (title, source, fetched_at, content),
                )
                conn.commit()
                doc_id = int(cur.lastrowid)
        finally:
            conn.close()
        return {
            "id": doc_id,
            "url": url,
            "title": title,
            "source": source,
            "fetched_at": fetched_at,
            "chars": len(content),
        }

    def delete_document(self, doc_id: int) -> bool:
        conn = self._connect()
        try:
            cur = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    # -- reads -------------------------------------------------------------

    @staticmethod
    def _fts_query(query: str) -> str:
        """Turn free text into a safe FTS5 MATCH expression (AND of phrases)."""
        tokens = [t for t in query.split() if t.strip()]
        if not tokens:
            return '""'
        return " ".join('"' + t.replace('"', '""') + '"' for t in tokens)

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            if self.use_fts:
                rows = conn.execute(
                    """
                    SELECT d.id, d.url, d.title, d.source, d.fetched_at,
                           snippet(documents_fts, 1, '«', '»', ' … ', 16) AS snippet,
                           bm25(documents_fts) AS score
                    FROM documents_fts
                    JOIN documents d ON d.id = documents_fts.rowid
                    WHERE documents_fts MATCH ?
                    ORDER BY score
                    LIMIT ?
                    """,
                    (self._fts_query(query), limit),
                ).fetchall()
            else:
                like = f"%{query}%"
                rows = conn.execute(
                    """
                    SELECT id, url, title, source, fetched_at,
                           substr(content, 1, 240) AS snippet,
                           0.0 AS score
                    FROM documents
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY fetched_at DESC
                    LIMIT ?
                    """,
                    (like, like, limit),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_document(self, doc_id: int) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_documents(self, limit: int = 50) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT id, url, title, source, fetched_at, length(content) AS chars
                FROM documents
                ORDER BY fetched_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def stats(self) -> dict[str, Any]:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS documents, COALESCE(SUM(length(content)), 0) AS chars "
                "FROM documents"
            ).fetchone()
            return {
                "documents": int(row["documents"]),
                "total_chars": int(row["chars"]),
                "fts_enabled": self.use_fts,
                "db_path": str(self.db_path),
            }
        finally:
            conn.close()
