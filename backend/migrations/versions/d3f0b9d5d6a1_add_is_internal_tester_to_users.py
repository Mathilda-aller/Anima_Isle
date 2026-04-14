"""add_is_internal_tester_to_users

Revision ID: d3f0b9d5d6a1
Revises: c91c8f5b6a42
Create Date: 2026-04-14 15:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3f0b9d5d6a1"
down_revision: Union[str, Sequence[str], None] = "c91c8f5b6a42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_internal_tester", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    if op.get_bind().dialect.name != "sqlite":
        op.alter_column("users", "is_internal_tester", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "is_internal_tester")
