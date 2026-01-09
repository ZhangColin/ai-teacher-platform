"""create_common_tools_tables

Revision ID: b1c2d3e4f5g6
Revises: 000af84421da
Create Date: 2026-01-09 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5g6'
down_revision: Union[str, Sequence[str], None] = '000af84421da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 tool_categories 和 common_tools 表"""
    # 创建 tool_categories 表
    op.create_table(
        'tool_categories',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_order', 'tool_categories', ['order'])
    
    # 创建 common_tools 表
    op.create_table(
        'common_tools',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=False),
        sa.Column('category_id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.Enum('built-in', 'html', name='commontooltype'), nullable=False),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('html_path', sa.String(length=255), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('visible', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['tool_categories.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_category_id', 'common_tools', ['category_id'])
    op.create_index('idx_visible', 'common_tools', ['visible'])
    op.create_index('idx_category_order', 'common_tools', ['category_id', 'order'])


def downgrade() -> None:
    """删除 tool_categories 和 common_tools 表"""
    op.drop_index('idx_category_order', table_name='common_tools')
    op.drop_index('idx_visible', table_name='common_tools')
    op.drop_index('idx_category_id', table_name='common_tools')
    op.drop_table('common_tools')
    op.drop_index('idx_order', table_name='tool_categories')
    op.drop_table('tool_categories')
