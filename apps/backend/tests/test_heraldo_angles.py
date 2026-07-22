"""Tests de la memoria de ángulos: recuerda lo tratado y recupera lo relevante por similitud."""

from __future__ import annotations

from datetime import UTC, datetime

from jarvis.domain.embedding import BatchEmbeddingResult, EmbeddingResult
from jarvis.modules.heraldo.angles import AngleMemory
from jarvis.modules.heraldo.in_memory_angles import InMemoryAngleStore

NOW = datetime(2026, 7, 20, tzinfo=UTC)

_VECTORS = {
    "El rol del criterio": [1.0, 0.0],
    "La disciplina diaria": [0.0, 1.0],
    "criterio para decidir": [0.9, 0.1],
}


class FakeEmbedder:
    """Embedder de prueba: mapea textos conocidos a vectores fijos, sin red."""

    async def embed(self, text: str) -> EmbeddingResult:
        return EmbeddingResult(vector=_VECTORS[text], tokens=0)

    async def embed_batch(self, texts: list[str]) -> BatchEmbeddingResult:
        return BatchEmbeddingResult(vectors=[_VECTORS[t] for t in texts], tokens=0)


def _memory(store: InMemoryAngleStore) -> AngleMemory:
    return AngleMemory(FakeEmbedder(), store, k=5)


async def test_covered_returns_closest_angles_first() -> None:
    store = InMemoryAngleStore()
    memory = _memory(store)
    await memory.remember("t1", "El rol del criterio", NOW)
    await memory.remember("t1", "La disciplina diaria", NOW)

    covered = await memory.covered("t1", "criterio para decidir")

    assert covered[0] == "El rol del criterio"


async def test_covered_ignores_other_topics() -> None:
    store = InMemoryAngleStore()
    memory = _memory(store)
    await memory.remember("otro", "El rol del criterio", NOW)

    assert await memory.covered("t1", "criterio para decidir") == ()


async def test_empty_query_returns_no_covered_angles() -> None:
    memory = _memory(InMemoryAngleStore())
    assert await memory.covered("t1", "   ") == ()


async def test_blank_summary_is_not_stored() -> None:
    store = InMemoryAngleStore()
    memory = _memory(store)
    await memory.remember("t1", "  ", NOW)
    assert await store.similar("t1", [1.0, 0.0], 5) == []
