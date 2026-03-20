"""add ai tool config tables

Revision ID: e76e4604e3f4
Revises: 47a947d71251
Create Date: 2026-03-20 20:34:35.471461

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'e76e4604e3f4'  # 保留生成的值
down_revision = '47a947d71251'  # 保留生成的值
branch_labels = None
depends_on = None


def upgrade():
    # 创建 navigation_modules 表
    op.create_table(
        'navigation_modules',
        sa.Column('id', mysql.CHAR(36), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('type', sa.Enum('toolset', 'page', name='navigationmoduletype'), nullable=False),
        sa.Column('config_source', sa.String(100), nullable=True),
        sa.Column('page_path', sa.String(100), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4'
    )
    op.create_index('idx_navigation_module_order', 'navigation_modules', ['order'])

    # 创建 toolsets 表
    op.create_table(
        'toolsets',
        sa.Column('id', mysql.CHAR(36), nullable=False),
        sa.Column('toolset_id', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('toolset_id'),
        mysql_charset='utf8mb4'
    )
    op.create_index(op.f('ix_toolsets_toolset_id'), 'toolsets', ['toolset_id'])

    # 创建 ai_tool_categories 表
    op.create_table(
        'ai_tool_categories',
        sa.Column('id', mysql.CHAR(36), nullable=False),
        sa.Column('toolset_id', mysql.CHAR(36), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['toolset_id'], ['toolsets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4'
    )

    # 创建 ai_tools 表
    op.create_table(
        'ai_tools',
        sa.Column('id', mysql.CHAR(36), nullable=False),
        sa.Column('tool_id', sa.String(50), nullable=False),
        sa.Column('toolset_id', mysql.CHAR(36), nullable=False),
        sa.Column('category_id', mysql.CHAR(36), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('type', sa.Enum('normal', 'media', name='aitooltype'), nullable=False, server_default='normal'),
        sa.Column('content_type', sa.String(20), nullable=True),
        sa.Column('media_type', sa.String(20), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('welcome_message', sa.Text(), nullable=True),
        sa.Column('visible', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['toolset_id'], ['toolsets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['ai_tool_categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tool_id'),
        mysql_charset='utf8mb4'
    )
    op.create_index(op.f('ix_ai_tools_tool_id'), 'ai_tools', ['tool_id'])
    op.create_index(op.f('ix_ai_tools_visible'), 'ai_tools', ['visible'])
    op.create_index('idx_ai_tool_toolset_order', 'ai_tools', ['toolset_id', 'order'])
    op.create_index('idx_ai_tool_category_order', 'ai_tools', ['category_id', 'order'])


def downgrade():
    # MySQL 中 ENUM 类型随表一起删除，无需单独处理
    op.drop_table('ai_tools')
    op.drop_table('ai_tool_categories')
    op.drop_table('toolsets')
    op.drop_table('navigation_modules')
