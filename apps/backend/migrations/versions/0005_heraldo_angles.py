"""Esquema de Heraldo: memoria de ángulos ya tratados por tema, con vector e índice HNSW.

Revision ID: 0005_heraldo_angles
Revises: 0004_heraldo_topic_onboarding
Create Date: 2026-07-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0005_heraldo_angles"
down_revision: str | None = "0004_heraldo_topic_onboarding"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIMENSIONS = 1024


def upgrade() -> None:
    op.create_table(
        "episode_angles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("topic_id", sa.String(64), nullable=False, index=True),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=False),
    )
    op.create_index(
        "ix_episode_angles_embedding_hnsw",
        "episode_angles",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_table("episode_angles")
