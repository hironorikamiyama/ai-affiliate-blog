"""backfill article defaults

Revision ID: 31f96b72bf9f
Revises: 1a667e76fd1e
Create Date: 2026-08-23 08:42:23.100881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31f96b72bf9f'
down_revision: Union[str, Sequence[str], None] = '1a667e76fd1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
