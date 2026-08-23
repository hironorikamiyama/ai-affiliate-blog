"""set article fields not null

Revision ID: 8e211ea1b3f6
Revises: 5b371a7ad8fc
Create Date: 2026-08-23 08:54:21.648244

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e211ea1b3f6'
down_revision: Union[str, Sequence[str], None] = '5b371a7ad8fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("articles") as batch_op:
        batch_op.alter_column(
            "slug",
            existing_type=sa.VARCHAR(length=300),
            nullable=False,
        )

        batch_op.alter_column(
            "created_at",
            existing_type=sa.DATETIME(),
            nullable=False,
        )

        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DATETIME(),
            nullable=False,
        )

def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("articles") as batch_op:
        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DATETIME(),
            nullable=True,
        )

        batch_op.alter_column(
            "created_at",
            existing_type=sa.DATETIME(),
            nullable=True,
        )

        batch_op.alter_column(
            "slug",
            existing_type=sa.VARCHAR(length=300),
            nullable=True,
        )
