"""make_ticket_and_ai_flags_non_nullable

Revision ID: c91c8f5b6a42
Revises: b7c40d4fce57
Create Date: 2026-03-27 14:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c91c8f5b6a42"
down_revision: Union[str, Sequence[str], None] = "b7c40d4fce57"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE tickets SET is_public = 0 WHERE is_public IS NULL")
    op.execute("UPDATE tickets SET is_printed_intent = 0 WHERE is_printed_intent IS NULL")
    op.execute("UPDATE ai_chat_logs SET ai_risk_flag = 0 WHERE ai_risk_flag IS NULL")

    if op.get_bind().dialect.name == "sqlite":
        return

    op.alter_column(
        "tickets",
        "is_public",
        existing_type=sa.Boolean(),
        nullable=False,
    )
    op.alter_column(
        "tickets",
        "is_printed_intent",
        existing_type=sa.Boolean(),
        nullable=False,
    )
    op.alter_column(
        "ai_chat_logs",
        "ai_risk_flag",
        existing_type=sa.Boolean(),
        nullable=False,
    )


def downgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        return

    op.alter_column(
        "ai_chat_logs",
        "ai_risk_flag",
        existing_type=sa.Boolean(),
        nullable=True,
    )
    op.alter_column(
        "tickets",
        "is_printed_intent",
        existing_type=sa.Boolean(),
        nullable=True,
    )
    op.alter_column(
        "tickets",
        "is_public",
        existing_type=sa.Boolean(),
        nullable=True,
    )
