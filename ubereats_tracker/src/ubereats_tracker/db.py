"""Database engine + session helpers."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base

_DEFAULT_DB_PATH = Path.home() / ".ubereats_tracker" / "orders.db"


def default_db_url() -> str:
    """Resolve the database URL from env or fall back to a local SQLite file."""
    url = os.environ.get("UBEREATS_DB_URL")
    if url:
        return url
    _DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{_DEFAULT_DB_PATH}"


def make_engine(url: str | None = None) -> Engine:
    db_url = url or default_db_url()
    kwargs: dict = {"future": True}
    if db_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in db_url:
            kwargs["poolclass"] = StaticPool
    return create_engine(db_url, **kwargs)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
