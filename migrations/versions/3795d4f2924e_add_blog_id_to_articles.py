"""add blog id to articles

Revision ID: 3795d4f2924e
Revises: c44f1e10226f
Create Date: 2026-08-27 19:43:21.979386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3795d4f2924e'
down_revision: Union[str, Sequence[str], None] = 'c44f1e10226f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    with op.batch_alter_table(
        "articles",
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
            "ix_articles_blog_id",
            ["blog_id"],
            unique=False,
        )

        batch_op.create_foreign_key(
            "fk_articles_blog_id_blogs",
            "blogs",
            ["blog_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Downgrade schema."""

    with op.batch_alter_table(
        "articles",
        schema=None,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_articles_blog_id_blogs",
            type_="foreignkey",
        )

        batch_op.drop_index(
            "ix_articles_blog_id"
        )

        batch_op.drop_column(
            "blog_id"
        )
