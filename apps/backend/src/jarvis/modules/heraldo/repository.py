"""Puerto de persistencia de temas. El dominio no conoce SQLAlchemy ni Postgres."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from jarvis.modules.heraldo.delivery import Delivery
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


@runtime_checkable
class DeliveryStore(Protocol):
    """Guarda y recupera las entregas producidas por cada tema."""

    async def add(self, delivery: Delivery) -> None:
        """Registra una entrega recién producida."""
        ...

    async def latest_for_topic(self, topic_id: str) -> Delivery | None:
        """Devuelve la entrega más reciente del tema; base para saber si hay algo pendiente."""
        ...

    async def mark_consumed(self, delivery_id: str, at: datetime) -> Delivery | None:
        """Marca una entrega como consumida (abierta o reproducida) y la devuelve actualizada."""
        ...
