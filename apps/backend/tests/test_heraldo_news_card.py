"""Tests del productor de tarjetas: IA perezosa, batch con troceo y caché por hash."""

from __future__ import annotations

from datetime import UTC, datetime

from jarvis.application.batching import BatchLimits
from jarvis.modules.heraldo.module import build_heraldo_module
from jarvis.modules.heraldo.news import StorySeed
from jarvis.modules.heraldo.news_cache import InMemoryNewsCardCache
from jarvis.modules.heraldo.news_card import NewsCardService
from tests.heraldo_fakes import FakeCompleter, make_deps

NOW = datetime(2026, 7, 20, tzinfo=UTC)


def _seed(story_id: str) -> StorySeed:
    return StorySeed(
        id=story_id,
        title=f"Titular {story_id}",
        snippet="contexto",
        url=f"https://x.cl/{story_id}",
        sources=("Medio A", "Medio B"),
    )


def _cards_json(*story_ids: str) -> str:
    cards = ", ".join(
        f'{{"story_id": "{sid}", "hook": "h{sid}", "one_line": "l", '
        '"key_points": ["a", "b"], "detail": "d", "why_it_matters": "w"}'
        for sid in story_ids
    )
    return f'{{"cards": [{cards}]}}'


async def test_deepen_builds_card_with_deterministic_sources() -> None:
    completer = FakeCompleter({"news_card": _cards_json("s1")})
    service = NewsCardService(completer, InMemoryNewsCardCache())
    cards = await service.deepen([_seed("s1")], NOW)
    assert cards[0].hook == "hs1"
    assert cards[0].sources == ("Medio A", "Medio B")


async def test_deepen_uses_cache_and_does_not_resummarize() -> None:
    completer = FakeCompleter({"news_card": _cards_json("s1")})
    service = NewsCardService(completer, InMemoryNewsCardCache())
    await service.deepen([_seed("s1")], NOW)
    await service.deepen([_seed("s1")], NOW)
    assert completer.calls == ["news_card"]


async def test_deepen_chunks_into_multiple_calls_by_limit() -> None:
    responses = {"news_card": _cards_json("s1", "s2", "s3")}
    completer = FakeCompleter(responses)
    limits = BatchLimits(max_items=1, max_input_tokens=9999, max_output_tokens=9999)
    service = NewsCardService(completer, InMemoryNewsCardCache(), limits)
    await service.deepen([_seed("s1"), _seed("s2"), _seed("s3")], NOW)
    assert len(completer.calls) == 3


async def test_deepen_stories_capability_returns_layered_cards() -> None:
    completer = FakeCompleter({"news_card": _cards_json("s1")})
    service = NewsCardService(completer, InMemoryNewsCardCache())
    capability = build_heraldo_module(make_deps(news_cards=service)).capability("deepen_stories")

    output = await capability.invoke(
        {"stories": [{"id": "s1", "title": "T", "snippet": "c", "url": "https://x.cl/s1",
                      "sources": ["Medio A"]}]}
    )

    card = output["cards"][0]
    assert card["story_id"] == "s1"
    assert card["key_points"] == ["a", "b"]
    assert card["sources"] == ["Medio A"]
