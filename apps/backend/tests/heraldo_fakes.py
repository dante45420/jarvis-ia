"""Ayudas de prueba para Heraldo: una fuente falsa y un constructor de ítems."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jarvis.modules.heraldo.domain import RawItem
from jarvis.modules.heraldo.ports import SourceQuery

_DEFAULT_NOW = datetime(2026, 7, 20, tzinfo=UTC)


class FakeSource:
    """Fuente de prueba que devuelve ítems predefinidos, ignorando la consulta."""

    def __init__(self, name: str, items: list[RawItem]) -> None:
        self._name = name
        self._items = items

    @property
    def name(self) -> str:
        return self._name

    async def fetch(self, query: SourceQuery) -> list[RawItem]:
        return list(self._items)


def make_item(
    title: str,
    source: str,
    *,
    url: str | None = None,
    hours_ago: int = 1,
    snippet: str = "",
    now: datetime = _DEFAULT_NOW,
) -> RawItem:
    """Construye un RawItem con valores por defecto razonables para los tests."""
    slug = title.replace(" ", "-")
    return RawItem(
        url=url or f"https://{source}.example/{slug}",
        title=title,
        snippet=snippet,
        source_name=source,
        published_at=now - timedelta(hours=hours_ago),
    )
