"""Shared pytest fixtures: in-memory SQLite session."""

from __future__ import annotations

from pathlib import Path

import pytest

from ubereats_tracker.db import init_db, make_engine, make_session_factory


SAMPLES = Path(__file__).resolve().parents[1] / "samples"


@pytest.fixture()
def session_factory():
    engine = make_engine("sqlite:///:memory:")
    init_db(engine)
    return make_session_factory(engine)


@pytest.fixture()
def session(session_factory):
    s = session_factory()
    try:
        yield s
        s.commit()
    finally:
        s.close()


@pytest.fixture()
def samples_dir() -> Path:
    return SAMPLES
