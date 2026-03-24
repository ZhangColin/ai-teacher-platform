"""merge heads before payment tables

Revision ID: f71224133188
Revises: 90efcb57410a, b8h9i0j1k2l3
Create Date: 2026-03-24 17:00:07.719909

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f71224133188'
down_revision: Union[str, Sequence[str], None] = ('90efcb57410a', 'b8h9i0j1k2l3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
