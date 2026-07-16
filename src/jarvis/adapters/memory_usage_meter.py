"""UsageMeter en memoria: acumula registros para tests y desarrollo.

La persistencia real (Supabase/Postgres) es otro adaptador del mismo puerto, y llega en Fase 1.
"""

from __future__ import annotations

from jarvis.domain.telemetry import UsageRecord


class InMemoryUsageMeter:
    """Implementa UsageMeter guardando los registros en una lista en memoria."""

    def __init__(self) -> None:
        self._records: list[UsageRecord] = []

    async def record(self, usage: UsageRecord) -> None:
        """Agrega un registro de uso a la colección."""
        self._records.append(usage)

    @property
    def records(self) -> list[UsageRecord]:
        """Devuelve una copia de los registros acumulados."""
        return list(self._records)
