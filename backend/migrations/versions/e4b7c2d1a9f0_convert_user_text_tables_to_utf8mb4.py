"""convert_user_text_tables_to_utf8mb4

Revision ID: e4b7c2d1a9f0
Revises: d3f0b9d5d6a1
Create Date: 2026-04-20 12:10:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "e4b7c2d1a9f0"
down_revision: Union[str, Sequence[str], None] = "d3f0b9d5d6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        return
    for table_name in ("users", "chat_sessions", "ai_chat_logs", "tickets"):
        op.execute(f"ALTER TABLE {table_name} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")


def downgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        return
    for table_name in ("tickets", "ai_chat_logs", "chat_sessions", "users"):
        op.execute(f"ALTER TABLE {table_name} CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci")
