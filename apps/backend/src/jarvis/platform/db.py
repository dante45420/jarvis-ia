"""Fábrica de conexión async a Postgres. Un solo engine y session factory por proceso."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_url: str) -> AsyncEngine:
    """Crea el engine async de SQLAlchemy para la URL dada."""
    return create_async_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Crea la fábrica de sesiones async ligada al engine."""
    return async_sessionmaker(engine, expire_on_commit=False)
