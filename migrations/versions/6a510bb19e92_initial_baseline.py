"""initial baseline

Revision ID: 6a510bb19e92
Revises:
Create Date: 2026-08-21 21:34:57.968053

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6a510bb19e92"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial application tables."""

    op.create_table(
        "affiliate_programs",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "asp_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "affiliate_url",
            sa.String(length=1000),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.String(length=100),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_affiliate_programs_id"),
        "affiliate_programs",
        ["id"],
        unique=False,
    )

    op.create_table(
        "articles",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "affiliate_program_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=300),
            nullable=False,
        ),
        sa.Column(
            "keyword",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "body",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["affiliate_program_id"],
            ["affiliate_programs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_articles_id"),
        "articles",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop initial application tables."""

    op.drop_index(
        op.f("ix_articles_id"),
        table_name="articles",
    )

    op.drop_table(
        "articles",
    )

    op.drop_index(
        op.f("ix_affiliate_programs_id"),
        table_name="affiliate_programs",
    )

    op.drop_table(
        "affiliate_programs",
    )