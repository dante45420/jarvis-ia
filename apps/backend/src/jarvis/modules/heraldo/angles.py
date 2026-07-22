"""Memoria de ángulos: qué facetas de un tema ya trató el podcast, para no repetirlas.

Cada episodio deja un ángulo (una frase corta que nombra su enfoque). Antes de generar el
siguiente, recuperamos por similitud los ángulos ya tratados y se los pasamos al guionista para
que enseñe uno nuevo, como un experto que cada día muestra otra faceta del mismo tema.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from jarvis.domain.ports import EmbeddingProvider


@dataclass(frozen=True, slots=True)
class EpisodeAngle:
    """El ángulo que trató un episodio, con su vector para deduplicar por similitud."""

    topic_id: str
    summary: str
    embedding: list[float]
    created_at: datetime


@runtime_checkable
class AngleStore(Protocol):
    """Guarda y recupera los ángulos ya tratados por tema."""

    async def add(self, angle: EpisodeAngle) -> None:
        """Registra el ángulo de un episodio recién producido."""
        ...

    async def similar(self, topic_id: str, embedding: list[float], k: int) -> list[str]:
        """Devuelve hasta k resúmenes de ángulos del tema más parecidos al vector dado."""
        ...


class AngleMemory:
    """Recuerda los ángulos tratados y recupera los relevantes para no repetir ideas."""

    def __init__(self, embedder: EmbeddingProvider, store: AngleStore, k: int = 5) -> None:
        self._embedder = embedder
        self._store = store
        self._k = k

    async def covered(self, topic_id: str, query: str) -> tuple[str, ...]:
        """Recupera los ángulos ya tratados más cercanos a lo que se va a generar ahora."""
        if not query.strip():
            return ()
        vector = (await self._embedder.embed(query)).vector
        return tuple(await self._store.similar(topic_id, vector, self._k))

    async def remember(self, topic_id: str, summary: str, now: datetime) -> None:
        """Embebe y guarda el ángulo del episodio recién producido."""
        if not summary.strip():
            return
        vector = (await self._embedder.embed(summary)).vector
        await self._store.add(EpisodeAngle(topic_id, summary.strip(), vector, now))
