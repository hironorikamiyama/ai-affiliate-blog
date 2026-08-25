"""add categories and tags

Revision ID: 553a791e9639
Revises: 51b4e006bf57
Create Date: 2026-08-25 12:35:40.312081

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "553a791e9639"
down_revision: Union[str, Sequence[str], None] = "51b4e006bf57"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ========================================
    # categories
    # ========================================

    op.create_table(
        "categories",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "slug",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_index(
        op.f("ix_categories_id"),
        "categories",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_categories_slug"),
        "categories",
        ["slug"],
        unique=True,
    )

    # ========================================
    # tags
    # ========================================

    op.create_table(
        "tags",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "slug",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_index(
        op.f("ix_tags_id"),
        "tags",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_tags_slug"),
        "tags",
        ["slug"],
        unique=True,
    )

    # ========================================
    # article_tags
    # ========================================

    op.create_table(
        "article_tags",
        sa.Column(
            "article_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "tag_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["articles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "article_id",
            "tag_id",
        ),
    )

    # ========================================
    # articles.category_id
    #
    # SQLiteではALTER CONSTRAINTを
    # 直接使えないためbatch modeを使用
    # ========================================

    with op.batch_alter_table(
        "articles",
        schema=None,
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "category_id",
                sa.Integer(),
                nullable=True,
            )
        )

        batch_op.create_index(
            batch_op.f(
                "ix_articles_category_id"
            ),
            ["category_id"],
            unique=False,
        )

        batch_op.create_foreign_key(
            "fk_articles_category_id_categories",
            "categories",
            ["category_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema."""

    # ========================================
    # articles.category_id
    # ========================================

    with op.batch_alter_table(
        "articles",
        schema=None,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_articles_category_id_categories",
            type_="foreignkey",
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_articles_category_id"
            )
        )

        batch_op.drop_column(
            "category_id"
        )

    # ========================================
    # article_tags
    # ========================================

    op.drop_table(
        "article_tags"
    )

    # ========================================
    # tags
    # ========================================

    op.drop_index(
        op.f("ix_tags_slug"),
        table_name="tags",
    )

    op.drop_index(
        op.f("ix_tags_id"),
        table_name="tags",
    )

    op.drop_table(
        "tags"
    )

    # ========================================
    # categories
    # ========================================

    op.drop_index(
        op.f("ix_categories_slug"),
        table_name="categories",
    )

    op.drop_index(
        op.f("ix_categories_id"),
        table_name="categories",
    )

    op.drop_table(
        "categories"
    )
