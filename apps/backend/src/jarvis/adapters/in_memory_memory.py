"""MemoryStore en memoria para tests y desarrollo. La persistencia real es el adaptador pgvector."""

from __future__ import annotations

from jarvis.domain.memory import (
    ConversationTurn,
    EmbeddedFact,
    RetrievedFact,
)
from jarvis.platform.vectors import cosine_similarity


class InMemoryMemoryStore:
    """Implementa MemoryStore con listas en memoria y similitud de coseno en Python."""

    def __init__(self) -> None:
        self._turns: list[ConversationTurn] = []
        self._facts: list[EmbeddedFact] = []

    async def append_turn(self, turn: ConversationTurn) -> None:
        """Agrega un turno al log."""
        self._turns.append(turn)

    async def recent_turns(self, owner_id: str, limit: int) -> list[ConversationTurn]:
        """Devuelve los turnos del usuario, del más nuevo al más viejo, hasta el límite."""
        owned = [turn for turn in self._turns if turn.owner_id == owner_id]
        return list(reversed(owned))[:limit]

    async def add_facts(self, facts: list[EmbeddedFact]) -> None:
        """Persiste en lote hechos con su vector."""
        self._facts.extend(facts)

    async def search_facts(
        self, owner_id: str, embedding: list[float], k: int, min_similarity: float
    ) -> list[RetrievedFact]:
        """Recupera los k hechos más similares del usuario que superan el umbral."""
        scored = self._scored_facts(owner_id, embedding)
        above = [item for item in scored if item.similarity >= min_similarity]
        above.sort(key=lambda item: item.similarity, reverse=True)
        return above[:k]

    def _scored_facts(self, owner_id: str, embedding: list[float]) -> list[RetrievedFact]:
        """Puntúa cada hecho del usuario por similitud con el vector de consulta."""
        return [
            RetrievedFact(item.fact, cosine_similarity(embedding, item.embedding))
            for item in self._facts
            if item.fact.owner_id == owner_id
        ]
