"""add_selected_image_id_to_tickets

Revision ID: 9b3d1f5c2a10
Revises: f2a19c6d4b11
Create Date: 2026-02-25 20:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9b3d1f5c2a10"
down_revision: Union[str, Sequence[str], None] = "f2a19c6d4b11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("selected_image_id", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("tickets", "selected_image_id")
