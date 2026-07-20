"""Adaptador de DeliveryStore sobre Postgres con SQLAlchemy async."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jarvis.modules.heraldo.db_models import DeliveryRow
from jarvis.modules.heraldo.delivery import Delivery, DeliveryKind


class PgDeliveryStore:
    """Implementa DeliveryStore con SQLAlchemy async."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add(self, delivery: Delivery) -> None:
        """Inserta una entrega nueva."""
        async with self._session_factory() as session:
            session.add(_to_row(delivery))
            await session.commit()

    async def latest_for_topic(self, topic_id: str) -> Delivery | None:
        """Recupera la entrega más reciente del tema."""
        stmt = (
            select(DeliveryRow)
            .where(DeliveryRow.topic_id == topic_id)
            .order_by(DeliveryRow.created_at.desc())
            .limit(1)
        )
        async with self._session_factory() as session:
            row = (await session.scalars(stmt)).one_or_none()
        return _to_delivery(row) if row is not None else None

    async def mark_consumed(self, delivery_id: str, at: datetime) -> Delivery | None:
        """Marca una entrega como consumida y la devuelve, o None si no existe."""
        async with self._session_factory() as session:
            row = await session.get(DeliveryRow, delivery_id)
            if row is None:
                return None
            row.consumed_at = at
            await session.commit()
            return _to_delivery(row)


def _to_row(delivery: Delivery) -> DeliveryRow:
    """Traduce una entrega de dominio a fila."""
    return DeliveryRow(
        id=delivery.id,
        topic_id=delivery.topic_id,
        kind=delivery.kind.value,
        created_at=delivery.created_at,
        consumed_at=delivery.consumed_at,
    )


def _to_delivery(row: DeliveryRow) -> Delivery:
    """Traduce una fila a entrega de dominio."""
    return Delivery(
        id=row.id,
        topic_id=row.topic_id,
        kind=DeliveryKind(row.kind),
        created_at=row.created_at,
        consumed_at=row.consumed_at,
    )
