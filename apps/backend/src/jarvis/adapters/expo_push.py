"""Adaptador de PushSender sobre la Expo Push API. Envía los avisos al celular del usuario."""

from __future__ import annotations

import httpx

from jarvis.domain.notifications import PushMessage

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
_MAX_PER_REQUEST = 100


class ExpoPushSender:
    """Implementa PushSender llamando a la Expo Push API, en lotes de hasta 100 mensajes."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def send(self, tokens: list[str], message: PushMessage) -> None:
        """Envía el mensaje a todos los tokens, troceando en lotes que la API acepta."""
        for batch in _chunks(tokens, _MAX_PER_REQUEST):
            await self._post([_to_payload(token, message) for token in batch])

    async def _post(self, messages: list[dict[str, object]]) -> None:
        """Ejecuta una petición de push con el lote de mensajes."""
        response = await self._client.post(EXPO_PUSH_URL, json=messages)
        response.raise_for_status()


def _to_payload(token: str, message: PushMessage) -> dict[str, object]:
    """Arma el mensaje de Expo para un token."""
    return {"to": token, "title": message.title, "body": message.body, "data": message.data}


def _chunks(items: list[str], size: int) -> list[list[str]]:
    """Trocea la lista en sublistas de a lo más `size`."""
    return [items[start : start + size] for start in range(0, len(items), size)]
