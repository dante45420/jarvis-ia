"""Tests del cableado de generación: la instrucción del onboarding entra al guion y se recuerda
el ángulo; la cadencia decide qué temas tocan ahora."""

from __future__ import annotations

from datetime import UTC, datetime

from jarvis.adapters.null_embedding import NullEmbeddingProvider
from jarvis.modules.heraldo.angles import AngleMemory
from jarvis.modules.heraldo.cadence import Cadence, Frequency
from jarvis.modules.heraldo.delivery import Delivery, DeliveryKind
from jarvis.modules.heraldo.domain import PodcastStyle, Topic, TopicProfile, TopicState
from jarvis.modules.heraldo.in_memory_angles import InMemoryAngleStore
from jarvis.modules.heraldo.in_memory_deliveries import InMemoryDeliveryStore
from jarvis.modules.heraldo.in_memory_topics import InMemoryTopicStore
from jarvis.modules.heraldo.module import build_heraldo_module
from jarvis.modules.heraldo.onboarding import Objective, OnboardingForm, Style, TopicQuestion
from jarvis.modules.heraldo.podcast_service import PodcastService
from tests.heraldo_fakes import FakeAudioStorage, FakeCompleter, FakeSynthesizer, make_deps

NOW = datetime(2026, 7, 20, 8, tzinfo=UTC)
_SCRIPT = '{"title": "Ep", "script": "hola", "angle": "el rol del criterio"}'
_STORY = {"id": "s1", "title": "Titular", "snippet": "contexto", "url": "https://x.cl/s1",
          "sources": ["Medio A"]}


def _topic_with_onboarding() -> Topic:
    form = OnboardingForm(
        objective=Objective.LEARN_SKILL,
        style=Style(),
        questions=(TopicQuestion("¿Nivel?", "principiante"),),
    )
    return Topic(
        id="t1",
        owner_id="u1",
        name="IA para emprender",
        profile=TopicProfile(("ia",), (), (), reach_threshold=1, recency_hours=48),
        podcast_style=PodcastStyle.NARRATOR,
        state=TopicState.ACTIVE,
        cadence=Cadence(Frequency.DAILY, hour=8),
        onboarding=form,
    )


async def test_compose_injects_onboarding_instruction_and_remembers_angle() -> None:
    topics = InMemoryTopicStore()
    await topics.save(_topic_with_onboarding())
    store = InMemoryAngleStore()
    completer = FakeCompleter({"podcast_script": _SCRIPT})
    podcast = PodcastService(completer, FakeSynthesizer(), FakeAudioStorage())
    deps = make_deps(
        topics=topics,
        podcast=podcast,
        angles=AngleMemory(NullEmbeddingProvider(), store),
        clock=lambda: NOW,
        new_id=lambda: "ep-1",
    )
    capability = build_heraldo_module(deps).capability("compose_episode")

    await capability.invoke({"stories": [_STORY], "minutes": 5, "topic_id": "t1"})

    user_prompt = completer.prompts[0][1].content
    assert "IA para emprender" in user_prompt
    assert "APRENDER" in user_prompt
    assert await store.similar("t1", [], 5) == ["el rol del criterio"]


async def test_compose_without_topic_id_sends_no_instruction() -> None:
    completer = FakeCompleter({"podcast_script": _SCRIPT})
    podcast = PodcastService(completer, FakeSynthesizer(), FakeAudioStorage())
    deps = make_deps(podcast=podcast, new_id=lambda: "ep-1")
    capability = build_heraldo_module(deps).capability("compose_episode")

    await capability.invoke({"stories": [_STORY], "minutes": 5})

    assert "APRENDER" not in completer.prompts[0][1].content


async def test_due_topics_lists_only_topics_due_now() -> None:
    topics, deliveries = InMemoryTopicStore(), InMemoryDeliveryStore()
    await topics.save(_topic_with_onboarding())
    await deliveries.add(
        Delivery(id="d1", topic_id="t1", kind=DeliveryKind.PODCAST, created_at=NOW)
    )
    deps = make_deps(topics=topics, deliveries=deliveries, clock=lambda: NOW)
    capability = build_heraldo_module(deps).capability("due_topics")

    output = await capability.invoke({"owner_id": "u1"})

    assert output["topics"] == []


async def test_due_topics_returns_topic_never_delivered() -> None:
    topics = InMemoryTopicStore()
    await topics.save(_topic_with_onboarding())
    deps = make_deps(topics=topics, clock=lambda: NOW)
    capability = build_heraldo_module(deps).capability("due_topics")

    output = await capability.invoke({"owner_id": "u1"})

    assert output["topics"] == [
        {"topic_id": "t1", "name": "IA para emprender", "kind": "podcast", "needs_approval": True}
    ]
