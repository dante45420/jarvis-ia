"""Puertos del dominio: contratos que la infraestructura implementa como adaptadores.

El dominio depende de estas interfaces, nunca de proveedores concretos. Sumar o cambiar un
proveedor significa escribir un adaptador que cumpla el puerto, sin tocar dominio ni casos de uso.

Los puertos que dependen de entidades aún no modeladas (VectorStore, MemoryStore,
ChannelAdapter) se definen en la Fase 1, junto a sus entidades. Ver docs/ROADMAP.md.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from jarvis.domain.embedding import BatchEmbeddingResult, EmbeddingResult
from jarvis.domain.llm import LLMResult, Message
from jarvis.domain.memory import (
    ConversationTurn,
    EmbeddedFact,
    RetrievedFact,
)
from jarvis.domain.telemetry import UsageRecord


@runtime_checkable
class UsageMeter(Protocol):
    """Registra el gasto de IA. Es el insumo del dashboard de costo."""

    async def record(self, usage: UsageRecord) -> None:
        """Persiste un registro de uso."""
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """Ejecuta una completación de chat con un modelo dado (vía OpenRouter)."""

    async def complete(self, model: str, messages: list[Message]) -> LLMResult:
        """Devuelve la respuesta del modelo junto al conteo de tokens."""
        ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Convierte texto en vectores para búsqueda por similitud (RAG)."""

    async def embed(self, text: str) -> EmbeddingResult:
        """Devuelve el vector de embedding del texto junto a los tokens consumidos."""
        ...

    async def embed_batch(self, texts: list[str]) -> BatchEmbeddingResult:
        """Embebe varios textos en una sola llamada (batching obligatorio, ver D-0011)."""
        ...


@runtime_checkable
class ModelRouter(Protocol):
    """Elige el modelo más barato capaz de resolver una tarea."""

    def select(self, task: str) -> str:
        """Devuelve el identificador del modelo a usar para la tarea."""
        ...


@runtime_checkable
class SemanticCache(Protocol):
    """Reutiliza respuestas cuando la intención entrante es equivalente a una previa."""

    async def get(self, prompt: str) -> str | None:
        """Devuelve una respuesta cacheada equivalente, o None si no hay."""
        ...

    async def put(self, prompt: str, response: str) -> None:
        """Guarda una respuesta para reutilizarla ante intenciones equivalentes."""
        ...


@runtime_checkable
class MemoryStore(Protocol):
    """Persiste el log de turnos y los hechos durables; recupera hechos por similitud (RAG)."""

    async def append_turn(self, turn: ConversationTurn) -> None:
        """Agrega un turno al log de conversación."""
        ...

    async def recent_turns(self, owner_id: str, limit: int) -> list[ConversationTurn]:
        """Devuelve los turnos más recientes del usuario, del más nuevo al más viejo."""
        ...

    async def add_facts(self, facts: list[EmbeddedFact]) -> None:
        """Persiste en lote hechos durables con su vector."""
        ...

    async def search_facts(
        self, owner_id: str, embedding: list[float], k: int, min_similarity: float
    ) -> list[RetrievedFact]:
        """Recupera hasta k hechos por similitud de coseno sobre el umbral dado."""
        ...
