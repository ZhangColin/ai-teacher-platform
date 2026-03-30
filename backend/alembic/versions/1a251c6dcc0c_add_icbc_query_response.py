"""add_icbc_query_response

Revision ID: 1a251c6dcc0c
Revises: d55ebc51c92b
Create Date: 2026-03-30 14:59:17.324672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a251c6dcc0c'
down_revision: Union[str, Sequence[str], None] = 'd55ebc51c92b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('payment_refunds',
        sa.Column('icbc_query_response', sa.JSON(), nullable=True, comment='工行退款查询接口响应')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('payment_refunds', 'icbc_query_response')
