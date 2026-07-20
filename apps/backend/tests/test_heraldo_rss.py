"""Tests del adaptador RSS: parseo puro, resiliencia y encaje con el motor (alcance)."""

from __future__ import annotations

from datetime import UTC, datetime

from jarvis.modules.heraldo.domain import TopicProfile
from jarvis.modules.heraldo.gather import GatherService
from jarvis.modules.heraldo.ports import SourceQuery
from jarvis.modules.heraldo.sources.rss import RssSource, parse_feed

NOW = datetime(2026, 7, 20, 12, tzinfo=UTC)

_ITEM_RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel>
<title>Diario Tech</title>
<item>
  <title>Nueva ley de IA aprobada</title>
  <link>https://diariotech.cl/ley-ia?utm_source=rss</link>
  <description>El congreso &lt;b&gt;aprobó&lt;/b&gt; la ley hoy.</description>
  <pubDate>Mon, 20 Jul 2026 09:00:00 +0000</pubDate>
</item>
</channel></rss>"""


def _feed(channel: str, host: str, title: str = "Ley de IA aprobada") -> str:
    return (
        '<?xml version="1.0"?><rss version="2.0"><channel>'
        f"<title>{channel}</title>"
        f"<item><title>{title}</title><link>https://{host}/ley</link>"
        "<pubDate>Mon, 20 Jul 2026 09:00:00 +0000</pubDate></item>"
        "</channel></rss>"
    )


class _FakeFetcher:
    """Descargador falso: sirve páginas conocidas y falla en las demás (feed caído)."""

    def __init__(self, pages: dict[str, str]) -> None:
        self._pages = pages

    async def __call__(self, url: str) -> str:
        if url not in self._pages:
            raise RuntimeError("feed caído")
        return self._pages[url]


def test_parse_feed_extracts_item_with_source_and_clean_snippet() -> None:
    items = parse_feed(_ITEM_RSS, "diariotech.cl", NOW)
    assert len(items) == 1
    item = items[0]
    assert item.title == "Nueva ley de IA aprobada"
    assert item.source_name == "Diario Tech"
    assert item.snippet == "El congreso aprobó la ley hoy."
    assert item.published_at == datetime(2026, 7, 20, 9, tzinfo=UTC)


def test_parse_feed_falls_back_and_assumes_now_without_date() -> None:
    feed = (
        '<?xml version="1.0"?><rss version="2.0"><channel>'
        "<item><title>x</title><link>https://a.cl/x</link></item></channel></rss>"
    )
    items = parse_feed(feed, "a.cl", NOW)
    assert items[0].source_name == "a.cl"
    assert items[0].published_at == NOW


async def test_rss_source_survives_a_dead_feed() -> None:
    pages = {"https://diariotech.cl/rss": _ITEM_RSS}
    source = RssSource(
        feeds=["https://diariotech.cl/rss", "https://caido.cl/rss"],
        fetcher=_FakeFetcher(pages),
        clock=lambda: NOW,
    )
    items = await source.fetch(SourceQuery(subtopics=(), include_keywords=(), recency_hours=48))
    assert len(items) == 1
    assert items[0].source_name == "Diario Tech"


async def test_two_feeds_same_story_reach_two_via_gather() -> None:
    pages = {"https://a.cl/rss": _feed("Medio A", "a.cl"),
             "https://b.cl/rss": _feed("Medio B", "b.cl")}
    source = RssSource(list(pages), _FakeFetcher(pages), lambda: NOW)
    profile = TopicProfile((), (), (), reach_threshold=2, recency_hours=48)
    clusters = await GatherService([source]).gather(profile, NOW)
    assert len(clusters) == 1
    assert clusters[0].reach == 2
