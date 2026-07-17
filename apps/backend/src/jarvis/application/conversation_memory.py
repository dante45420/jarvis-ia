"""Orquestador de memoria: guarda turnos, aprende hechos y arma el contexto para el LLM."""

from __future__ import annotations

from datetime import datetime

from jarvis.application.context import ContextBudget, assemble_context
from jarvis.application.fact_extraction import extract_facts
from jarvis.domain.llm import Message
from jarvis.domain.memory import ConversationTurn, EmbeddedFact, Fact
from jarvis.domain.ports import EmbeddingProvider, MemoryStore


class ConversationMemory:
    """Compone el almacén de memoria y el proveedor de embeddings en operaciones de alto nivel."""

    def __init__(
        self,
        store: MemoryStore,
        embedder: EmbeddingProvider,
        budget: ContextBudget | None = None,
        top_k: int = 5,
        min_similarity: float = 0.75,
        dedup_similarity: float = 0.95,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._budget = budget or ContextBudget()
        self._top_k = top_k
        self._min_similarity = min_similarity
        self._dedup_similarity = dedup_similarity

    async def record_user_message(self, owner_id: str, text: str, now: datetime) -> list[Fact]:
        """Guarda el turno del usuario y aprende los hechos determinísticos que contenga."""
        await self._store.append_turn(ConversationTurn(owner_id, "user", text, now))
        facts = extract_facts(owner_id, text, now)
        return await self._learn(facts) if facts else []

    async def record_assistant_message(self, owner_id: str, text: str, now: datetime) -> None:
        """Guarda el turno del asistente en el log."""
        await self._store.append_turn(ConversationTurn(owner_id, "assistant", text, now))

    async def build_context(
        self, owner_id: str, query: str, recent_turns: int = 8
    ) -> list[Message]:
        """Arma el contexto para responder: hechos relevantes (RAG) + turnos recientes."""
        turns = await self._store.recent_turns(owner_id, recent_turns)
        query_vector = (await self._embedder.embed(query)).vector
        facts = await self._store.search_facts(
            owner_id, query_vector, self._top_k, self._min_similarity
        )
        return assemble_context(facts, turns, self._budget)

    async def _learn(self, facts: list[Fact]) -> list[Fact]:
        """Embebe los hechos en lote, descarta duplicados y persiste los nuevos."""
        batch = await self._embedder.embed_batch([fact.as_text() for fact in facts])
        fresh = await self._keep_new(facts, batch.vectors)
        if fresh:
            await self._store.add_facts(fresh)
        return [embedded.fact for embedded in fresh]

    async def _keep_new(self, facts: list[Fact], vectors: list[list[float]]) -> list[EmbeddedFact]:
        """Deja fuera los hechos ya conocidos (similitud sobre el umbral de dedup)."""
        fresh: list[EmbeddedFact] = []
        for fact, vector in zip(facts, vectors, strict=True):
            if not await self._is_duplicate(fact.owner_id, vector):
                fresh.append(EmbeddedFact(fact, vector))
        return fresh

    async def _is_duplicate(self, owner_id: str, vector: list[float]) -> bool:
        """Indica si ya existe un hecho casi idéntico al vector dado."""
        hits = await self._store.search_facts(owner_id, vector, 1, self._dedup_similarity)
        return len(hits) > 0
