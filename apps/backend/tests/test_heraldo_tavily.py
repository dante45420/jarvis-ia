"""Test del adaptador Tavily: arma la consulta y mapea resultados a ítems. Sin red real."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import httpx

from jarvis.modules.heraldo.ports import SourceQuery
from jarvis.modules.heraldo.sources.tavily import TavilySource

NOW = datetime(2026, 7, 20, tzinfo=UTC)

_RESULTS = {
    "results": [
        {"title": "Consejo real", "url": "https://blog.dev/x", "content": "algo concreto y útil"},
        {"title": "Otro", "url": "https://news.io/y", "content": "más contenido"},
    ]
}


async def test_fetch_builds_query_and_maps_results() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json=_RESULTS)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        source = TavilySource("tvly-key", client, lambda: NOW)
        query = SourceQuery(subtopics=("ia",), include_keywords=("dev",), recency_hours=48)
        items = await source.fetch(query)

    assert [item.source_name for item in items] == ["blog.dev", "news.io"]
    assert items[0].snippet == "algo concreto y útil"
    assert items[0].published_at == NOW
    assert captured["auth"] == "Bearer tvly-key"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["query"] == "ia dev"
