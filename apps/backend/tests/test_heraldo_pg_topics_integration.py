"""Test de integración de PgTopicStore contra un Postgres real.

Se salta salvo que JARVIS_TEST_DATABASE_URL apunte a un Postgres alcanzable (ej. docker-compose).
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from jarvis.modules.heraldo.domain import PodcastStyle, Topic, TopicProfile, TopicState
from jarvis.modules.heraldo.pg_topics import PgTopicStore
from jarvis.platform.db import create_engine, create_session_factory
from jarvis.platform.orm import Base

DATABASE_URL = os.environ.get("JARVIS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(DATABASE_URL is None, reason="sin Postgres de integración")

_PROFILE = TopicProfile(("ia",), ("modelo",), ("rumor",), reach_threshold=2, recency_hours=24)


def _topic(topic_id: str, owner: str, state: TopicState = TopicState.ACTIVE) -> Topic:
    return Topic(
        id=topic_id,
        owner_id=owner,
        name="IA en medicina",
        profile=_PROFILE,
        podcast_style=PodcastStyle.DIALOGUE,
        state=state,
    )


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_engine(DATABASE_URL or "")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


async def test_save_and_get_roundtrip_preserves_profile(engine: AsyncEngine) -> None:
    store = PgTopicStore(create_session_factory(engine))
    await store.save(_topic("t1", "u1"))
    recovered = await store.get("t1")
    assert recovered is not None
    assert recovered.profile.exclude_keywords == ("rumor",)
    assert recovered.podcast_style is PodcastStyle.DIALOGUE


async def test_save_upserts_on_same_id(engine: AsyncEngine) -> None:
    store = PgTopicStore(create_session_factory(engine))
    await store.save(_topic("t1", "u1"))
    await store.save(_topic("t1", "u1", state=TopicState.PAUSED))
    recovered = await store.get("t1")
    assert recovered is not None
    assert recovered.state is TopicState.PAUSED


async def test_list_active_excludes_paused(engine: AsyncEngine) -> None:
    store = PgTopicStore(create_session_factory(engine))
    await store.save(_topic("t1", "u1"))
    await store.save(_topic("t2", "u1", state=TopicState.PAUSED))
    assert [topic.id for topic in await store.list_active("u1")] == ["t1"]
