"""add_email_verification_codes

Revision ID: b7c40d4fce57
Revises: 9b3d1f5c2a10
Create Date: 2026-03-19 21:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c40d4fce57"
down_revision: Union[str, Sequence[str], None] = "9b3d1f5c2a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_verification_codes",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            nullable=False,
            autoincrement=True,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("code_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("send_count", sa.Integer(), nullable=False),
        sa.Column("requested_ip", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_email_verification_codes_id"), "email_verification_codes", ["id"], unique=False)
    op.create_index(op.f("ix_email_verification_codes_email"), "email_verification_codes", ["email"], unique=False)
    op.create_index(
        op.f("ix_email_verification_codes_code_hash"),
        "email_verification_codes",
        ["code_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_email_verification_codes_expires_at"),
        "email_verification_codes",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_email_verification_codes_created_at"),
        "email_verification_codes",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_email_verification_codes_created_at"), table_name="email_verification_codes")
    op.drop_index(op.f("ix_email_verification_codes_expires_at"), table_name="email_verification_codes")
    op.drop_index(op.f("ix_email_verification_codes_code_hash"), table_name="email_verification_codes")
    op.drop_index(op.f("ix_email_verification_codes_email"), table_name="email_verification_codes")
    op.drop_index(op.f("ix_email_verification_codes_id"), table_name="email_verification_codes")
    op.drop_table("email_verification_codes")
