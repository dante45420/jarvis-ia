"""Tests de push: registrar el token del dispositivo y avisar por push los podcasts que tocan."""

from __future__ import annotations

from datetime import UTC, datetime

from jarvis.adapters.in_memory_push_tokens import InMemoryPushTokenStore
from jarvis.domain.notifications import PushToken
from jarvis.modules.heraldo.cadence import Cadence
from jarvis.modules.heraldo.domain import PodcastStyle, Topic, TopicProfile, TopicState
from jarvis.modules.heraldo.in_memory_topics import InMemoryTopicStore
from jarvis.modules.heraldo.module import build_heraldo_module
from tests.heraldo_fakes import FakePushSender, make_deps

NOW = datetime(2026, 7, 20, 8, tzinfo=UTC)


def _topic() -> Topic:
    return Topic(
        id="t1",
        owner_id="u1",
        name="IA para emprender",
        profile=TopicProfile(("ia",), (), (), reach_threshold=1, recency_hours=48),
        podcast_style=PodcastStyle.NARRATOR,
        state=TopicState.ACTIVE,
        cadence=Cadence(hour=8),
    )


async def test_register_push_token_saves_the_device() -> None:
    tokens = InMemoryPushTokenStore()
    deps = make_deps(push_tokens=tokens, clock=lambda: NOW)
    capability = build_heraldo_module(deps).capability("register_push_token")

    output = await capability.invoke(
        {"owner_id": "u1", "token": "ExponentPushToken[x]", "platform": "ios"}
    )

    assert output == {"ok": True}
    saved = await tokens.list_for_owner("u1")
    assert [item.token for item in saved] == ["ExponentPushToken[x]"]


async def test_tick_pushes_due_podcast_to_registered_devices() -> None:
    topics, tokens, push = InMemoryTopicStore(), InMemoryPushTokenStore(), FakePushSender()
    await topics.save(_topic())
    await tokens.save(PushToken("u1", "ExponentPushToken[x]", "ios", NOW))
    deps = make_deps(topics=topics, push_tokens=tokens, push=push, clock=lambda: NOW)
    capability = build_heraldo_module(deps).capability("run_scheduler_tick")

    output = await capability.invoke({"owner_id": "u1"})

    assert output == {"notified": 1, "topics": ["IA para emprender"]}
    sent_tokens, message = push.sent[0]
    assert sent_tokens == ["ExponentPushToken[x]"]
    assert message.data["topic_id"] == "t1"
    assert message.data["action"] == "approve_podcast"


async def test_tick_without_devices_notifies_no_one() -> None:
    topics, push = InMemoryTopicStore(), FakePushSender()
    await topics.save(_topic())
    deps = make_deps(topics=topics, push=push, clock=lambda: NOW)
    capability = build_heraldo_module(deps).capability("run_scheduler_tick")

    output = await capability.invoke({"owner_id": "u1"})

    assert output["notified"] == 0
    assert push.sent == []
