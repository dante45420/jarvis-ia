"""Tests del almacén de temas en memoria y de las capacidades create_topic/list_topics."""

from __future__ import annotations

from datetime import UTC, datetime

from jarvis.modules.core import Module
from jarvis.modules.heraldo.domain import (
    PodcastStyle,
    Topic,
    TopicProfile,
    TopicState,
)
from jarvis.modules.heraldo.in_memory_topics import InMemoryTopicStore
from jarvis.modules.heraldo.module import build_heraldo_module
from tests.heraldo_fakes import make_deps

NOW = datetime(2026, 7, 20, tzinfo=UTC)
_PROFILE = TopicProfile(("ia",), (), (), reach_threshold=1, recency_hours=48)


def _topic(topic_id: str, owner: str, state: TopicState = TopicState.ACTIVE) -> Topic:
    return Topic(
        id=topic_id,
        owner_id=owner,
        name="IA en medicina",
        profile=_PROFILE,
        podcast_style=PodcastStyle.NARRATOR,
        state=state,
    )


def _module(store: InMemoryTopicStore) -> Module:
    return build_heraldo_module(make_deps(topics=store, new_id=lambda: "topic-1"))


async def test_store_saves_and_recovers_topic() -> None:
    store = InMemoryTopicStore()
    await store.save(_topic("t1", "u1"))
    recovered = await store.get("t1")
    assert recovered is not None
    assert recovered.name == "IA en medicina"


async def test_store_lists_only_owner_topics() -> None:
    store = InMemoryTopicStore()
    await store.save(_topic("t1", "u1"))
    await store.save(_topic("t2", "u2"))
    assert [topic.id for topic in await store.list_by_owner("u1")] == ["t1"]


async def test_store_active_excludes_paused() -> None:
    store = InMemoryTopicStore()
    await store.save(_topic("t1", "u1"))
    await store.save(_topic("t2", "u1", state=TopicState.PAUSED))
    assert [topic.id for topic in await store.list_active("u1")] == ["t1"]


async def test_create_topic_capability_persists_and_returns_active_topic() -> None:
    store = InMemoryTopicStore()
    capability = _module(store).capability("create_topic")

    output = await capability.invoke(
        {"owner_id": "u1", "name": "IA en medicina", "subtopics": ["diagnóstico"]}
    )

    assert output["topic"]["id"] == "topic-1"
    assert output["topic"]["state"] == "active"
    assert (await store.get("topic-1")) is not None


async def test_list_topics_capability_returns_owner_topics() -> None:
    store = InMemoryTopicStore()
    await store.save(_topic("t1", "u1"))
    capability = _module(store).capability("list_topics")

    output = await capability.invoke({"owner_id": "u1"})

    assert [topic["id"] for topic in output["topics"]] == ["t1"]
