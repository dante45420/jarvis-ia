"""Test end-to-end de la capacidad gather_stories del módulo Heraldo."""

from __future__ import annotations

from datetime import UTC, datetime

from jarvis.modules.heraldo.gather import GatherService
from jarvis.modules.heraldo.in_memory_topics import InMemoryTopicStore
from jarvis.modules.heraldo.module import build_heraldo_module
from tests.heraldo_fakes import FakeSource, make_item

NOW = datetime(2026, 7, 20, tzinfo=UTC)


async def test_gather_stories_returns_ranked_json_with_reach_and_sources() -> None:
    gather = GatherService([FakeSource("A", [make_item("Ley de IA aprobada", "A")]),
                            FakeSource("B", [make_item("Ley de IA aprobada", "B")])])
    module = build_heraldo_module(
        gather, InMemoryTopicStore(), clock=lambda: NOW, new_id=lambda: "id-1"
    )
    capability = module.capability("gather_stories")

    output = await capability.invoke({"subtopics": ["ia"], "reach_threshold": 2})

    assert len(output["stories"]) == 1
    story = output["stories"][0]
    assert story["reach"] == 2
    assert story["sources"] == ["A", "B"]
