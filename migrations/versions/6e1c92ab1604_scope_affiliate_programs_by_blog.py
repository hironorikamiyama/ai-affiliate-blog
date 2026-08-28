"""Scope affiliate programs by blog

Revision ID: 6e1c92ab1604
Revises: 8fceeb1c406a
Create Date: 2026-08-28 17:55:40.564570

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6e1c92ab1604"
down_revision: Union[str, Sequence[str], None] = "8fceeb1c406a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NAMING_CONVENTION = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def upgrade() -> None:
    """Scope affiliate programs by blog."""

    # Step 1:
    # Add blog_id as nullable first because existing rows already exist.
    with op.batch_alter_table(
        "affiliate_programs",
        naming_convention=NAMING_CONVENTION,
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "blog_id",
                sa.Integer(),
                nullable=True,
            )
        )

    # Step 2:
    # Existing affiliate programs belong to the initial blog.
    op.execute(
        sa.text(
            """
            UPDATE affiliate_programs
            SET blog_id = 1
            WHERE blog_id IS NULL
            """
        )
    )

    # Step 3:
    # After backfilling, enforce NOT NULL and create the FK.
    with op.batch_alter_table(
        "affiliate_programs",
        naming_convention=NAMING_CONVENTION,
    ) as batch_op:
        batch_op.alter_column(
            "blog_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

        batch_op.create_foreign_key(
            "fk_affiliate_programs_blog_id_blogs",
            "blogs",
            ["blog_id"],
            ["id"],
            ondelete="CASCADE",
        )

        batch_op.create_index(
            "ix_affiliate_programs_blog_id",
            ["blog_id"],
            unique=False,
        )


def downgrade() -> None:
    """Remove blog scoping from affiliate programs."""

    with op.batch_alter_table(
        "affiliate_programs",
        naming_convention=NAMING_CONVENTION,
    ) as batch_op:
        batch_op.drop_index(
            "ix_affiliate_programs_blog_id",
        )

        batch_op.drop_constraint(
            "fk_affiliate_programs_blog_id_blogs",
            type_="foreignkey",
        )

        batch_op.drop_column(
            "blog_id",
        )