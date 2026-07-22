"""PushTokenStore en memoria: para arrancar sin base y para los tests."""

from __future__ import annotations

from jarvis.domain.notifications import PushToken


class InMemoryPushTokenStore:
    """Guarda los tokens en un dict por token; deduplica dispositivos por su token."""

    def __init__(self) -> None:
        self._tokens: dict[str, PushToken] = {}

    async def save(self, token: PushToken) -> None:
        """Registra o actualiza el token del dispositivo."""
        self._tokens[token.token] = token

    async def list_for_owner(self, owner_id: str) -> list[PushToken]:
        """Devuelve los tokens del usuario."""
        return [token for token in self._tokens.values() if token.owner_id == owner_id]
