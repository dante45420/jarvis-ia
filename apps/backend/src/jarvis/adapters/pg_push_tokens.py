"""Adaptador de PushTokenStore sobre Postgres con SQLAlchemy async. La persistencia real."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jarvis.adapters.db_models import PushTokenRow
from jarvis.domain.notifications import PushToken


class PgPushTokenStore:
    """Implementa PushTokenStore con SQLAlchemy async; guarda por upsert sobre el token."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save(self, token: PushToken) -> None:
        """Inserta o actualiza el token del dispositivo por su clave."""
        async with self._session_factory() as session:
            await session.merge(_to_row(token))
            await session.commit()

    async def list_for_owner(self, owner_id: str) -> list[PushToken]:
        """Recupera los tokens del usuario."""
        stmt = select(PushTokenRow).where(PushTokenRow.owner_id == owner_id)
        async with self._session_factory() as session:
            rows = (await session.scalars(stmt)).all()
        return [_to_token(row) for row in rows]


def _to_row(token: PushToken) -> PushTokenRow:
    """Traduce un token de dominio a fila."""
    return PushTokenRow(
        token=token.token,
        owner_id=token.owner_id,
        platform=token.platform,
        created_at=token.created_at,
    )


def _to_token(row: PushTokenRow) -> PushToken:
    """Traduce una fila a token de dominio."""
    return PushToken(
        owner_id=row.owner_id,
        token=row.token,
        platform=row.platform,
        created_at=row.created_at,
    )
