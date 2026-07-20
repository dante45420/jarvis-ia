"""Tests del scheduler: decide generar o pausar por tema, sin afectar a los demás."""

from __future__ import annotations

from datetime import UTC, datetime

from jarvis.modules.heraldo.delivery import Delivery, DeliveryKind
from jarvis.modules.heraldo.domain import PodcastStyle, Topic, TopicProfile, TopicState
from jarvis.modules.heraldo.in_memory_deliveries import InMemoryDeliveryStore
from jarvis.modules.heraldo.in_memory_topics import InMemoryTopicStore
from jarvis.modules.heraldo.pause import PauseController
from jarvis.modules.heraldo.scheduler import TopicScheduler
from tests.heraldo_fakes import FakeInbox

NOW = datetime(2026, 7, 20, tzinfo=UTC)
EARLIER = datetime(2026, 7, 19, tzinfo=UTC)
_PROFILE = TopicProfile(("ia",), (), (), reach_threshold=1, recency_hours=48)


def _topic(topic_id: str, state: TopicState = TopicState.ACTIVE) -> Topic:
    return Topic(
        id=topic_id,
        owner_id="u1",
        name=f"Tema {topic_id}",
        profile=_PROFILE,
        podcast_style=PodcastStyle.NARRATOR,
        state=state,
    )


def _delivery(topic_id: str, *, consumed: bool) -> Delivery:
    return Delivery(
        id=f"d-{topic_id}",
        topic_id=topic_id,
        kind=DeliveryKind.PODCAST,
        created_at=EARLIER,
        consumed_at=NOW if consumed else None,
    )


def _scheduler(topics: InMemoryTopicStore, deliveries: InMemoryDeliveryStore) -> TopicScheduler:
    return TopicScheduler(topics, deliveries, PauseController(FakeInbox()))


async def test_generates_topics_without_pending() -> None:
    topics = InMemoryTopicStore()
    await topics.save(_topic("t1"))
    ready = await _scheduler(topics, InMemoryDeliveryStore()).topics_to_generate("u1", NOW)
    assert [topic.id for topic in ready] == ["t1"]


async def test_generates_when_pending_is_consumed() -> None:
    topics, deliveries = InMemoryTopicStore(), InMemoryDeliveryStore()
    await topics.save(_topic("t1"))
    await deliveries.add(_delivery("t1", consumed=True))
    ready = await _scheduler(topics, deliveries).topics_to_generate("u1", NOW)
    assert [topic.id for topic in ready] == ["t1"]


async def test_pauses_topic_with_unconsumed_pending() -> None:
    topics, deliveries = InMemoryTopicStore(), InMemoryDeliveryStore()
    await topics.save(_topic("t1"))
    await deliveries.add(_delivery("t1", consumed=False))

    ready = await _scheduler(topics, deliveries).topics_to_generate("u1", NOW)

    assert ready == []
    paused = await topics.get("t1")
    assert paused is not None
    assert paused.state is TopicState.PAUSED


async def test_pause_of_one_topic_does_not_block_another() -> None:
    topics, deliveries = InMemoryTopicStore(), InMemoryDeliveryStore()
    await topics.save(_topic("blocked"))
    await topics.save(_topic("free"))
    await deliveries.add(_delivery("blocked", consumed=False))

    ready = await _scheduler(topics, deliveries).topics_to_generate("u1", NOW)

    assert [topic.id for topic in ready] == ["free"]
