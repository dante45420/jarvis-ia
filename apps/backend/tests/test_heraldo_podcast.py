"""Tests del productor de podcast: guion en lote, voz y audio alojado."""

from __future__ import annotations

from datetime import UTC, datetime

from jarvis.modules.heraldo.domain import PodcastStyle
from jarvis.modules.heraldo.module import build_heraldo_module
from jarvis.modules.heraldo.news import StorySeed
from jarvis.modules.heraldo.podcast_service import PodcastService
from tests.heraldo_fakes import FakeAudioStorage, FakeCompleter, FakeSynthesizer, make_deps

NOW = datetime(2026, 7, 20, tzinfo=UTC)
_SCRIPT_JSON = '{"title": "Lo último en IA", "script": "Hola, hoy hablamos de la nueva ley."}'


def _seed(story_id: str) -> StorySeed:
    return StorySeed(
        id=story_id,
        title=f"Titular {story_id}",
        snippet="contexto",
        url=f"https://x.cl/{story_id}",
        sources=("Medio B", "Medio A"),
    )


async def test_compose_writes_script_synthesizes_and_stores_audio() -> None:
    storage = FakeAudioStorage()
    completer = FakeCompleter({"podcast_script": _SCRIPT_JSON})
    service = PodcastService(completer, FakeSynthesizer(), storage)

    episode = await service.compose([_seed("s1")], PodcastStyle.NARRATOR, 10, NOW, "ep-1")

    assert episode.title == "Lo último en IA"
    assert episode.audio_url == "memory://episodes/ep-1.mp3"
    assert episode.sources == ("Medio A", "Medio B")
    assert storage.saved["episodes/ep-1.mp3"] == episode.script.encode()


async def test_compose_uses_single_script_call_for_all_stories() -> None:
    completer = FakeCompleter({"podcast_script": _SCRIPT_JSON})
    service = PodcastService(completer, FakeSynthesizer(), FakeAudioStorage())
    await service.compose([_seed("s1"), _seed("s2")], PodcastStyle.DIALOGUE, 5, NOW, "ep-1")
    assert completer.calls == ["podcast_script"]


async def test_compose_episode_capability_returns_episode() -> None:
    service = PodcastService(
        FakeCompleter({"podcast_script": _SCRIPT_JSON}), FakeSynthesizer(), FakeAudioStorage()
    )
    deps = make_deps(podcast=service, new_id=lambda: "ep-1")
    capability = build_heraldo_module(deps).capability("compose_episode")

    output = await capability.invoke(
        {"stories": [{"id": "s1", "title": "T", "snippet": "c", "url": "https://x.cl/s1",
                      "sources": ["Medio A"]}],
         "style": "dialogue", "minutes": 8}
    )

    assert output["episode"]["id"] == "ep-1"
    assert output["episode"]["duration_minutes"] == 8
    assert output["episode"]["title"] == "Lo último en IA"
