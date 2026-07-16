"""Adaptador de LLMProvider sobre OpenRouter. Traduce el puerto a la API HTTP del proveedor."""

from __future__ import annotations

from typing import Any

import httpx

from jarvis.domain.llm import LLMResult, Message

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProvider:
    """Implementa LLMProvider llamando a la API de OpenRouter."""

    def __init__(self, api_key: str, client: httpx.AsyncClient) -> None:
        self._api_key = api_key
        self._client = client

    async def complete(self, model: str, messages: list[Message]) -> LLMResult:
        """Ejecuta una completación de chat y devuelve el texto con el conteo de tokens."""
        payload = _build_payload(model, messages)
        response = await self._client.post(OPENROUTER_URL, json=payload, headers=self._headers())
        response.raise_for_status()
        return _parse_result(response.json())

    def _headers(self) -> dict[str, str]:
        """Arma las cabeceras de autenticación."""
        return {"Authorization": f"Bearer {self._api_key}"}


def _build_payload(model: str, messages: list[Message]) -> dict[str, Any]:
    """Arma el cuerpo de la petición a partir del modelo y los mensajes."""
    return {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
    }


def _parse_result(data: dict[str, Any]) -> LLMResult:
    """Extrae el texto y los tokens consumidos desde la respuesta de OpenRouter."""
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return LLMResult(
        text=text,
        tokens_in=usage.get("prompt_tokens", 0),
        tokens_out=usage.get("completion_tokens", 0),
    )
