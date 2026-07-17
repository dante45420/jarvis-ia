"""Test del adaptador de embeddings de OpenRouter: parsea vector + tokens y arma la petición."""

import json

import httpx

from jarvis.adapters.openrouter import OpenRouterEmbeddingProvider


def _fake_response(_: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={"data": [{"embedding": [0.1, 0.2, 0.3]}], "usage": {"prompt_tokens": 7}},
    )


async def test_embed_returns_vector_and_tokens() -> None:
    transport = httpx.MockTransport(_fake_response)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenRouterEmbeddingProvider(api_key="k", model="baai/bge-m3", client=client)
        result = await provider.embed("hola")
    assert result.vector == [0.1, 0.2, 0.3]
    assert result.tokens == 7


async def test_embed_sends_model_and_input() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _fake_response(request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenRouterEmbeddingProvider(api_key="k", model="baai/bge-m3", client=client)
        await provider.embed("hola")

    body = json.loads(seen[0].content)
    assert body["model"] == "baai/bge-m3"
    assert body["input"] == "hola"
