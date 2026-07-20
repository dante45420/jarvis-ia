"""Almacén de entregas en memoria: implementación liviana para tests y wiring temprano."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from jarvis.modules.heraldo.delivery import Delivery


class InMemoryDeliveryStore:
    """Guarda las entregas en un diccionario. Cumple DeliveryStore sin tocar la base de datos."""

    def __init__(self) -> None:
        self._deliveries: dict[str, Delivery] = {}

    async def add(self, delivery: Delivery) -> None:
        self._deliveries[delivery.id] = delivery

    async def latest_for_topic(self, topic_id: str) -> Delivery | None:
        candidates = [d for d in self._deliveries.values() if d.topic_id == topic_id]
        return max(candidates, key=lambda d: d.created_at, default=None)

    async def mark_consumed(self, delivery_id: str, at: datetime) -> Delivery | None:
        current = self._deliveries.get(delivery_id)
        if current is None:
            return None
        updated = replace(current, consumed_at=at)
        self._deliveries[delivery_id] = updated
        return updated
