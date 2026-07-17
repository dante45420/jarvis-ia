"""Test del adaptador OpenRouter: arma la petición y parsea texto + tokens, sin red real."""

import json

import httpx

from jarvis.adapters.openrouter import OpenRouterProvider
from jarvis.domain.llm import Message


def _fake_response(_: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": "hola"}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 5},
        },
    )


async def test_complete_returns_text_and_tokens() -> None:
    transport = httpx.MockTransport(_fake_response)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenRouterProvider(api_key="test", client=client)
        result = await provider.complete("openai/gpt-4o-mini", [Message("user", "hola")])
    assert result.text == "hola"
    assert result.tokens_in == 12
    assert result.tokens_out == 5


async def test_complete_sends_model_and_auth_header() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _fake_response(request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenRouterProvider(api_key="secret", client=client)
        await provider.complete("openai/gpt-4o-mini", [Message("user", "hola")])

    assert seen[0].headers["Authorization"] == "Bearer secret"
    body = json.loads(seen[0].content)
    assert body["model"] == "openai/gpt-4o-mini"
    assert body["messages"] == [{"role": "user", "content": "hola"}]
