"""make site settings blog id required unique

Revision ID: c44f1e10226f
Revises: 2e17a04bf9bd
Create Date: 2026-08-27 19:25:50.324956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c44f1e10226f'
down_revision: Union[str, Sequence[str], None] = '2e17a04bf9bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    with op.batch_alter_table(
        "site_settings",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "blog_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

        batch_op.drop_index(
            "ix_site_settings_blog_id"
        )

        batch_op.create_index(
            "ix_site_settings_blog_id",
            ["blog_id"],
            unique=True,
        )


def downgrade() -> None:
    """Downgrade schema."""

    with op.batch_alter_table(
        "site_settings",
        schema=None,
    ) as batch_op:
        batch_op.drop_index(
            "ix_site_settings_blog_id"
        )

        batch_op.create_index(
            "ix_site_settings_blog_id",
            ["blog_id"],
            unique=False,
        )

        batch_op.alter_column(
            "blog_id",
            existing_type=sa.Integer(),
            nullable=True,
        )