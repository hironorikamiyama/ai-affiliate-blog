"""make articles blog id required

Revision ID: efb25575c094
Revises: 3795d4f2924e
Create Date: 2026-08-27 19:50:02.465700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efb25575c094'
down_revision: Union[str, Sequence[str], None] = '3795d4f2924e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('articles') as batch_op:
        batch_op.alter_column(
            'blog_id',
            existing_type=sa.INTEGER(),
            nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('articles') as batch_op:
        batch_op.alter_column(
            'blog_id',
            existing_type=sa.INTEGER(),
            nullable=True,
        )