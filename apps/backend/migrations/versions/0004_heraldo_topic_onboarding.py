"""Esquema de Heraldo: cadencia y onboarding por tema.

Revision ID: 0004_heraldo_topic_onboarding
Revises: 0003_heraldo_deliveries
Create Date: 2026-07-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_heraldo_topic_onboarding"
down_revision: str | None = "0003_heraldo_deliveries"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "topics",
        sa.Column("cadence_frequency", sa.String(16), nullable=False, server_default="daily"),
    )
    op.add_column(
        "topics", sa.Column("cadence_every_days", sa.Integer, nullable=False, server_default="1")
    )
    op.add_column(
        "topics", sa.Column("cadence_hour", sa.Integer, nullable=False, server_default="8")
    )
    op.add_column("topics", sa.Column("onboarding", sa.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("topics", "onboarding")
    op.drop_column("topics", "cadence_hour")
    op.drop_column("topics", "cadence_every_days")
    op.drop_column("topics", "cadence_frequency")
