"""add blog id to site settings

Revision ID: 2e17a04bf9bd
Revises: 911b5324d990
Create Date: 2026-08-27 19:12:45.486954

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e17a04bf9bd'
down_revision: Union[str, Sequence[str], None] = '911b5324d990'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    with op.batch_alter_table(
        "site_settings",
        schema=None,
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "blog_id",
                sa.Integer(),
                nullable=True,
            )
        )

        batch_op.create_index(
            "ix_site_settings_blog_id",
            ["blog_id"],
            unique=False,
        )

        batch_op.create_foreign_key(
            "fk_site_settings_blog_id_blogs",
            "blogs",
            ["blog_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Downgrade schema."""

    with op.batch_alter_table(
        "site_settings",
        schema=None,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_site_settings_blog_id_blogs",
            type_="foreignkey",
        )

        batch_op.drop_index(
            "ix_site_settings_blog_id",
        )

        batch_op.drop_column(
            "blog_id",
        )