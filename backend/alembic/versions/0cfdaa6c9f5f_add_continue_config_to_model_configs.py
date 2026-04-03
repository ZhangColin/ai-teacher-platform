"""add_continue_config_to_model_configs

Revision ID: 0cfdaa6c9f5f
Revises: 1a251c6dcc0c
Create Date: 2026-04-04 00:06:45.958389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0cfdaa6c9f5f'
down_revision: Union[str, Sequence[str], None] = '1a251c6dcc0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加新字段
    op.add_column('model_configs', sa.Column('context_window', sa.Integer(), nullable=True))
    op.add_column('model_configs', sa.Column('max_output_tokens', sa.Integer(), nullable=True))
    op.add_column('model_configs', sa.Column('continue_window_size', sa.Integer(), nullable=True))

    # 设置默认值
    op.execute("UPDATE model_configs SET context_window = 8000 WHERE context_window IS NULL")
    op.execute("UPDATE model_configs SET max_output_tokens = 4000 WHERE max_output_tokens IS NULL")
    op.execute("UPDATE model_configs SET continue_window_size = 2000 WHERE continue_window_size IS NULL")

    # 为不同模型设置合理的默认值
    # DeepSeek
    op.execute("UPDATE model_configs SET context_window = 16000, max_output_tokens = 4000, continue_window_size = 2000 WHERE model_code LIKE 'deepseek%'")
    # Kimi
    op.execute("UPDATE model_configs SET context_window = 32000, max_output_tokens = 4000, continue_window_size = 3000 WHERE model_code LIKE 'moonshot%' OR model_code LIKE 'kimi%'")
    # OpenAI
    op.execute("UPDATE model_configs SET context_window = 8192, max_output_tokens = 4096, continue_window_size = 2000 WHERE model_code LIKE 'gpt-%'")
    # Claude
    op.execute("UPDATE model_configs SET context_window = 200000, max_output_tokens = 4000, continue_window_size = 5000 WHERE model_code LIKE 'claude%'")
    # GLM
    op.execute("UPDATE model_configs SET context_window = 128000, max_output_tokens = 4000, continue_window_size = 3000 WHERE model_code LIKE 'glm%'")
    # Gemini
    op.execute("UPDATE model_configs SET context_window = 1000000, max_output_tokens = 4000, continue_window_size = 3000 WHERE model_code LIKE 'gemini%'")

    # 修改为 NOT NULL
    op.alter_column('model_configs', 'context_window', nullable=False)
    op.alter_column('model_configs', 'max_output_tokens', nullable=False)
    op.alter_column('model_configs', 'continue_window_size', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('model_configs', 'continue_window_size', nullable=True)
    op.alter_column('model_configs', 'max_output_tokens', nullable=True)
    op.alter_column('model_configs', 'context_window', nullable=True)

    op.drop_column('model_configs', 'continue_window_size')
    op.drop_column('model_configs', 'max_output_tokens')
    op.drop_column('model_configs', 'context_window')
