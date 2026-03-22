"""添加 AWS Bedrock 供应商和 Claude 模型

Revision ID: c80318561d4a
Revises: 7ef319414486
Create Date: 2026-03-22 16:07:06.273679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import uuid

# revision identifiers, used by Alembic.
revision: str = 'c80318561d4a'
down_revision: Union[str, Sequence[str], None] = '7ef319414486'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # 添加索引
    op.create_index(op.f('ix_ai_tool_categories_navigation_module_id'), 'ai_tool_categories', ['navigation_module_id'], unique=False)
    op.create_index(op.f('ix_ai_tools_navigation_module_id'), 'ai_tools', ['navigation_module_id'], unique=False)

    # 修改列注释
    op.alter_column('model_configs', 'provider_id',
               existing_type=mysql.CHAR(collation='utf8mb4_unicode_ci', length=36),
               comment=None,
               existing_comment='关联供应商',
               existing_nullable=False)
    op.alter_column('model_configs', 'model_code',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=50),
               comment='模型代码',
               existing_comment='模型代码（内置）',
               existing_nullable=False)

    # 重建索引
    op.drop_index('idx_capabilities', table_name='model_configs')
    op.create_index(op.f('ix_model_configs_provider_id'), 'model_configs', ['provider_id'], unique=False)

    op.alter_column('model_providers', 'provider_code',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=50),
               comment='供应商代码',
               existing_comment='供应商代码（内置）',
               existing_nullable=False)
    op.alter_column('model_providers', 'order',
               existing_type=mysql.INTEGER(),
               comment='排序',
               existing_comment='排序顺序',
               existing_nullable=False)

    op.drop_index('idx_order', table_name='model_providers')
    op.drop_index('idx_provider_code', table_name='model_providers')
    op.drop_index('provider_code', table_name='model_providers')
    op.create_index(op.f('ix_model_providers_order'), 'model_providers', ['order'], unique=False)
    op.create_index(op.f('ix_model_providers_provider_code'), 'model_providers', ['provider_code'], unique=True)

    # 添加 AWS Bedrock 供应商和模型
    bedrock_provider_id = str(uuid.uuid4())

    # 获取当前最大 order 值
    result = conn.execute(sa.text("SELECT MAX(`order`) FROM model_providers"))
    max_order = result.scalar() or 0

    # 插入 Bedrock 供应商
    conn.execute(sa.text("""
        INSERT INTO model_providers (id, provider_code, provider_name, api_key_encrypted, base_url, is_enabled, is_default, `order`)
        VALUES (:id, :provider_code, :provider_name, :api_key_encrypted, :base_url, :is_enabled, :is_default, :order)
    """), {
        'id': bedrock_provider_id,
        'provider_code': 'bedrock',
        'provider_name': 'AWS Bedrock (Claude)',
        'api_key_encrypted': '',
        'base_url': 'us-west-2',
        'is_enabled': True,
        'is_default': False,
        'order': max_order + 1,
    })

    # 插入 Bedrock Claude 模型
    models = [
        ('us.anthropic.claude-opus-4-6-v1:0', 'Claude Opus 4.6 (us-west-2)', 'chat,image,code'),
        ('anthropic.claude-opus-4-6-v1', 'Claude Opus 4.6 (Global)', 'chat,image,code'),
        ('us.anthropic.claude-sonnet-4-6', 'Claude Sonnet 4.6 (us-west-2)', 'chat,image,code'),
        ('anthropic.claude-sonnet-4-6', 'Claude Sonnet 4.6 (Global)', 'chat,image,code'),
        ('us.anthropic.claude-sonnet-4-5-20250929-v1:0', 'Claude Sonnet 4.5 (us-west-2)', 'chat,image,code'),
        ('anthropic.claude-sonnet-4-5-20250929-v1:0', 'Claude Sonnet 4.5 (Global)', 'chat,image,code'),
        ('us.anthropic.claude-haiku-4-5-20251001-v1:0', 'Claude Haiku 4.5 (us-west-2)', 'chat'),
        ('anthropic.claude-haiku-4-5-20251001-v1:0', 'Claude Haiku 4.5 (Global)', 'chat'),
        ('us.anthropic.claude-3-5-haiku-20241022-v1:0', 'Claude 3.5 Haiku (us-west-2)', 'chat'),
    ]

    for model_code, model_name, capabilities in models:
        model_id = str(uuid.uuid4())
        conn.execute(sa.text("""
            INSERT INTO model_configs (id, provider_id, model_code, model_name, capabilities, is_enabled)
            VALUES (:id, :provider_id, :model_code, :model_name, :capabilities, :is_enabled)
        """), {
            'id': model_id,
            'provider_id': bedrock_provider_id,
            'model_code': model_code,
            'model_name': model_name,
            'capabilities': capabilities,
            'is_enabled': True,
        })


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()

    # 删除插入的数据
    conn.execute(sa.text("DELETE FROM model_configs WHERE provider_id = (SELECT id FROM model_providers WHERE provider_code = 'bedrock')"))
    conn.execute(sa.text("DELETE FROM model_providers WHERE provider_code = 'bedrock'"))

    # 恢复索引和列
    op.drop_index(op.f('ix_model_providers_provider_code'), table_name='model_providers')
    op.drop_index(op.f('ix_model_providers_order'), table_name='model_providers')
    op.create_index('provider_code', 'model_providers', ['provider_code'], unique=True)
    op.create_index('idx_provider_code', 'model_providers', ['provider_code'], unique=False)
    op.create_index('idx_order', 'model_providers', ['order'], unique=False)

    op.alter_column('model_providers', 'order',
               existing_type=mysql.INTEGER(),
               comment='排序顺序',
               existing_comment='排序',
               existing_nullable=False)
    op.alter_column('model_providers', 'provider_code',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=50),
               comment='供应商代码（内置）',
               existing_comment='供应商代码',
               existing_nullable=False)

    op.drop_index(op.f('ix_model_configs_provider_id'), 'model_configs')
    op.create_index('idx_capabilities', 'model_configs', ['capabilities'], unique=False)

    op.alter_column('model_configs', 'model_code',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=50),
               comment='模型代码（内置）',
               existing_comment='模型代码',
               existing_nullable=False)
    op.alter_column('model_configs', 'provider_id',
               existing_type=mysql.CHAR(collation='utf8mb4_unicode_ci', length=36),
               comment='关联供应商',
               existing_nullable=False)

    op.drop_index(op.f('ix_ai_tools_navigation_module_id'), table_name='ai_tools')
    op.drop_index(op.f('ix_ai_tool_categories_navigation_module_id'), table_name='ai_tool_categories')
