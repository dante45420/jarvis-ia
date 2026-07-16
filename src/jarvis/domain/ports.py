"""Puertos del dominio: contratos que la infraestructura implementa como adaptadores.

El dominio depende de estas interfaces, nunca de proveedores concretos. Sumar o cambiar un
proveedor significa escribir un adaptador que cumpla el puerto, sin tocar dominio ni casos de uso.

Los puertos que dependen de entidades aún no modeladas (VectorStore, MemoryStore,
ChannelAdapter) se definen en la Fase 1, junto a sus entidades. Ver docs/ROADMAP.md.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from jarvis.domain.llm import LLMResult, Message
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

    async def embed(self, text: str) -> list[float]:
        """Devuelve el vector de embedding del texto."""
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
