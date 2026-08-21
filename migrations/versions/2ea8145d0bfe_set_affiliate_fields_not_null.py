"""set affiliate fields not null

Revision ID: 2ea8145d0bfe
Revises: e6afde0555eb
Create Date: 2026-08-21 21:49:04.672703

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ea8145d0bfe'
down_revision: Union[str, Sequence[str], None] = 'e6afde0555eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("affiliate_programs") as batch_op:
        batch_op.alter_column(
            "reward_type",
            existing_type=sa.String(length=50),
            nullable=False,
        )

        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=50),
            nullable=False,
        )

        batch_op.alter_column(
            "created_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )

        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("affiliate_programs") as batch_op:
        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(),
            nullable=True,
        )

        batch_op.alter_column(
            "created_at",
            existing_type=sa.DateTime(),
            nullable=True,
        )

        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=50),
            nullable=True,
        )

        batch_op.alter_column(
            "reward_type",
            existing_type=sa.String(length=50),
            nullable=True,
        )
        