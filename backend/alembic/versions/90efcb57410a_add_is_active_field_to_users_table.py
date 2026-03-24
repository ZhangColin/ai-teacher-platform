"""add is_active field to users table

Revision ID: 90efcb57410a
Revises: 20260323_init_hcy
Create Date: 2026-03-24 12:07:21.815447

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90efcb57410a'
down_revision: Union[str, Sequence[str], None] = '20260323_init_hcy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加 is_active 字段
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='用户是否激活'))
    # 添加索引
    op.create_index('ix_users_is_active', 'users', ['is_active'])


def downgrade() -> None:
    """Downgrade schema."""
    # 删除索引
    op.drop_index('ix_users_is_active', 'users')
    # 删除字段
    op.drop_column('users', 'is_active')
