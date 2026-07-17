"""Esquema inicial de memoria: log de turnos y hechos con vector e índice HNSW.

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIMENSIONS = 1024


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    _create_conversation_turns()
    _create_facts()


def downgrade() -> None:
    op.drop_table("facts")
    op.drop_table("conversation_turns")


def _create_conversation_turns() -> None:
    """Crea la tabla del log de conversación con índices por dueño y por tiempo."""
    op.create_table(
        "conversation_turns",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("owner_id", sa.String(64), nullable=False, index=True),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, index=True),
    )


def _create_facts() -> None:
    """Crea la tabla de hechos con su vector y el índice HNSW por similitud de coseno."""
    op.create_table(
        "facts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("owner_id", sa.String(64), nullable=False, index=True),
        sa.Column("subject", sa.String(128), nullable=False),
        sa.Column("predicate", sa.String(128), nullable=False),
        sa.Column("object", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_accessed", sa.DateTime(timezone=True), nullable=False),
        sa.Column("access_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=False),
    )
    op.create_index(
        "ix_facts_embedding_hnsw",
        "facts",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
