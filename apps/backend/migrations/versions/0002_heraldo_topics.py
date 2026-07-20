"""Esquema de Heraldo: tabla de temas seguidos.

Revision ID: 0002_heraldo_topics
Revises: 0001_initial
Create Date: 2026-07-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_heraldo_topics"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_id", sa.String(64), nullable=False, index=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("subtopics", sa.ARRAY(sa.Text), nullable=False),
        sa.Column("include_keywords", sa.ARRAY(sa.Text), nullable=False),
        sa.Column("exclude_keywords", sa.ARRAY(sa.Text), nullable=False),
        sa.Column("reach_threshold", sa.Integer, nullable=False),
        sa.Column("recency_hours", sa.Integer, nullable=False),
        sa.Column("podcast_style", sa.String(16), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("topics")
