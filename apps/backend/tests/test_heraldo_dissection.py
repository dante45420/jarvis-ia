"""Tests de la disección de temas: parseo de JSON del modelo y capacidades, sin red."""

from __future__ import annotations

from datetime import UTC, datetime

from jarvis.modules.heraldo.dissection import DissectionService, QuestionAnswer
from jarvis.modules.heraldo.in_memory_topics import InMemoryTopicStore
from jarvis.modules.heraldo.module import build_heraldo_module
from tests.heraldo_fakes import FakeCompleter, make_deps

NOW = datetime(2026, 7, 20, tzinfo=UTC)

_QUESTIONS_JSON = '{"questions": ["¿Qué enfoque te interesa?", "¿Qué nivel de detalle?"]}'
_PROFILE_JSON = (
    "Claro, aquí va:\n```json\n"
    '{"subtopics": ["diagnóstico por imágenes"], "include_keywords": ["FDA"], '
    '"exclude_keywords": ["rumor"], "reach_threshold": 2, "recency_hours": 24}\n```'
)


def _dissection(responses: dict[str, str]) -> DissectionService:
    return DissectionService(FakeCompleter(responses))


async def test_propose_questions_parses_model_json() -> None:
    service = _dissection({"dissect_questions": _QUESTIONS_JSON})
    questions = await service.propose_questions("IA en medicina", NOW)
    assert questions == ["¿Qué enfoque te interesa?", "¿Qué nivel de detalle?"]


async def test_compile_profile_parses_json_wrapped_in_prose() -> None:
    service = _dissection({"dissect_profile": _PROFILE_JSON})
    profile = await service.compile_profile("IA en medicina", [QuestionAnswer("q", "a")], NOW)
    assert profile.subtopics == ("diagnóstico por imágenes",)
    assert profile.exclude_keywords == ("rumor",)
    assert profile.reach_threshold == 2


async def test_compile_profile_falls_back_to_defaults_on_empty() -> None:
    service = _dissection({"dissect_profile": "{}"})
    profile = await service.compile_profile("tema", [], NOW)
    assert profile.subtopics == ()
    assert profile.reach_threshold == 1


async def test_propose_questions_capability_returns_questions() -> None:
    deps = make_deps(dissection=_dissection({"dissect_questions": _QUESTIONS_JSON}))
    output = await build_heraldo_module(deps).capability("propose_topic_questions").invoke(
        {"name": "IA en medicina"}
    )
    assert len(output["questions"]) == 2


async def test_compile_profile_capability_creates_active_topic() -> None:
    store = InMemoryTopicStore()
    deps = make_deps(
        topics=store,
        dissection=_dissection({"dissect_profile": _PROFILE_JSON}),
        new_id=lambda: "topic-1",
    )
    capability = build_heraldo_module(deps).capability("compile_topic_profile")

    output = await capability.invoke(
        {"owner_id": "u1", "name": "IA en medicina",
         "answers": [{"question": "q", "answer": "a"}]}
    )

    assert output["topic"]["id"] == "topic-1"
    assert output["topic"]["state"] == "active"
    saved = await store.get("topic-1")
    assert saved is not None
    assert saved.profile.reach_threshold == 2
