"""Fuente Tavily: búsqueda web real del tema, agregando varias fuentes en una sola llamada.

Sirve tanto al noticiero como al modo en vivo: convierte los subtemas y keywords del perfil en una
consulta y devuelve resultados reales con su contenido, para fundamentar el contenido (no inventar).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit

import httpx

from jarvis.modules.heraldo.domain import RawItem
from jarvis.modules.heraldo.ports import SourceQuery

_SEARCH_URL = "https://api.tavily.com/search"
_SNIPPET_LIMIT = 600
Clock = Callable[[], datetime]


class TavilySource:
    """Fuente sobre la API de búsqueda de Tavily."""

    name = "tavily"

    def __init__(
        self, api_key: str, client: httpx.AsyncClient, clock: Clock, max_results: int = 8
    ) -> None:
        self._api_key = api_key
        self._client = client
        self._clock = clock
        self._max_results = max_results

    async def fetch(self, query: SourceQuery) -> list[RawItem]:
        """Busca en la web la consulta del tema y devuelve los resultados como ítems."""
        response = await self._client.post(
            _SEARCH_URL,
            json=_payload(query, self._max_results),
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        response.raise_for_status()
        now = self._clock()
        return [_to_item(result, now) for result in response.json().get("results", [])]


def _payload(query: SourceQuery, max_results: int) -> dict[str, Any]:
    """Arma la consulta de Tavily a partir de los subtemas y keywords del perfil."""
    terms = " ".join((*query.subtopics, *query.include_keywords)).strip()
    return {"query": terms, "max_results": max_results, "search_depth": "basic"}


def _to_item(result: dict[str, Any], now: datetime) -> RawItem:
    """Traduce un resultado de Tavily a un RawItem, usando el dominio como fuente."""
    url = str(result.get("url", ""))
    return RawItem(
        url=url,
        title=str(result.get("title", "")).strip(),
        snippet=str(result.get("content", "")).strip()[:_SNIPPET_LIMIT],
        source_name=_domain(url),
        published_at=now,
    )


def _domain(url: str) -> str:
    """Dominio del resultado, usado como nombre de fuente para medir alcance."""
    return urlsplit(url).netloc or "tavily"
