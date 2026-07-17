"""Tests del orquestador de memoria con el almacén en memoria y embeddings fake."""

from datetime import datetime

from jarvis.adapters.in_memory_memory import InMemoryMemoryStore
from jarvis.application.conversation_memory import ConversationMemory
from tests.fakes import FakeEmbeddingProvider

NOW = datetime(2026, 7, 17)


def _memory() -> ConversationMemory:
    # El embedder fake es bolsa-de-palabras (no semántico): usamos umbral bajo para probar el
    # cableado de recuperación, no la calidad del embedding real.
    return ConversationMemory(InMemoryMemoryStore(), FakeEmbeddingProvider(), min_similarity=0.0)


async def test_records_turn_and_learns_fact() -> None:
    memory = _memory()
    learned = await memory.record_user_message("dante", "me llamo Dante", NOW)
    assert any(f.object == "Dante" for f in learned)


async def test_skips_duplicate_facts() -> None:
    memory = _memory()
    await memory.record_user_message("dante", "me llamo Dante", NOW)
    learned_again = await memory.record_user_message("dante", "me llamo Dante", NOW)
    assert learned_again == []


async def test_build_context_includes_learned_fact() -> None:
    memory = _memory()
    await memory.record_user_message("dante", "mi jefe es Ana", NOW)
    messages = await memory.build_context("dante", "quién es mi jefe")
    joined = " ".join(m.content for m in messages)
    assert "jefe Ana" in joined


async def test_memory_is_scoped_by_owner() -> None:
    memory = _memory()
    await memory.record_user_message("dante", "me llamo Dante", NOW)
    messages = await memory.build_context("otro", "cómo me llamo")
    assert all("Dante" not in m.content for m in messages)
