"""Adaptador sobre la API directa de Gemini: implementa LLMProvider para el carril inmediato.

Se llama directo a Google (sin pasar por OpenRouter) para no pagar su margen cuando ya
manejamos la key de Gemini. Queda detrás del mismo puerto LLMProvider.
"""

from __future__ import annotations

from typing import Any

import httpx

from jarvis.domain.llm import LLMResult, Message

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider:
    """Implementa LLMProvider llamando a la API generateContent de Gemini."""

    def __init__(self, api_key: str, client: httpx.AsyncClient) -> None:
        self._api_key = api_key
        self._client = client

    async def complete(self, model: str, messages: list[Message]) -> LLMResult:
        """Ejecuta una completación y devuelve el texto con el conteo de tokens."""
        response = await self._client.post(
            f"{_BASE_URL}/{model}:generateContent",
            json=_payload(messages),
            headers={"x-goog-api-key": self._api_key},
        )
        response.raise_for_status()
        return _parse_completion(response.json())


def _payload(messages: list[Message]) -> dict[str, Any]:
    """Arma el cuerpo: los mensajes de sistema van a system_instruction; el resto a contents."""
    system = " ".join(message.content for message in messages if message.role == "system")
    contents = [_content(message) for message in messages if message.role != "system"]
    body: dict[str, Any] = {"contents": contents}
    if system:
        body["system_instruction"] = {"parts": [{"text": system}]}
    return body


def _content(message: Message) -> dict[str, Any]:
    """Traduce un mensaje a un turno de Gemini (rol 'user' o 'model')."""
    role = "model" if message.role == "assistant" else "user"
    return {"role": role, "parts": [{"text": message.content}]}


def _parse_completion(data: dict[str, Any]) -> LLMResult:
    """Extrae el texto y los tokens consumidos desde la respuesta de Gemini."""
    usage = data.get("usageMetadata", {})
    return LLMResult(
        text=_text(data),
        tokens_in=usage.get("promptTokenCount", 0),
        tokens_out=usage.get("candidatesTokenCount", 0),
    )


def _text(data: dict[str, Any]) -> str:
    """Une el texto de las partes de la primera candidata, o vacío si no hay."""
    candidates = data.get("candidates", [])
    if not candidates:
        return ""
    parts = candidates[0]["content"]["parts"]
    return "".join(part.get("text", "") for part in parts)
