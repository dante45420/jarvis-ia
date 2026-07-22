"""Modelos SQLAlchemy de Heraldo: el esquema físico tras los puertos de repositorio."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from jarvis.adapters.db_models import EMBEDDING_DIMENSIONS
from jarvis.platform.orm import Base


class TopicRow(Base):
    """Fila de un tema seguido, con su perfil de búsqueda aplanado en columnas."""

    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(256))
    subtopics: Mapped[list[str]] = mapped_column(ARRAY(Text))
    include_keywords: Mapped[list[str]] = mapped_column(ARRAY(Text))
    exclude_keywords: Mapped[list[str]] = mapped_column(ARRAY(Text))
    reach_threshold: Mapped[int] = mapped_column(Integer)
    recency_hours: Mapped[int] = mapped_column(Integer)
    podcast_style: Mapped[str] = mapped_column(String(16))
    state: Mapped[str] = mapped_column(String(16), index=True)
    cadence_frequency: Mapped[str] = mapped_column(String(16), default="daily")
    cadence_every_days: Mapped[int] = mapped_column(Integer, default=1)
    cadence_hour: Mapped[int] = mapped_column(Integer, default=8)
    onboarding: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class AngleRow(Base):
    """Fila de un ángulo ya tratado por un tema, con su vector para deduplicar por similitud."""

    __tablename__ = "episode_angles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[str] = mapped_column(String(64), index=True)
    summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS))


class DeliveryRow(Base):
    """Fila de una entrega producida por un tema, con su marca de consumo."""

    __tablename__ = "deliveries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    topic_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
