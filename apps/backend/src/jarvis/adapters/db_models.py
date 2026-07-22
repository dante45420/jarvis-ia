"""Modelos SQLAlchemy del almacén de memoria. El esquema físico detrás del puerto MemoryStore."""

from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from jarvis.platform.orm import Base

EMBEDDING_DIMENSIONS = 1024


class ConversationTurnRow(Base):
    """Fila del log de conversación. Fuente de verdad de los turnos."""

    __tablename__ = "conversation_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class PushTokenRow(Base):
    """Fila del token de push de un dispositivo. Clave por token para no duplicar dispositivos."""

    __tablename__ = "push_tokens"

    token: Mapped[str] = mapped_column(String(256), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FactRow(Base):
    """Fila de un hecho durable graph-ready, con su vector y campos de decaimiento."""

    __tablename__ = "facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    subject: Mapped[str] = mapped_column(String(128))
    predicate: Mapped[str] = mapped_column(String(128))
    object: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_accessed: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS))
