"""Test de integración de PgDeliveryStore contra un Postgres real.

Se salta salvo que JARVIS_TEST_DATABASE_URL apunte a un Postgres alcanzable (ej. docker-compose).
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from jarvis.modules.heraldo.delivery import Delivery, DeliveryKind
from jarvis.modules.heraldo.pg_deliveries import PgDeliveryStore
from jarvis.platform.db import create_engine, create_session_factory
from jarvis.platform.orm import Base

DATABASE_URL = os.environ.get("JARVIS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(DATABASE_URL is None, reason="sin Postgres de integración")

NOW = datetime(2026, 7, 20, tzinfo=UTC)
EARLIER = datetime(2026, 7, 19, tzinfo=UTC)


def _delivery(delivery_id: str, topic_id: str, created_at: datetime) -> Delivery:
    return Delivery(
        id=delivery_id, topic_id=topic_id, kind=DeliveryKind.PODCAST, created_at=created_at
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


async def test_latest_for_topic_returns_most_recent(engine: AsyncEngine) -> None:
    store = PgDeliveryStore(create_session_factory(engine))
    await store.add(_delivery("d1", "t1", EARLIER))
    await store.add(_delivery("d2", "t1", NOW))
    latest = await store.latest_for_topic("t1")
    assert latest is not None
    assert latest.id == "d2"


async def test_mark_consumed_persists_timestamp(engine: AsyncEngine) -> None:
    store = PgDeliveryStore(create_session_factory(engine))
    await store.add(_delivery("d1", "t1", EARLIER))
    await store.mark_consumed("d1", NOW)
    latest = await store.latest_for_topic("t1")
    assert latest is not None
    assert latest.is_consumed
