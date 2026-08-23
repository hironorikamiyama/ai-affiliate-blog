"""backfill article fields

Revision ID: 5b371a7ad8fc
Revises: 31f96b72bf9f
Create Date: 2026-08-23 08:52:53.369972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b371a7ad8fc'
down_revision: Union[str, Sequence[str], None] = '31f96b72bf9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Backfill existing article rows."""
    op.execute(
        """
        UPDATE articles
        SET
            slug = 'article-' || id,
            created_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE
            slug IS NULL
            OR created_at IS NULL
            OR updated_at IS NULL
        """
    )


def downgrade() -> None:
    """Downgrade data migration."""
    pass