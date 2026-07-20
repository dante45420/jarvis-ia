"""Esquema de Heraldo: tabla de entregas producidas por cada tema.

Revision ID: 0003_heraldo_deliveries
Revises: 0002_heraldo_topics
Create Date: 2026-07-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_heraldo_deliveries"
down_revision: str | None = "0002_heraldo_topics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "deliveries",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("topic_id", sa.String(64), nullable=False, index=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("deliveries")
