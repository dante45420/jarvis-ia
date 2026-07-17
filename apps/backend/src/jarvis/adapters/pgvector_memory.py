"""Adaptador de MemoryStore sobre Postgres + pgvector. La persistencia real de la memoria."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jarvis.adapters.db_models import ConversationTurnRow, FactRow
from jarvis.domain.memory import (
    ConversationTurn,
    EmbeddedFact,
    Fact,
    RetrievedFact,
)


class PgVectorMemoryStore:
    """Implementa MemoryStore con SQLAlchemy async; la búsqueda usa distancia de coseno en la DB."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def append_turn(self, turn: ConversationTurn) -> None:
        """Inserta un turno en el log."""
        async with self._session_factory() as session:
            session.add(_to_turn_row(turn))
            await session.commit()

    async def recent_turns(self, owner_id: str, limit: int) -> list[ConversationTurn]:
        """Recupera los turnos más recientes del usuario, del más nuevo al más viejo."""
        stmt = (
            select(ConversationTurnRow)
            .where(ConversationTurnRow.owner_id == owner_id)
            .order_by(ConversationTurnRow.occurred_at.desc())
            .limit(limit)
        )
        async with self._session_factory() as session:
            rows = (await session.scalars(stmt)).all()
        return [_to_turn(row) for row in rows]

    async def add_facts(self, facts: list[EmbeddedFact]) -> None:
        """Inserta en lote los hechos con su vector."""
        async with self._session_factory() as session:
            session.add_all([_to_fact_row(item) for item in facts])
            await session.commit()

    async def search_facts(
        self, owner_id: str, embedding: list[float], k: int, min_similarity: float
    ) -> list[RetrievedFact]:
        """Recupera hasta k hechos del usuario cuya similitud de coseno supera el umbral."""
        distance = FactRow.embedding.cosine_distance(embedding)
        stmt = (
            select(FactRow, distance.label("distance"))
            .where(FactRow.owner_id == owner_id, distance <= 1 - min_similarity)
            .order_by(distance)
            .limit(k)
        )
        async with self._session_factory() as session:
            rows = (await session.execute(stmt)).all()
        return [_to_retrieved(row.FactRow, row.distance) for row in rows]


def _to_turn_row(turn: ConversationTurn) -> ConversationTurnRow:
    """Traduce un turno de dominio a fila."""
    return ConversationTurnRow(
        owner_id=turn.owner_id, role=turn.role, content=turn.content, occurred_at=turn.occurred_at
    )


def _to_turn(row: ConversationTurnRow) -> ConversationTurn:
    """Traduce una fila a turno de dominio."""
    return ConversationTurn(
        owner_id=row.owner_id, role=row.role, content=row.content, occurred_at=row.occurred_at
    )


def _to_fact_row(item: EmbeddedFact) -> FactRow:
    """Traduce un hecho embebido a fila, inicializando los campos de decaimiento."""
    fact = item.fact
    return FactRow(
        owner_id=fact.owner_id,
        subject=fact.subject,
        predicate=fact.predicate,
        object=fact.object,
        created_at=fact.created_at,
        last_accessed=fact.created_at,
        access_count=0,
        embedding=item.embedding,
    )


def _to_retrieved(row: FactRow, distance: float) -> RetrievedFact:
    """Traduce una fila y su distancia a un hecho recuperado con similitud."""
    fact = Fact(
        owner_id=row.owner_id,
        subject=row.subject,
        predicate=row.predicate,
        object=row.object,
        created_at=row.created_at,
    )
    return RetrievedFact(fact=fact, similarity=1 - distance)
