"""Test del adaptador Gemini directo: mapea roles y parsea tokens, sin red real."""

from __future__ import annotations

import json

import httpx

from jarvis.adapters.gemini import GeminiProvider
from jarvis.domain.llm import Message

_RESPONSE = {
    "candidates": [{"content": {"parts": [{"text": "hola"}]}}],
    "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5},
}


async def test_complete_maps_system_and_parses_usage() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        captured["key"] = request.headers.get("x-goog-api-key")
        return httpx.Response(200, json=_RESPONSE)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = GeminiProvider("secret", client)
        result = await provider.complete(
            "gemini-2.5-flash", [Message("system", "sé breve"), Message("user", "hola")]
        )

    assert result.text == "hola"
    assert result.tokens_in == 10
    assert result.tokens_out == 5
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["system_instruction"]["parts"][0]["text"] == "sé breve"
    assert body["contents"][0]["role"] == "user"
    assert captured["key"] == "secret"
