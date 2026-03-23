"""add_model_providers

Revision ID: 4a83ebad1439
Revises: 08138ce1d286
Create Date: 2026-03-20 23:57:19.652255

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a83ebad1439'
# 跳过 08138ce1d286（有问题的迁移），直接从 e76e4604e3f4 继续
down_revision: Union[str, Sequence[str], None] = 'e76e4604e3f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 创建 model_providers 表
    op.create_table(
        'model_providers',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('provider_code', sa.String(50), nullable=False, unique=True, comment='供应商代码（内置）'),
        sa.Column('provider_name', sa.String(100), nullable=False, comment='供应商名称'),
        sa.Column('api_key_encrypted', sa.Text(), nullable=False, comment='加密后的API密钥'),
        sa.Column('base_url', sa.String(500), nullable=True, comment='API地址'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True, comment='是否启用'),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False, comment='是否为默认供应商'),
        sa.Column('order', sa.Integer(), nullable=False, default=0, comment='排序顺序'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Index('idx_provider_code', 'provider_code'),
        sa.Index('idx_order', 'order')
    )

    # 创建 model_configs 表
    op.create_table(
        'model_configs',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('provider_id', sa.CHAR(36), nullable=False, comment='关联供应商'),
        sa.Column('model_code', sa.String(50), nullable=False, comment='模型代码（内置）'),
        sa.Column('model_name', sa.String(100), nullable=False, comment='模型名称'),
        sa.Column('capabilities', sa.String(50), nullable=False, comment='支持的能力，逗号分隔'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True, comment='是否启用'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['provider_id'], ['model_providers.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('provider_id', 'model_code', name='uk_provider_model'),
        sa.Index('idx_capabilities', 'capabilities')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('model_configs')
    op.drop_table('model_providers')
