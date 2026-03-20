"""add_model_and_tokens_to_sessions_messages

Revision ID: g2h3i4j5k6l7
Revises: f1g2h3i4j5k6
Create Date: 2026-03-20

为sessions和messages表添加模型选择和token记录功能，为后续积分计费做准备。
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = 'g2h3i4j5k6l7'
down_revision: Union[str, Sequence[str], None] = 'f1g2h3i4j5k6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加模型和token相关字段"""

    # ========== SessionModel 新增字段 ==========
    # AI服务提供商（deepseek/openai/kimi/glm）
    op.add_column('sessions', sa.Column(
        'model_provider',
        sa.String(50),
        nullable=True,
        comment='AI服务提供商（deepseek/openai/kimi/glm）'
    ))

    # 使用的模型名称（如deepseek-chat/gpt-4）
    op.add_column('sessions', sa.Column(
        'model_name',
        sa.String(100),
        nullable=True,
        comment='使用的模型名称（如deepseek-chat/gpt-4）'
    ))

    # 会话总token消耗
    op.add_column('sessions', sa.Column(
        'total_tokens',
        sa.Integer,
        nullable=False,
        server_default='0',
        comment='会话总token消耗'
    ))

    # 会话总prompt token消耗
    op.add_column('sessions', sa.Column(
        'total_prompt_tokens',
        sa.Integer,
        nullable=False,
        server_default='0',
        comment='会话总prompt token消耗'
    ))

    # 会话总completion token消耗
    op.add_column('sessions', sa.Column(
        'total_completion_tokens',
        sa.Integer,
        nullable=False,
        server_default='0',
        comment='会话总completion token消耗'
    ))

    # ========== MessageModel 新增字段 ==========
    # AI服务提供商
    op.add_column('messages', sa.Column(
        'model_provider',
        sa.String(50),
        nullable=True,
        comment='AI服务提供商'
    ))

    # 使用的模型名称
    op.add_column('messages', sa.Column(
        'model_name',
        sa.String(100),
        nullable=True,
        comment='使用的模型名称'
    ))

    # 用户消息的token消耗
    op.add_column('messages', sa.Column(
        'prompt_tokens',
        sa.Integer,
        nullable=True,
        comment='用户消息的token消耗'
    ))

    # AI回复的token消耗
    op.add_column('messages', sa.Column(
        'completion_tokens',
        sa.Integer,
        nullable=True,
        comment='AI回复的token消耗'
    ))

    # 本条消息的总token消耗
    op.add_column('messages', sa.Column(
        'total_tokens',
        sa.Integer,
        nullable=True,
        comment='本条消息的总token消耗'
    ))

    # ========== 创建 token_usage_logs 表 ==========
    # 用于详细记录每次API调用，便于计费和审计
    op.create_table(
        'token_usage_logs',
        sa.Column(
            'id',
            sa.CHAR(36),
            primary_key=True,
            default=lambda: str(uuid.uuid4())
        ),
        sa.Column(
            'user_id',
            sa.CHAR(36),
            sa.ForeignKey('users.user_id', ondelete='CASCADE'),
            nullable=False,
            comment='用户ID'
        ),
        sa.Column(
            'session_id',
            sa.CHAR(36),
            sa.ForeignKey('sessions.session_id', ondelete='CASCADE'),
            nullable=False,
            comment='会话ID'
        ),
        sa.Column(
            'message_id',
            sa.CHAR(36),
            sa.ForeignKey('messages.message_id', ondelete='CASCADE'),
            nullable=False,
            comment='消息ID'
        ),
        sa.Column(
            'model_provider',
            sa.String(50),
            nullable=False,
            comment='AI服务提供商'
        ),
        sa.Column(
            'model_name',
            sa.String(100),
            nullable=False,
            comment='模型名称'
        ),
        sa.Column(
            'prompt_tokens',
            sa.Integer,
            nullable=False,
            comment='Prompt token数'
        ),
        sa.Column(
            'completion_tokens',
            sa.Integer,
            nullable=False,
            comment='Completion token数'
        ),
        sa.Column(
            'total_tokens',
            sa.Integer,
            nullable=False,
            comment='总token数'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            comment='创建时间'
        ),
        comment='Token使用日志表，用于计费和审计'
    )

    # 创建索引以优化查询性能
    op.create_index(
        'idx_token_logs_user_date',
        'token_usage_logs',
        ['user_id', 'created_at']
    )
    op.create_index(
        'idx_token_logs_session',
        'token_usage_logs',
        ['session_id']
    )
    op.create_index(
        'idx_token_logs_message',
        'token_usage_logs',
        ['message_id']
    )
    op.create_index(
        'idx_token_logs_provider',
        'token_usage_logs',
        ['model_provider']
    )


def downgrade() -> None:
    """回滚所有变更"""

    # 删除 token_usage_logs 表及其索引
    op.drop_index('idx_token_logs_provider', table_name='token_usage_logs')
    op.drop_index('idx_token_logs_message', table_name='token_usage_logs')
    op.drop_index('idx_token_logs_session', table_name='token_usage_logs')
    op.drop_index('idx_token_logs_user_date', table_name='token_usage_logs')
    op.drop_table('token_usage_logs')

    # 删除 MessageModel 新增的字段
    op.drop_column('messages', 'total_tokens')
    op.drop_column('messages', 'completion_tokens')
    op.drop_column('messages', 'prompt_tokens')
    op.drop_column('messages', 'model_name')
    op.drop_column('messages', 'model_provider')

    # 删除 SessionModel 新增的字段
    op.drop_column('sessions', 'total_completion_tokens')
    op.drop_column('sessions', 'total_prompt_tokens')
    op.drop_column('sessions', 'total_tokens')
    op.drop_column('sessions', 'model_name')
    op.drop_column('sessions', 'model_provider')
