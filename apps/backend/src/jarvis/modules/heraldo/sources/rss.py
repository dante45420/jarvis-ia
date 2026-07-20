"""Fuente RSS/Atom: descarga feeds y los normaliza a RawItem. La parte pesada es pura y sin IA.

El parseo (parse_feed) no toca la red: recibe el XML ya descargado, lo que lo hace testeable
sin salir a internet. La descarga vive detrás de FeedFetcher, inyectable.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

import feedparser

from jarvis.modules.heraldo.domain import RawItem
from jarvis.modules.heraldo.ports import SourceQuery

FeedFetcher = Callable[[str], Awaitable[str]]
Clock = Callable[[], datetime]

_TAGS = re.compile(r"<[^>]+>")


def parse_feed(content: str, fallback_source: str, now: datetime) -> list[RawItem]:
    """Convierte el XML de un feed en ítems; usa el título del feed como nombre de fuente."""
    parsed = feedparser.parse(content)
    source = _source_name(parsed, fallback_source)
    return [_to_item(entry, source, now) for entry in parsed.entries if entry.get("link")]


def _source_name(parsed: Any, fallback: str) -> str:
    """Nombre de la fuente: el título del feed, o el respaldo si no lo trae."""
    title = str(parsed.feed.get("title", "")).strip()
    return title or fallback


def _to_item(entry: Any, source: str, now: datetime) -> RawItem:
    """Traduce una entrada del feed a un RawItem con texto ya limpio."""
    return RawItem(
        url=str(entry.get("link", "")),
        title=str(entry.get("title", "")).strip(),
        snippet=_plain_text(str(entry.get("summary", ""))),
        source_name=source,
        published_at=_published_at(entry, now),
    )


def _published_at(entry: Any, now: datetime) -> datetime:
    """Fecha de publicación en UTC; si la entrada no la trae, se asume recién publicada."""
    struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if struct is None:
        return now
    return datetime(
        struct[0], struct[1], struct[2], struct[3], struct[4], struct[5], tzinfo=UTC
    )


def _plain_text(html: str) -> str:
    """Quita etiquetas HTML y colapsa espacios para dejar un snippet legible."""
    return " ".join(_TAGS.sub(" ", html).split())


class RssSource:
    """Fuente sobre un conjunto de feeds RSS/Atom. Un feed caído no tumba al resto."""

    name = "rss"

    def __init__(self, feeds: Sequence[str], fetcher: FeedFetcher, clock: Clock) -> None:
        self._feeds = tuple(feeds)
        self._fetcher = fetcher
        self._clock = clock

    async def fetch(self, query: SourceQuery) -> list[RawItem]:
        """Descarga todos los feeds en paralelo y devuelve sus ítems normalizados."""
        contents = await self._download_all()
        return self._parse_all(contents)

    async def _download_all(self) -> list[str | BaseException]:
        """Descarga los feeds en paralelo, capturando los que fallen sin abortar el lote."""
        return await asyncio.gather(
            *(self._fetcher(url) for url in self._feeds), return_exceptions=True
        )

    def _parse_all(self, contents: list[str | BaseException]) -> list[RawItem]:
        """Parsea el contenido descargado, saltándose los feeds que fallaron."""
        now = self._clock()
        items: list[RawItem] = []
        for url, content in zip(self._feeds, contents, strict=True):
            if isinstance(content, str):
                items.extend(parse_feed(content, _domain(url), now))
        return items


def _domain(url: str) -> str:
    """Dominio del feed, usado como respaldo del nombre de fuente."""
    return urlsplit(url).netloc or url
