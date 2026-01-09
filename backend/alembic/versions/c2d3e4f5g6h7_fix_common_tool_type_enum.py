"""fix_common_tool_type_enum

Revision ID: c2d3e4f5g6h7
Revises: b1c2d3e4f5g6
Create Date: 2026-01-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5g6h7'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3e4f5g6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    修复 common_tools.type 枚举类型
    将 'built-in' 改为 'built_in' 以匹配 Python 枚举
    """
    # MySQL 修改 ENUM 的方式：
    # 1. 先修改列的 ENUM 定义，添加新值
    # 2. 更新数据
    # 3. 再次修改列，移除旧值
    
    # 步骤1: 修改 ENUM，同时包含新旧两个值
    op.execute("""
        ALTER TABLE common_tools 
        MODIFY COLUMN type ENUM('built-in', 'built_in', 'html') NOT NULL
    """)
    
    # 步骤2: 更新数据，将 'built-in' 改为 'built_in'
    op.execute("""
        UPDATE common_tools 
        SET type = 'built_in' 
        WHERE type = 'built-in'
    """)
    
    # 步骤3: 修改 ENUM，只保留新值
    op.execute("""
        ALTER TABLE common_tools 
        MODIFY COLUMN type ENUM('built_in', 'html') NOT NULL
    """)


def downgrade() -> None:
    """
    回滚：将 'built_in' 改回 'built-in'
    """
    # 步骤1: 修改 ENUM，同时包含新旧两个值
    op.execute("""
        ALTER TABLE common_tools 
        MODIFY COLUMN type ENUM('built-in', 'built_in', 'html') NOT NULL
    """)
    
    # 步骤2: 更新数据，将 'built_in' 改回 'built-in'
    op.execute("""
        UPDATE common_tools 
        SET type = 'built-in' 
        WHERE type = 'built_in'
    """)
    
    # 步骤3: 修改 ENUM，只保留旧值
    op.execute("""
        ALTER TABLE common_tools 
        MODIFY COLUMN type ENUM('built-in', 'html') NOT NULL
    """)
