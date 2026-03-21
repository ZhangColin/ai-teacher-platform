"""merge_toolsets_to_navigation_modules

Revision ID: 7ef319414486
Revises: 705c676a8b9f
Create Date: 2026-03-21 13:03:21.762652

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, select


# revision identifiers, used by Alembic.
revision: str = '7ef319414486'
down_revision: Union[str, Sequence[str], None] = '705c676a8b9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """迁移：合并 toolsets 到 navigation_modules"""

    # 1. 给 ai_tool_categories 添加 navigation_module_id 列
    op.add_column(
        'ai_tool_categories',
        sa.Column('navigation_module_id', sa.CHAR(36), nullable=True)
    )

    # 2. 给 ai_tools 添加 navigation_module_id 列
    op.add_column(
        'ai_tools',
        sa.Column('navigation_module_id', sa.CHAR(36), nullable=True)
    )

    # 3. 创建外键约束
    op.create_foreign_key(
        'fk_ai_tool_categories_nav_module',
        'ai_tool_categories', 'navigation_modules',
        ['navigation_module_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_ai_tools_nav_module',
        'ai_tools', 'navigation_modules',
        ['navigation_module_id'], ['id'],
        ondelete='CASCADE'
    )

    # 4. 数据迁移：建立 toolset_id 到 navigation_module_id 的映射
    connection = op.get_bind()

    # 获取所有 type='toolset' 的导航模块
    nav_modules = connection.execute(
        sa.text("""
            SELECT id, config_source
            FROM navigation_modules
            WHERE type = 'toolset'
        """)
    ).fetchall()

    # 构建映射
    toolset_to_nav_map = {}
    for nav_id, config_source in nav_modules:
        if config_source:
            # 从 "tools/ai_tools" 提取 "ai_tools"
            toolset_id = config_source.strip().split("/")[-1]
            # 查找对应的 toolset 记录
            toolset = connection.execute(
                sa.text("""
                    SELECT id FROM toolsets WHERE toolset_id = :toolset_id
                """),
                {"toolset_id": toolset_id}
            ).fetchone()
            if toolset:
                toolset_to_nav_map[str(toolset[0])] = str(nav_id)

    # 更新 ai_tool_categories
    for toolset_id, nav_id in toolset_to_nav_map.items():
        connection.execute(
            sa.text("""
                UPDATE ai_tool_categories
                SET navigation_module_id = :nav_id
                WHERE toolset_id = :toolset_id
            """),
            {"nav_id": nav_id, "toolset_id": toolset_id}
        )

    # 更新 ai_tools
    for toolset_id, nav_id in toolset_to_nav_map.items():
        connection.execute(
            sa.text("""
                UPDATE ai_tools
                SET navigation_module_id = :nav_id
                WHERE toolset_id = :toolset_id
            """),
            {"nav_id": nav_id, "toolset_id": toolset_id}
        )

    # 5. 将 navigation_module_id 设为非空
    op.alter_column(
        'ai_tool_categories',
        'navigation_module_id',
        nullable=False
    )
    op.alter_column(
        'ai_tools',
        'navigation_module_id',
        nullable=False
    )

    # 6. 删除旧的外键和列
    # ai_tool_categories
    op.drop_constraint('fk_ai_tool_categories_toolset', 'ai_tool_categories', type_='foreignkey')
    op.drop_column('ai_tool_categories', 'toolset_id')

    # ai_tools
    op.drop_constraint('fk_ai_tools_toolset', 'ai_tools', type_='foreignkey')
    op.drop_column('ai_tools', 'toolset_id')

    # 7. 删除 toolsets 表
    op.drop_table('toolsets')

    # 8. 更新 navigation_modules 表的枚举类型
    # MySQL 中需要修改 ENUM 定义
    op.execute("""
        ALTER TABLE navigation_modules
        MODIFY COLUMN type ENUM('ai_tools', 'page') NOT NULL
    """)

    # 9. 更新现有数据的 type 值
    op.execute("""
        UPDATE navigation_modules
        SET type = 'ai_tools'
        WHERE type = 'toolset'
    """)

    # 10. 更新索引名称
    op.drop_index('idx_ai_tool_toolset_order', table_name='ai_tools')
    op.create_index(
        'idx_ai_tool_navigation_module_order',
        'ai_tools',
        ['navigation_module_id', 'order']
    )


def downgrade() -> None:
    """回滚：恢复 toolsets 表"""

    # 1. 恢复 navigation_modules 的枚举
    op.execute("""
        ALTER TABLE navigation_modules
        MODIFY COLUMN type ENUM('toolset', 'page') NOT NULL
    """)

    op.execute("""
        UPDATE navigation_modules
        SET type = 'toolset'
        WHERE type = 'ai_tools'
    """)

    # 2. 恢复 toolsets 表
    op.create_table(
        'toolsets',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('toolset_id', sa.String(50), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('icon', sa.String(50)),
        sa.Column('order', sa.Integer, nullable=False, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=sa.func.now()),
        mysql_charset='utf8mb4'
    )

    # 3. 恢复 ai_tool_categories 的 toolset_id 列
    op.add_column(
        'ai_tool_categories',
        sa.Column('toolset_id', sa.CHAR(36), nullable=True)
    )

    # 4. 恢复 ai_tools 的 toolset_id 列
    op.add_column(
        'ai_tools',
        sa.Column('toolset_id', sa.CHAR(36), nullable=True)
    )

    # 5. 数据回迁（简化版，实际需要更复杂的映射）
    connection = op.get_bind()
    connection.execute("""
        UPDATE ai_tool_categories
        SET toolset_id = navigation_module_id
    """)
    connection.execute("""
        UPDATE ai_tools
        SET toolset_id = navigation_module_id
    """)

    # 6. 恢复外键
    op.create_foreign_key(
        'fk_ai_tool_categories_toolset',
        'ai_tool_categories', 'toolsets',
        ['toolset_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_ai_tools_toolset',
        'ai_tools', 'toolsets',
        ['toolset_id'], ['id'],
        ondelete='CASCADE'
    )

    # 7. 删除 navigation_module_id 相关
    op.drop_constraint('fk_ai_tool_categories_nav_module', 'ai_tool_categories', type_='foreignkey')
    op.drop_constraint('fk_ai_tools_nav_module', 'ai_tools', type_='foreignkey')
    op.drop_column('ai_tool_categories', 'navigation_module_id')
    op.drop_column('ai_tools', 'navigation_module_id')

    # 8. 恢复索引
    op.drop_index('idx_ai_tool_navigation_module_order', table_name='ai_tools')
    op.create_index(
        'idx_ai_tool_toolset_order',
        'ai_tools',
        ['toolset_id', 'order']
    )
