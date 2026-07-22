"""Adaptador de AngleStore sobre Postgres + pgvector. La memoria real de ángulos por tema."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jarvis.modules.heraldo.angles import EpisodeAngle
from jarvis.modules.heraldo.db_models import AngleRow


class PgAngleStore:
    """Implementa AngleStore con SQLAlchemy async; la similitud usa distancia de coseno en la DB."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add(self, angle: EpisodeAngle) -> None:
        """Inserta el ángulo con su vector."""
        async with self._session_factory() as session:
            session.add(_to_row(angle))
            await session.commit()

    async def similar(self, topic_id: str, embedding: list[float], k: int) -> list[str]:
        """Recupera hasta k resúmenes del tema más cercanos al vector, por distancia de coseno."""
        distance = AngleRow.embedding.cosine_distance(embedding)
        stmt = (
            select(AngleRow.summary)
            .where(AngleRow.topic_id == topic_id)
            .order_by(distance)
            .limit(k)
        )
        async with self._session_factory() as session:
            rows = (await session.scalars(stmt)).all()
        return list(rows)


def _to_row(angle: EpisodeAngle) -> AngleRow:
    """Traduce un ángulo de dominio a fila."""
    return AngleRow(
        topic_id=angle.topic_id,
        summary=angle.summary,
        created_at=angle.created_at,
        embedding=angle.embedding,
    )
