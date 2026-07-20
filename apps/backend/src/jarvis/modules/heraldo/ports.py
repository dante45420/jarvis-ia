"""Puertos de Heraldo: contratos que los adaptadores de fuentes implementan.

Cada fuente (RSS, Tavily, X, newsletters) vive detrás de este puerto. Sumar una fuente es
escribir un adaptador, sin tocar el motor determinístico que reúne y ordena.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from jarvis.modules.heraldo.domain import RawItem


@dataclass(frozen=True, slots=True)
class SourceQuery:
    """Lo que el motor le pide a una fuente: subtemas, keywords y ventana de tiempo."""

    subtopics: tuple[str, ...]
    include_keywords: tuple[str, ...]
    recency_hours: int


@runtime_checkable
class SourceAdapter(Protocol):
    """Una fuente de contenido que devuelve ítems crudos para una consulta."""

    @property
    def name(self) -> str:
        """Nombre de la fuente; se usa para medir su alcance y su costo por separado."""
        ...

    async def fetch(self, query: SourceQuery) -> list[RawItem]:
        """Trae los ítems de la fuente que calzan con la consulta."""
        ...
