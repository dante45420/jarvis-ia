"""Fábrica de conexión async a Postgres. Un solo engine y session factory por proceso."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_url: str) -> AsyncEngine:
    """Crea el engine async de SQLAlchemy; exige SSL en Postgres remoto (Supabase)."""
    return create_async_engine(
        database_url, pool_pre_ping=True, connect_args=_connect_args(database_url)
    )


def _connect_args(database_url: str) -> dict[str, object]:
    """SSL obligatorio para hosts remotos; local (docker) sin SSL."""
    if _is_remote_postgres(database_url):
        return {"ssl": "require"}
    return {}


def _is_remote_postgres(database_url: str) -> bool:
    """Indica si la URL apunta a un Postgres remoto (no local)."""
    return "asyncpg" in database_url and not any(
        host in database_url for host in ("localhost", "127.0.0.1")
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Crea la fábrica de sesiones async ligada al engine."""
    return async_sessionmaker(engine, expire_on_commit=False)
