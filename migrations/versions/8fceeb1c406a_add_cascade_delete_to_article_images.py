"""Add cascade delete to article images

Revision ID: 8fceeb1c406a
Revises: 80b23cefc1d9
Create Date: 2026-08-28 17:22:43.515313

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8fceeb1c406a"
down_revision: Union[str, Sequence[str], None] = "80b23cefc1d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NAMING_CONVENTION = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def upgrade() -> None:
    """Add ON DELETE CASCADE to article_images.article_id."""

    with op.batch_alter_table(
        "article_images",
        naming_convention=NAMING_CONVENTION,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_article_images_article_id_articles",
            type_="foreignkey",
        )

        batch_op.create_foreign_key(
            "fk_article_images_article_id_articles",
            "articles",
            ["article_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Remove ON DELETE CASCADE from article_images.article_id."""

    with op.batch_alter_table(
        "article_images",
        naming_convention=NAMING_CONVENTION,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_article_images_article_id_articles",
            type_="foreignkey",
        )

        batch_op.create_foreign_key(
            "fk_article_images_article_id_articles",
            "articles",
            ["article_id"],
            ["id"],
        )