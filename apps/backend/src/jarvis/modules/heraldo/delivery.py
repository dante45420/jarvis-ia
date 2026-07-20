"""Entregas de Heraldo: cada podcast o noticiero producido para un tema."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class DeliveryKind(StrEnum):
    """Tipo de entrega que produce un tema."""

    PODCAST = "podcast"
    NEWS = "news"


@dataclass(frozen=True, slots=True)
class Delivery:
    """Una entrega concreta; se considera consumida al abrirla o reproducirla."""

    id: str
    topic_id: str
    kind: DeliveryKind
    created_at: datetime
    consumed_at: datetime | None = None

    @property
    def is_consumed(self) -> bool:
        """Indica si el usuario ya abrió o reprodujo la entrega."""
        return self.consumed_at is not None
