"""Adaptador de TopicStore sobre Postgres con SQLAlchemy async. La persistencia real de temas."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.elements import ColumnElement

from jarvis.modules.heraldo.db_models import TopicRow
from jarvis.modules.heraldo.domain import PodcastStyle, Topic, TopicProfile, TopicState


class PgTopicStore:
    """Implementa TopicStore con SQLAlchemy async; guarda por upsert y filtra por dueño y estado."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save(self, topic: Topic) -> None:
        """Inserta o actualiza el tema por su id."""
        async with self._session_factory() as session:
            await session.merge(_to_row(topic))
            await session.commit()

    async def get(self, topic_id: str) -> Topic | None:
        """Recupera un tema por id."""
        stmt = select(TopicRow).where(TopicRow.id == topic_id)
        async with self._session_factory() as session:
            row = (await session.scalars(stmt)).one_or_none()
        return _to_topic(row) if row is not None else None

    async def list_by_owner(self, owner_id: str) -> list[Topic]:
        """Recupera todos los temas del usuario."""
        return await self._query(TopicRow.owner_id == owner_id)

    async def list_active(self, owner_id: str) -> list[Topic]:
        """Recupera los temas activos del usuario."""
        return await self._query(
            (TopicRow.owner_id == owner_id) & (TopicRow.state == TopicState.ACTIVE.value)
        )

    async def _query(self, condition: ColumnElement[bool]) -> list[Topic]:
        """Ejecuta una consulta de temas con la condición dada y mapea el resultado."""
        stmt = select(TopicRow).where(condition)
        async with self._session_factory() as session:
            rows = (await session.scalars(stmt)).all()
        return [_to_topic(row) for row in rows]


def _to_row(topic: Topic) -> TopicRow:
    """Traduce un tema de dominio a fila, aplanando su perfil en columnas."""
    profile = topic.profile
    return TopicRow(
        id=topic.id,
        owner_id=topic.owner_id,
        name=topic.name,
        subtopics=list(profile.subtopics),
        include_keywords=list(profile.include_keywords),
        exclude_keywords=list(profile.exclude_keywords),
        reach_threshold=profile.reach_threshold,
        recency_hours=profile.recency_hours,
        podcast_style=topic.podcast_style.value,
        state=topic.state.value,
    )


def _to_topic(row: TopicRow) -> Topic:
    """Traduce una fila a tema de dominio, reconstruyendo su perfil."""
    profile = TopicProfile(
        subtopics=tuple(row.subtopics),
        include_keywords=tuple(row.include_keywords),
        exclude_keywords=tuple(row.exclude_keywords),
        reach_threshold=row.reach_threshold,
        recency_hours=row.recency_hours,
    )
    return Topic(
        id=row.id,
        owner_id=row.owner_id,
        name=row.name,
        profile=profile,
        podcast_style=PodcastStyle(row.podcast_style),
        state=TopicState(row.state),
    )
