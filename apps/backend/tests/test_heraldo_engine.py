"""Tests del motor determinístico de Heraldo: normalización, clustering, filtro y ranking."""

from __future__ import annotations

from datetime import UTC, datetime

from jarvis.modules.heraldo.clustering import cluster_items
from jarvis.modules.heraldo.domain import TopicProfile
from jarvis.modules.heraldo.gather import GatherService
from jarvis.modules.heraldo.normalize import canonical_url
from jarvis.modules.heraldo.ranking import filter_clusters, rank_clusters
from tests.heraldo_fakes import FakeSource, make_item

NOW = datetime(2026, 7, 20, tzinfo=UTC)


def _profile(*, reach: int = 1, recency: int = 48, exclude: tuple[str, ...] = ()) -> TopicProfile:
    return TopicProfile(
        subtopics=(),
        include_keywords=(),
        exclude_keywords=exclude,
        reach_threshold=reach,
        recency_hours=recency,
    )


def test_canonical_url_strips_tracking_and_trailing_slash() -> None:
    assert canonical_url("https://Example.com/Nota/?utm_source=x&id=5") == "https://example.com/Nota?id=5"


def test_same_story_from_two_sources_clusters_with_reach_two() -> None:
    items = [make_item("Nueva ley de IA aprobada hoy", "medioA"),
             make_item("Nueva ley de IA aprobada hoy", "medioB")]
    clusters = cluster_items(items, 0.6)
    assert len(clusters) == 1
    assert clusters[0].reach == 2


def test_distinct_stories_stay_separate() -> None:
    items = [make_item("Nueva ley de IA aprobada", "a"),
             make_item("Resultados del partido de futbol", "b")]
    assert len(cluster_items(items, 0.6)) == 2


def test_same_url_with_tracking_clusters_despite_titles() -> None:
    items = [make_item("Titular original", "a", url="https://diario.cl/x?utm_source=mail"),
             make_item("Titular reescrito distinto", "b", url="https://diario.cl/x")]
    assert len(cluster_items(items, 0.6)) == 1


def test_filter_drops_stories_below_reach_threshold() -> None:
    clusters = cluster_items([make_item("solo una fuente lo cubre", "a")], 0.6)
    assert filter_clusters(clusters, _profile(reach=2), NOW) == []


def test_filter_drops_excluded_keyword() -> None:
    clusters = cluster_items([make_item("posible ascenso", "a", snippet="es solo un rumor")], 0.6)
    assert filter_clusters(clusters, _profile(exclude=("rumor",)), NOW) == []


def test_filter_drops_stories_outside_recency_window() -> None:
    clusters = cluster_items([make_item("historia vieja", "a", hours_ago=100)], 0.6)
    assert filter_clusters(clusters, _profile(recency=48), NOW) == []


def test_rank_prioritizes_reach_over_recency() -> None:
    big = [make_item("historia grande", "a"), make_item("historia grande", "b")]
    high = cluster_items(big, 0.6)[0]
    low = cluster_items([make_item("historia chica", "c", hours_ago=0)], 0.6)[0]
    ranked = rank_clusters([low, high], NOW)
    assert ranked[0] is high


async def test_gather_merges_sources_dedups_and_ranks() -> None:
    sources = [FakeSource("medioA", [make_item("Ley de IA aprobada", "medioA")]),
               FakeSource("medioB", [make_item("Ley de IA aprobada", "medioB")])]
    clusters = await GatherService(sources).gather(_profile(reach=2), NOW)
    assert len(clusters) == 1
    assert clusters[0].reach == 2
