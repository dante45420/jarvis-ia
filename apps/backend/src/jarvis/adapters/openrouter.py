"""Adaptador sobre OpenRouter: implementa LLMProvider y EmbeddingProvider con un mismo key."""

from __future__ import annotations

from typing import Any

import httpx

from jarvis.domain.embedding import BatchEmbeddingResult, EmbeddingResult
from jarvis.domain.llm import LLMResult, Message

CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"


class OpenRouterProvider:
    """Implementa LLMProvider llamando a la API de chat de OpenRouter."""

    def __init__(self, api_key: str, client: httpx.AsyncClient) -> None:
        self._api_key = api_key
        self._client = client

    async def complete(self, model: str, messages: list[Message]) -> LLMResult:
        """Ejecuta una completación de chat y devuelve el texto con el conteo de tokens."""
        payload = _chat_payload(model, messages)
        response = await self._client.post(
            CHAT_URL, json=payload, headers=_auth_headers(self._api_key)
        )
        response.raise_for_status()
        return _parse_completion(response.json())


class OpenRouterEmbeddingProvider:
    """Implementa EmbeddingProvider llamando a la API de embeddings de OpenRouter."""

    def __init__(self, api_key: str, model: str, client: httpx.AsyncClient) -> None:
        self._api_key = api_key
        self._model = model
        self._client = client

    async def embed(self, text: str) -> EmbeddingResult:
        """Devuelve el vector de embedding del texto junto a los tokens consumidos."""
        data = await self._post_embeddings(text)
        return _parse_embedding(data)

    async def embed_batch(self, texts: list[str]) -> BatchEmbeddingResult:
        """Embebe varios textos en una sola llamada (batching, ver D-0011)."""
        data = await self._post_embeddings(texts)
        return _parse_batch_embedding(data)

    async def _post_embeddings(self, input_: str | list[str]) -> dict[str, Any]:
        """Ejecuta la petición de embeddings y devuelve el JSON de respuesta."""
        payload = {"model": self._model, "input": input_}
        response = await self._client.post(
            EMBEDDINGS_URL, json=payload, headers=_auth_headers(self._api_key)
        )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result


def _auth_headers(api_key: str) -> dict[str, str]:
    """Arma las cabeceras de autenticación para OpenRouter."""
    return {"Authorization": f"Bearer {api_key}"}


def _chat_payload(model: str, messages: list[Message]) -> dict[str, Any]:
    """Arma el cuerpo de la petición de chat a partir del modelo y los mensajes."""
    return {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
    }


def _parse_completion(data: dict[str, Any]) -> LLMResult:
    """Extrae el texto y los tokens consumidos desde la respuesta de chat."""
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return LLMResult(
        text=text,
        tokens_in=usage.get("prompt_tokens", 0),
        tokens_out=usage.get("completion_tokens", 0),
    )


def _parse_embedding(data: dict[str, Any]) -> EmbeddingResult:
    """Extrae el vector y los tokens consumidos desde la respuesta de embeddings."""
    vector = data["data"][0]["embedding"]
    usage = data.get("usage", {})
    return EmbeddingResult(vector=vector, tokens=usage.get("prompt_tokens", 0))


def _parse_batch_embedding(data: dict[str, Any]) -> BatchEmbeddingResult:
    """Extrae los vectores en orden y los tokens totales desde la respuesta de embeddings."""
    vectors = [item["embedding"] for item in data["data"]]
    usage = data.get("usage", {})
    return BatchEmbeddingResult(vectors=vectors, tokens=usage.get("prompt_tokens", 0))
