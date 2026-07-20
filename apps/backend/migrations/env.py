"""Entorno de migraciones Alembic en modo async, alimentado por la config de la app."""

from __future__ import annotations

import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import AsyncEngine

from jarvis.adapters import db_models  # noqa: F401  (registra tablas de memoria en la metadata)
from jarvis.modules.heraldo import db_models as heraldo_models  # noqa: F401  (registra topics)
from jarvis.platform.config import get_settings
from jarvis.platform.db import create_engine
from jarvis.platform.orm import Base

target_metadata = Base.metadata


def _database_url() -> str:
    """Obtiene la URL de la base desde la configuración de la app."""
    return get_settings().database_url


def run_migrations_online() -> None:
    """Ejecuta las migraciones abriendo una conexión async."""
    asyncio.run(_run_async_migrations(create_engine(_database_url())))


async def _run_async_migrations(engine: AsyncEngine) -> None:
    """Corre las migraciones dentro de una conexión async y cierra el engine."""
    async with engine.connect() as connection:
        await connection.run_sync(_do_migrations)
    await engine.dispose()


def _do_migrations(connection: object) -> None:
    """Configura el contexto de Alembic y aplica las migraciones."""
    context.configure(connection=connection, target_metadata=target_metadata)  # type: ignore[arg-type]
    with context.begin_transaction():
        context.run_migrations()


run_migrations_online()
