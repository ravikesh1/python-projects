"""SQLite-based relational store (same concepts as MySQL)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "healthcare.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def setup(patients: list[dict]) -> None:
    """Create tables and insert patient records."""
    conn = get_connection()
    conn.execute("DROP TABLE IF EXISTS patients")
    conn.execute("""
        CREATE TABLE patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            condition TEXT NOT NULL,
            department TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.executemany(
        "INSERT INTO patients (name, age, condition, department, status) VALUES (?, ?, ?, ?, ?)",
        [(p["name"], p["age"], p["condition"], p["department"], p["status"]) for p in patients],
    )
    conn.commit()
    conn.close()


def query_exact(department: str) -> list[dict]:
    """Find patients by exact department match."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM patients WHERE department = ?", (department,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_like(keyword: str) -> list[dict]:
    """Find patients where condition contains a keyword (fuzzy but still literal)."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM patients WHERE condition LIKE ?", (f"%{keyword}%",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_filter(min_age: int, status: str) -> list[dict]:
    """Find patients by age threshold and status."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM patients WHERE age >= ? AND status = ?", (min_age, status)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_aggregate() -> list[dict]:
    """Count patients per department."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT department, COUNT(*) as patient_count FROM patients GROUP BY department ORDER BY patient_count DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
