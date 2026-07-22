"""Cadencia de un tema: cada cuánto y a qué hora se entrega. Determinística, cero IA.

La decisión de "toca generar ahora" es pura: depende solo de la cadencia, la última entrega y
la hora actual. El scheduler la usa para no gastar IA fuera del ritmo que tú elegiste por tema.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Frequency(StrEnum):
    """Ritmo de entrega de un tema; se traduce a un período en días."""

    DAILY = "daily"
    EVERY_N_DAYS = "every_n_days"
    WEEKLY = "weekly"


@dataclass(frozen=True, slots=True)
class Cadence:
    """Cada cuánto (frecuencia) y a qué hora local se entrega el contenido de un tema."""

    frequency: Frequency = Frequency.DAILY
    every_days: int = 1
    hour: int = 8

    @property
    def period_days(self) -> int:
        """Días entre entregas según la frecuencia; nunca menos de uno."""
        if self.frequency is Frequency.WEEKLY:
            return 7
        if self.frequency is Frequency.EVERY_N_DAYS:
            return max(1, self.every_days)
        return 1


def is_due(cadence: Cadence, last_delivery_at: datetime | None, now: datetime) -> bool:
    """Indica si toca generar: es la hora elegida y pasó el período desde la última entrega."""
    if now.hour != cadence.hour:
        return False
    if last_delivery_at is None:
        return True
    return _days_elapsed(last_delivery_at, now) >= cadence.period_days


def _days_elapsed(last_delivery_at: datetime, now: datetime) -> int:
    """Días calendario transcurridos desde la última entrega hasta ahora."""
    return (now.date() - last_delivery_at.date()).days
