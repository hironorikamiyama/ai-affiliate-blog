"""backfill affiliate program defaults

Revision ID: e6afde0555eb
Revises: e688907d8f91
Create Date: 2026-08-21 21:45:34.191421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6afde0555eb'
down_revision: Union[str, Sequence[str], None] = 'e688907d8f91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE affiliate_programs
        SET
            reward_type = 'fixed',
            status = 'active',
            created_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE
            reward_type IS NULL
            OR status IS NULL
            OR created_at IS NULL
            OR updated_at IS NULL
    """)

def downgrade() -> None:
    """Downgrade schema."""
    pass
