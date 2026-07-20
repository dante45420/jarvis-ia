"""Test de integración del adaptador pgvector contra un Postgres real.

Se salta salvo que JARVIS_TEST_DATABASE_URL apunte a un Postgres con pgvector alcanzable
(ej. el del docker-compose). El runtime real es Postgres en servidor, nunca SQLite.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from jarvis.adapters.pgvector_memory import PgVectorMemoryStore
from jarvis.domain.memory import ConversationTurn, EmbeddedFact, Fact
from jarvis.platform.db import create_engine, create_session_factory
from jarvis.platform.orm import Base

DATABASE_URL = os.environ.get("JARVIS_TEST_DATABASE_URL")
NOW = datetime(2026, 7, 17, tzinfo=UTC)
DIMENSIONS = 1024

pytestmark = pytest.mark.skipif(DATABASE_URL is None, reason="sin Postgres de integración")


def _vector(seed: float) -> list[float]:
    """Vector de dimensión completa con un valor constante, para pruebas determinísticas."""
    return [seed] * DIMENSIONS


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_engine(DATABASE_URL or "")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


async def test_append_and_read_recent_turns(engine: AsyncEngine) -> None:
    store = PgVectorMemoryStore(create_session_factory(engine))
    await store.append_turn(ConversationTurn("dante", "user", "hola", NOW))
    turns = await store.recent_turns("dante", 8)
    assert [t.content for t in turns] == ["hola"]


async def test_add_and_search_facts_by_similarity(engine: AsyncEngine) -> None:
    store = PgVectorMemoryStore(create_session_factory(engine))
    fact = Fact("dante", "usuario", "se_llama", "Dante", NOW)
    await store.add_facts([EmbeddedFact(fact, _vector(0.5))])
    hits = await store.search_facts("dante", _vector(0.5), k=5, min_similarity=0.9)
    assert hits[0].fact.object == "Dante"
    assert hits[0].similarity == pytest.approx(1.0, abs=1e-4)
