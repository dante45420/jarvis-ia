"""Puerto de persistencia de temas. El dominio no conoce SQLAlchemy ni Postgres."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from jarvis.modules.heraldo.domain import Topic


@runtime_checkable
class TopicStore(Protocol):
    """Guarda y recupera los temas que el usuario sigue."""

    async def save(self, topic: Topic) -> None:
        """Inserta o actualiza un tema por su id."""
        ...

    async def get(self, topic_id: str) -> Topic | None:
        """Devuelve un tema por id, o None si no existe."""
        ...

    async def list_by_owner(self, owner_id: str) -> list[Topic]:
        """Devuelve todos los temas del usuario."""
        ...

    async def list_active(self, owner_id: str) -> list[Topic]:
        """Devuelve los temas activos del usuario; el scheduler solo genera para estos."""
        ...
