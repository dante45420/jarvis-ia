"""Modelos SQLAlchemy de Heraldo: el esquema físico tras los puertos de repositorio."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ARRAY, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

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


class DeliveryRow(Base):
    """Fila de una entrega producida por un tema, con su marca de consumo."""

    __tablename__ = "deliveries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    topic_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
