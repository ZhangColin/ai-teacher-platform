"""add_continue_config_to_model_configs

Revision ID: 0cfdaa6c9f5f
Revises: 1a251c6dcc0c
Create Date: 2026-04-04 00:06:45.958389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '0cfdaa6c9f5f'
down_revision: Union[str, Sequence[str], None] = '1a251c6dcc0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    bind = op.get_bind()
    result = bind.execute(text(
        f"SHOW COLUMNS FROM {table_name} LIKE '{column_name}'"
    ))
    return result.rowcount > 0


def upgrade() -> None:
    """Upgrade schema."""

    # 检查并添加 context_window 列
    if not _column_exists('model_configs', 'context_window'):
        op.add_column('model_configs', sa.Column('context_window', sa.Integer(), nullable=True))
        print("✅ 已添加 context_window 列")
    else:
        print("ℹ️  context_window 列已存在，跳过添加")

    # 检查并添加 max_output_tokens 列
    if not _column_exists('model_configs', 'max_output_tokens'):
        op.add_column('model_configs', sa.Column('max_output_tokens', sa.Integer(), nullable=True))
        print("✅ 已添加 max_output_tokens 列")
    else:
        print("ℹ️  max_output_tokens 列已存在，跳过添加")

    # 检查并添加 continue_window_size 列
    if not _column_exists('model_configs', 'continue_window_size'):
        op.add_column('model_configs', sa.Column('continue_window_size', sa.Integer(), nullable=True))
        print("✅ 已添加 continue_window_size 列")
    else:
        print("ℹ️  continue_window_size 列已存在，跳过添加")

    # 设置默认值（幂等性：使用 WHERE IS NULL）
    bind = op.get_bind()
    bind.execute(text("UPDATE model_configs SET context_window = 8000 WHERE context_window IS NULL"))
    bind.execute(text("UPDATE model_configs SET max_output_tokens = 4000 WHERE max_output_tokens IS NULL"))
    bind.execute(text("UPDATE model_configs SET continue_window_size = 2000 WHERE continue_window_size IS NULL"))
    print("✅ 已设置通用默认值")

    # 为不同模型设置合理的默认值（幂等性：每次覆盖）
    # DeepSeek
    bind.execute(text("UPDATE model_configs SET context_window = 16000, max_output_tokens = 4000, continue_window_size = 2000 WHERE model_code LIKE 'deepseek%'"))
    # Kimi
    bind.execute(text("UPDATE model_configs SET context_window = 32000, max_output_tokens = 4000, continue_window_size = 3000 WHERE model_code LIKE 'moonshot%' OR model_code LIKE 'kimi%'"))
    # OpenAI
    bind.execute(text("UPDATE model_configs SET context_window = 8192, max_output_tokens = 4096, continue_window_size = 2000 WHERE model_code LIKE 'gpt-%'"))
    # Claude
    bind.execute(text("UPDATE model_configs SET context_window = 200000, max_output_tokens = 4000, continue_window_size = 5000 WHERE model_code LIKE 'claude%'"))
    # GLM
    bind.execute(text("UPDATE model_configs SET context_window = 128000, max_output_tokens = 4000, continue_window_size = 3000 WHERE model_code LIKE 'glm%'"))
    # Gemini
    bind.execute(text("UPDATE model_configs SET context_window = 1000000, max_output_tokens = 4000, continue_window_size = 3000 WHERE model_code LIKE 'gemini%'"))
    print("✅ 已为特定模型设置默认值")

    # 修改为 NOT NULL（检查是否已经是 NOT NULL）
    # 获取列信息
    result = bind.execute(text("SHOW COLUMNS FROM model_configs LIKE 'context_window'"))
    context_window_row = result.fetchone()
    if context_window_row and context_window_row[2] == 'YES':  # Null 列
        op.alter_column('model_configs', 'context_window',
                       existing_type=sa.Integer(),
                       nullable=False)
        print("✅ 已将 context_window 设置为 NOT NULL")
    else:
        print("ℹ️  context_window 已经是 NOT NULL，跳过修改")

    result = bind.execute(text("SHOW COLUMNS FROM model_configs LIKE 'max_output_tokens'"))
    max_output_tokens_row = result.fetchone()
    if max_output_tokens_row and max_output_tokens_row[2] == 'YES':
        op.alter_column('model_configs', 'max_output_tokens',
                       existing_type=sa.Integer(),
                       nullable=False)
        print("✅ 已将 max_output_tokens 设置为 NOT NULL")
    else:
        print("ℹ️  max_output_tokens 已经是 NOT NULL，跳过修改")

    result = bind.execute(text("SHOW COLUMNS FROM model_configs LIKE 'continue_window_size'"))
    continue_window_size_row = result.fetchone()
    if continue_window_size_row and continue_window_size_row[2] == 'YES':
        op.alter_column('model_configs', 'continue_window_size',
                       existing_type=sa.Integer(),
                       nullable=False)
        print("✅ 已将 continue_window_size 设置为 NOT NULL")
    else:
        print("ℹ️  continue_window_size 已经是 NOT NULL，跳过修改")


def downgrade() -> None:
    """Downgrade schema."""
    # 先修改为 nullable（检查当前状态）
    bind = op.get_bind()

    result = bind.execute(text("SHOW COLUMNS FROM model_configs LIKE 'continue_window_size'"))
    if result.fetchone() and result.fetchone()[2] == 'NO':
        op.alter_column('model_configs', 'continue_window_size',
                       existing_type=sa.Integer(),
                       nullable=True)

    result = bind.execute(text("SHOW COLUMNS FROM model_configs LIKE 'max_output_tokens'"))
    if result.fetchone() and result.fetchone()[2] == 'NO':
        op.alter_column('model_configs', 'max_output_tokens',
                       existing_type=sa.Integer(),
                       nullable=True)

    result = bind.execute(text("SHOW COLUMNS FROM model_configs LIKE 'context_window'"))
    if result.fetchone() and result.fetchone()[2] == 'NO':
        op.alter_column('model_configs', 'context_window',
                       existing_type=sa.Integer(),
                       nullable=True)

    # 删除列（检查是否存在）
    if _column_exists('model_configs', 'continue_window_size'):
        op.drop_column('model_configs', 'continue_window_size')

    if _column_exists('model_configs', 'max_output_tokens'):
        op.drop_column('model_configs', 'max_output_tokens')

    if _column_exists('model_configs', 'context_window'):
        op.drop_column('model_configs', 'context_window')
