"""Tests del almacén de entregas en memoria y de las capacidades record/mark_consumed."""

from __future__ import annotations

from datetime import UTC, datetime

from jarvis.modules.heraldo.delivery import Delivery, DeliveryKind
from jarvis.modules.heraldo.in_memory_deliveries import InMemoryDeliveryStore
from jarvis.modules.heraldo.module import build_heraldo_module
from tests.heraldo_fakes import make_deps

NOW = datetime(2026, 7, 20, tzinfo=UTC)
EARLIER = datetime(2026, 7, 19, tzinfo=UTC)


def _delivery(delivery_id: str, topic_id: str, created_at: datetime) -> Delivery:
    return Delivery(
        id=delivery_id, topic_id=topic_id, kind=DeliveryKind.PODCAST, created_at=created_at
    )


async def test_latest_for_topic_returns_most_recent() -> None:
    store = InMemoryDeliveryStore()
    await store.add(_delivery("d1", "t1", EARLIER))
    await store.add(_delivery("d2", "t1", NOW))
    latest = await store.latest_for_topic("t1")
    assert latest is not None
    assert latest.id == "d2"


async def test_latest_for_topic_is_none_when_empty() -> None:
    assert await InMemoryDeliveryStore().latest_for_topic("t1") is None


async def test_mark_consumed_sets_timestamp() -> None:
    store = InMemoryDeliveryStore()
    await store.add(_delivery("d1", "t1", EARLIER))
    updated = await store.mark_consumed("d1", NOW)
    assert updated is not None
    assert updated.is_consumed


async def test_record_delivery_capability_persists_unconsumed() -> None:
    store = InMemoryDeliveryStore()
    deps = make_deps(deliveries=store, clock=lambda: NOW, new_id=lambda: "d1")
    capability = build_heraldo_module(deps).capability("record_delivery")

    output = await capability.invoke({"topic_id": "t1", "kind": "podcast"})

    assert output["delivery"]["id"] == "d1"
    assert output["delivery"]["consumed"] is False
    assert (await store.latest_for_topic("t1")) is not None


async def test_mark_consumed_capability_returns_updated_delivery() -> None:
    store = InMemoryDeliveryStore()
    await store.add(_delivery("d1", "t1", EARLIER))
    module = build_heraldo_module(make_deps(deliveries=store, clock=lambda: NOW))

    output = await module.capability("mark_delivery_consumed").invoke({"delivery_id": "d1"})

    assert output["delivery"]["consumed"] is True


async def test_mark_consumed_capability_none_when_missing() -> None:
    module = build_heraldo_module(make_deps(clock=lambda: NOW))
    output = await module.capability("mark_delivery_consumed").invoke({"delivery_id": "ghost"})
    assert output["delivery"] is None
