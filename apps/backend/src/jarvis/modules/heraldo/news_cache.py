"""Caché de tarjetas: garantiza que una historia nunca se resuma dos veces (ahorro de IA)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from jarvis.modules.heraldo.news import NewsCard


@runtime_checkable
class NewsCardCache(Protocol):
    """Guarda las tarjetas ya generadas, indexadas por el id de la historia."""

    async def get_many(self, story_ids: list[str]) -> dict[str, NewsCard]:
        """Devuelve las tarjetas cacheadas para los ids pedidos que existan."""
        ...

    async def put_many(self, cards: list[NewsCard]) -> None:
        """Guarda en lote las tarjetas recién generadas."""
        ...


class InMemoryNewsCardCache:
    """Caché en memoria; implementación liviana para tests y wiring temprano."""

    def __init__(self) -> None:
        self._cards: dict[str, NewsCard] = {}

    async def get_many(self, story_ids: list[str]) -> dict[str, NewsCard]:
        return {sid: self._cards[sid] for sid in story_ids if sid in self._cards}

    async def put_many(self, cards: list[NewsCard]) -> None:
        for card in cards:
            self._cards[card.story_id] = card
