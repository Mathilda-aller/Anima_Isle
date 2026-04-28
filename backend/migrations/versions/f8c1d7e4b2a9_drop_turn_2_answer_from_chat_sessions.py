"""drop_turn_2_answer_from_chat_sessions

Revision ID: f8c1d7e4b2a9
Revises: d3f0b9d5d6a1
Create Date: 2026-04-28 17:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8c1d7e4b2a9"
down_revision: Union[str, Sequence[str], None] = "d3f0b9d5d6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("chat_sessions", "turn_2_answer")


def downgrade() -> None:
    op.add_column("chat_sessions", sa.Column("turn_2_answer", sa.Text(), nullable=True))
