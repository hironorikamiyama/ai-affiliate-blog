"""scope tags by blog

Revision ID: 80b23cefc1d9
Revises: b319643b6168
Create Date: 2026-08-27 23:16:13.624426

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "80b23cefc1d9"
down_revision: Union[str, Sequence[str], None] = "b319643b6168"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": (
        "fk_%(table_name)s_"
        "%(column_0_name)s_"
        "%(referred_table_name)s"
    ),
    "pk": "pk_%(table_name)s",
}


def upgrade() -> None:
    """Scope tags by blog."""

    # ------------------------------------
    # 1. blog_id を nullable=True で追加
    # ------------------------------------

    with op.batch_alter_table(
        "tags",
        schema=None,
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "blog_id",
                sa.Integer(),
                nullable=True,
            )
        )

    # ------------------------------------
    # 2. 既存Tagを既存Blogへ紐付け
    #
    # 現在の既存Blog:
    # id=1 電車釣行ブログ
    # ------------------------------------

    op.execute(
        sa.text(
            """
            UPDATE tags
            SET blog_id = 1
            WHERE blog_id IS NULL
            """
        )
    )

    # ------------------------------------
    # 3. blog_id を NOT NULL 化
    #    + ForeignKey追加
    # ------------------------------------

    with op.batch_alter_table(
        "tags",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "blog_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

        batch_op.create_foreign_key(
            "fk_tags_blog_id_blogs",
            "blogs",
            ["blog_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # ------------------------------------
    # 4. 既存のグローバルUNIQUEを解除
    #
    # name:
    #   無名 UNIQUE constraint
    #
    # slug:
    #   UNIQUE index
    # ------------------------------------

    with op.batch_alter_table(
        "tags",
        schema=None,
        naming_convention=NAMING_CONVENTION,
    ) as batch_op:
        batch_op.drop_constraint(
            "uq_tags_name",
            type_="unique",
        )

        batch_op.drop_index(
            "ix_tags_slug"
        )

    # ------------------------------------
    # 5. blog単位の制約を作成
    # ------------------------------------

    with op.batch_alter_table(
        "tags",
        schema=None,
    ) as batch_op:
        batch_op.create_index(
            "ix_tags_blog_id",
            ["blog_id"],
            unique=False,
        )

        batch_op.create_index(
            "ix_tags_slug",
            ["slug"],
            unique=False,
        )

        batch_op.create_unique_constraint(
            "uq_tags_blog_id_name",
            [
                "blog_id",
                "name",
            ],
        )

        batch_op.create_unique_constraint(
            "uq_tags_blog_id_slug",
            [
                "blog_id",
                "slug",
            ],
        )


def downgrade() -> None:
    """Restore global tag scope."""

    # ------------------------------------
    # 1. blog単位制約を削除
    # ------------------------------------

    with op.batch_alter_table(
        "tags",
        schema=None,
    ) as batch_op:
        batch_op.drop_constraint(
            "uq_tags_blog_id_slug",
            type_="unique",
        )

        batch_op.drop_constraint(
            "uq_tags_blog_id_name",
            type_="unique",
        )

        batch_op.drop_constraint(
            "fk_tags_blog_id_blogs",
            type_="foreignkey",
        )

        batch_op.drop_index(
            "ix_tags_blog_id"
        )

        batch_op.drop_index(
            "ix_tags_slug"
        )

    # ------------------------------------
    # 2. 旧グローバルUNIQUEを復元
    # ------------------------------------

    with op.batch_alter_table(
        "tags",
        schema=None,
    ) as batch_op:
        batch_op.create_unique_constraint(
            "uq_tags_name",
            ["name"],
        )

        batch_op.create_index(
            "ix_tags_slug",
            ["slug"],
            unique=True,
        )

    # ------------------------------------
    # 3. blog_id削除
    # ------------------------------------

    with op.batch_alter_table(
        "tags",
        schema=None,
    ) as batch_op:
        batch_op.drop_column(
            "blog_id"
        )