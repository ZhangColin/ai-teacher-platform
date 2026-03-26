"""add_required_capability_to_ai_tools

Revision ID: 3ae5f8556ec4
Revises: 20260325_add_newapi
Create Date: 2026-03-26 13:40:19.752706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ae5f8556ec4'
down_revision: Union[str, Sequence[str], None] = '20260325_add_newapi'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加 required_capability 字段到 ai_tools 表
    op.add_column('ai_tools', sa.Column('required_capability', sa.String(50), nullable=True, comment='所需的 AI 能力（如 chat, image, audio, video, code）'))

    # 根据现有数据自动填充 required_capability
    from sqlalchemy.orm import Session
    session = Session(op.get_bind())

    # 获取所有工具
    result = session.execute(sa.text("SELECT id, tool_id, content_type, media_type FROM ai_tools"))

    for row in result:
        tool_id, tool_name, content_type, media_type = row[0], row[1], row[2], row[3]
        required_capability = None

        # 根据 content_type 和 media_type 推导能力
        if content_type == 'multimodal':
            if media_type == 'image':
                required_capability = 'image'
            elif media_type == 'audio':
                required_capability = 'audio'
            elif media_type == 'video':
                required_capability = 'video'
        else:
            # 默认使用 chat 能力
            required_capability = 'chat'

        # 更新数据库
        session.execute(
            sa.text("UPDATE ai_tools SET required_capability = :capability WHERE id = :id"),
            {"capability": required_capability, "id": tool_id}
        )

    session.commit()


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('ai_tools', 'required_capability')
