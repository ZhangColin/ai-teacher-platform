# 配置文件数据库化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-step. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标:** 将系统中的 YAML 配置文件迁移到数据库存储，并提供后台管理页面进行维护。

**架构:**
1. 新增 4 张数据库表存储配置（导航模块、工具集、工具分类、AI工具）
2. 修改服务层从数据库读取配置（而非 YAML），保持现有 API 不变
3. 新增后台管理 API（/api/v1/admin/...）和前端管理页面

**技术栈:**
- 后端: FastAPI, SQLAlchemy, Alembic, Pydantic
- 前端: Vue 3, TypeScript, CodeMirror 6, Heroicons
- 数据库: MySQL

---

## Phase 1: 数据库层

### Task 1.1: 创建数据库模型

**文件:**
- Modify: `backend/src/db_models.py` (在文件末尾添加新模型)

- [ ] **Step 1: 添加 NavigationModuleType 枚举**

在 `db_models.py` 的 `import enum` 部分后添加：

```python
class NavigationModuleType(enum.Enum):
    """导航模块类型枚举"""
    toolset = "toolset"
    page = "page"


class AIToolType(enum.Enum):
    """AI工具类型枚举"""
    normal = "normal"
    media = "media"
```

- [ ] **Step 2: 添加 NavigationModuleModel 类**

在 `TokenUsageLogModel` 类之后添加：

```python
class NavigationModuleModel(Base):
    """导航模块数据库模型"""
    __tablename__ = "navigation_modules"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False)
    type = Column(Enum(NavigationModuleType), nullable=False)
    config_source = Column(String(100), nullable=True)
    page_path = Column(String(100), nullable=True)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 联合索引
    __table_args__ = (
        Index("idx_navigation_module_order", "order"),
    )
```

- [ ] **Step 3: 添加 ToolsetModel 类**

```python
class ToolsetModel(Base):
    """工具集数据库模型"""
    __tablename__ = "toolsets"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    toolset_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    categories = relationship("AIToolCategoryModel", back_populates="toolset", cascade="all, delete-orphan")
    tools = relationship("AIToolModel", back_populates="toolset", cascade="all, delete-orphan")
```

- [ ] **Step 4: 添加 AIToolCategoryModel 类**

```python
class AIToolCategoryModel(Base):
    """AI工具分类数据库模型"""
    __tablename__ = "ai_tool_categories"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    toolset_id = Column(CHAR(36), ForeignKey("toolsets.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    toolset = relationship("ToolsetModel", back_populates="categories")
    tools = relationship("AIToolModel", back_populates="category", cascade="all, delete-orphan")
```

- [ ] **Step 5: 添加 AIToolModel 类**

```python
class AIToolModel(Base):
    """AI工具数据库模型"""
    __tablename__ = "ai_tools"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String(50), unique=True, nullable=False, index=True)
    toolset_id = Column(CHAR(36), ForeignKey("toolsets.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(CHAR(36), ForeignKey("ai_tool_categories.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    type = Column(Enum(AIToolType), nullable=False, default=AIToolType.normal)
    content_type = Column(String(20), nullable=True)
    media_type = Column(String(20), nullable=True)
    model = Column(String(100), nullable=True)
    welcome_message = Column(Text, nullable=True)
    visible = Column(Boolean, nullable=False, default=True, index=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    toolset = relationship("ToolsetModel", back_populates="tools")
    category = relationship("AIToolCategoryModel", back_populates="tools")

    # 联合索引
    __table_args__ = (
        Index("idx_ai_tool_toolset_order", "toolset_id", "order"),
        Index("idx_ai_tool_category_order", "category_id", "order"),
    )
```

- [ ] **Step 6: 提交变更**

```bash
git add backend/src/db_models.py
git commit -m "feat: 添加AI工具配置数据库模型

- 添加 NavigationModuleModel 导航模块模型
- 添加 ToolsetModel 工具集模型
- 添加 AIToolCategoryModel 工具分类模型
- 添加 AIToolModel AI工具模型"
```

---

### Task 1.2: 创建 Alembic 迁移

**文件:**
- Create: `backend/alembic/versions/[timestamp]_add_ai_tool_config_tables.py`

- [ ] **Step 1: 生成迁移文件**

```bash
cd backend
alembic revision -m "add ai tool config tables"
```

- [ ] **Step 2: 编辑生成的迁移文件**

打开最新生成的迁移文件，将 `upgrade()` 和 `downgrade()` 函数替换为：

```python
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'xxxx'  # 保留生成的值
down_revision = 'yyyy'  # 保留生成的值
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
    op.drop_table('ai_tools')
    op.drop_table('ai_tool_categories')
    op.drop_table('toolsets')
    op.drop_table('navigation_modules')
    op.execute('DROP TYPE IF EXISTS navigationmoduletype')
    op.execute('DROP TYPE IF EXISTS aitooltype')
```

- [ ] **Step 3: 运行迁移**

```bash
cd backend
alembic upgrade head
```

预期输出: `Running upgrade -> [revision_id], add ai tool config tables`

- [ ] **Step 4: 验证表创建**

```bash
mysql -u root -p ai_teacher_platform -e "SHOW TABLES LIKE '%ai_%'; SHOW TABLES LIKE 'navigation%'; SHOW TABLES LIKE 'toolsets';"
```

预期输出: 应该看到 4 个新表

- [ ] **Step 5: 提交变更**

```bash
git add backend/alembic/versions/
git commit -m "feat: 添加AI工具配置表的数据库迁移"
```

---

## Phase 2: 数据迁移脚本

### Task 2.1: 创建 YAML 到数据库迁移脚本

**文件:**
- Create: `backend/scripts/migrate_yaml_to_db.py`

- [ ] **Step 1: 创建迁移脚本**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML 配置迁移到数据库脚本

将 configs/ 目录下的 YAML 配置文件迁移到数据库
"""
import sys
import yaml
import uuid
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from src.database import engine
from src.db_models import (
    NavigationModuleModel, NavigationModuleType,
    ToolsetModel, AIToolCategoryModel, AIToolModel, AIToolType
)


def load_yaml(file_path: Path) -> dict:
    """加载 YAML 文件"""
    if not file_path.exists():
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def migrate_navigation(db: Session):
    """迁移导航模块配置"""
    print("迁移导航模块...")
    nav_file = project_root / "configs" / "navigation.yaml"
    nav_data = load_yaml(nav_file)

    if not nav_data or 'modules' not in nav_data:
        print("  警告: navigation.yaml 不存在或格式错误")
        return

    for module_data in nav_data['modules']:
        module_type = NavigationModuleType.toolset if module_data.get('type') == 'toolset' else NavigationModuleType.page

        module = NavigationModuleModel(
            id=str(uuid.uuid4()),
            name=module_data.get('name', ''),
            type=module_type,
            config_source=module_data.get('config_source'),
            page_path=module_data.get('page_path'),
            icon=module_data.get('icon'),
            order=module_data.get('order', 0),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(module)

    db.commit()
    print(f"  迁移了 {len(nav_data['modules'])} 个导航模块")


def migrate_toolsets(db: Session):
    """迁移工具集配置"""
    print("迁移工具集...")
    tools_dir = project_root / "configs" / "tools"

    if not tools_dir.exists():
        print("  警告: tools 目录不存在")
        return {}

    toolset_map = {}  # toolset_id -> model id

    for toolset_dir in tools_dir.iterdir():
        if not toolset_dir.is_dir():
            continue

        toolset_id = toolset_dir.name

        # 检查是否有工具配置文件
        yaml_files = list(toolset_dir.glob("*.yaml"))
        if not yaml_files:
            continue

        # 从导航配置获取名称，或使用默认值
        name_map = {
            'ai_tools': 'AI模型能力',
            'teaching_researcher': 'AI教研员智能体',
            'test_tools': '测试工具集'
        }
        name = name_map.get(toolset_id, toolset_id)

        toolset = ToolsetModel(
            id=str(uuid.uuid4()),
            toolset_id=toolset_id,
            name=name,
            icon=None,
            order=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(toolset)
        db.flush()  # 获取生成的 ID

        toolset_map[toolset_id] = toolset.id
        print(f"  迁移工具集: {toolset_id}")

    db.commit()
    return toolset_map


def migrate_categories(db: Session, toolset_map: dict):
    """迁移工具分类配置"""
    print("迁移工具分类...")
    tools_dir = project_root / "configs" / "tools"

    category_map = {}  # (toolset_id, category_name) -> model id

    for toolset_id, toolset_db_id in toolset_map.items():
        categories_file = tools_dir / toolset_id / "categories.yaml"
        categories_data = load_yaml(categories_file)

        if not categories_data or 'categories' not in categories_data:
            continue

        for cat_data in categories_data['categories']:
            category = AIToolCategoryModel(
                id=str(uuid.uuid4()),
                toolset_id=toolset_db_id,
                name=cat_data.get('name', ''),
                icon=cat_data.get('icon'),
                order=cat_data.get('order', 0),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(category)
            db.flush()

            category_map[(toolset_id, cat_data.get('name', ''))] = category.id

    db.commit()
    print(f"  迁移了 {len(category_map)} 个分类")
    return category_map


def migrate_tools(db: Session, toolset_map: dict, category_map: dict):
    """迁移 AI 工具配置"""
    print("迁移 AI 工具...")
    tools_dir = project_root / "configs" / "tools"

    tool_count = 0

    for toolset_id, toolset_db_id in toolset_map.items():
        toolset_dir = tools_dir / toolset_id

        for yaml_file in toolset_dir.glob("*.yaml"):
            if yaml_file.name == 'categories.yaml':
                continue

            tool_data = load_yaml(yaml_file)
            if not tool_data:
                continue

            # 获取分类 ID
            category_name = tool_data.get('category')
            category_id = category_map.get((toolset_id, category_name))

            # 处理系统提示词
            system_prompt = tool_data.get('system_prompt')
            system_prompt_file = tool_data.get('system_prompt_file')

            if system_prompt_file:
                prompt_file = toolset_dir / "prompts" / system_prompt_file
                if prompt_file.exists():
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        system_prompt = f.read()

            # 确定工具类型
            tool_type = AIToolType.media if tool_data.get('type') == 'media' else AIToolType.normal

            tool = AIToolModel(
                id=str(uuid.uuid4()),
                tool_id=tool_data.get('tool_id'),
                toolset_id=toolset_db_id,
                category_id=category_id,
                name=tool_data.get('name'),
                description=tool_data.get('description'),
                system_prompt=system_prompt,
                icon=tool_data.get('icon'),
                type=tool_type,
                content_type=tool_data.get('content_type'),
                media_type=tool_data.get('media_type'),
                model=tool_data.get('model'),
                welcome_message=tool_data.get('welcome_message'),
                visible=tool_data.get('visible', True),
                order=tool_data.get('order', 0),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(tool)
            tool_count += 1

    db.commit()
    print(f"  迁移了 {tool_count} 个 AI 工具")


def main():
    """主函数"""
    print("=" * 50)
    print("开始 YAML 配置迁移")
    print("=" * 50)

    # 创建数据库会话
    with Session(engine) as db:
        # 清空现有数据（可选）
        # db.query(AIToolModel).delete()
        # db.query(AIToolCategoryModel).delete()
        # db.query(ToolsetModel).delete()
        # db.query(NavigationModuleModel).delete()
        # db.commit()

        # 迁移导航模块
        migrate_navigation(db)

        # 迁移工具集
        toolset_map = migrate_toolsets(db)

        # 迁移分类
        category_map = migrate_categories(db, toolset_map)

        # 迁移工具
        migrate_tools(db, toolset_map, category_map)

    print("=" * 50)
    print("迁移完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 创建 scripts 目录（如果不存在）**

```bash
mkdir -p backend/scripts
```

- [ ] **Step 3: 运行迁移脚本**

```bash
cd backend
python scripts/migrate_yaml_to_db.py
```

预期输出:
```
==================================================
开始 YAML 配置迁移
==================================================
迁移导航模块...
  迁移了 5 个导航模块
迁移工具集...
  迁移工具集: ai_tools
  迁移工具集: teaching_researcher
迁移工具分类...
  迁移了 X 个分类
迁移 AI 工具...
  迁移了 Y 个 AI 工具
==================================================
迁移完成!
==================================================
```

- [ ] **Step 4: 验证数据**

```bash
mysql -u root -p ai_teacher_platform -e "SELECT COUNT(*) FROM navigation_modules; SELECT COUNT(*) FROM toolsets; SELECT COUNT(*) FROM ai_tool_categories; SELECT COUNT(*) FROM ai_tools;"
```

- [ ] **Step 5: 提交变更**

```bash
git add backend/scripts/
git commit -m "feat: 添加 YAML 到数据库迁移脚本"
```

---

## Phase 3: 服务层改造

### Task 3.1: 创建数据库配置服务

**文件:**
- Create: `backend/src/services/config_service.py`

- [ ] **Step 1: 创建配置服务**

```python
# -*- coding: utf-8 -*-
"""配置服务：从数据库加载配置"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from ..db_models import (
    NavigationModuleModel, ToolsetModel, AIToolCategoryModel, AIToolModel,
    NavigationModuleType, AIToolType
)
from ..models import NavigationModule, Tool

logger = logging.getLogger(__name__)


class ConfigService:
    """配置服务：从数据库读取配置"""

    def __init__(self, db: Session):
        self.db = db

    def get_navigation_modules(self) -> List[NavigationModule]:
        """获取导航模块列表"""
        models = self.db.query(NavigationModuleModel).order_by(NavigationModuleModel.order).all()
        return [
            NavigationModule(
                name=m.name,
                type=m.type.value,
                config_source=m.config_source,
                page_path=m.page_path,
                icon=m.icon,
                order=m.order
            )
            for m in models
        ]

    def get_toolsets(self) -> List[dict]:
        """获取工具集列表"""
        models = self.db.query(ToolsetModel).order_by(ToolsetModel.order).all()
        return [
            {
                'id': str(m.id),
                'toolset_id': m.toolset_id,
                'name': m.name,
                'description': m.description,
                'icon': m.icon,
                'order': m.order
            }
            for m in models
        ]

    def get_tools_by_toolset(self, toolset_id: str) -> List[Tool]:
        """获取指定工具集的工具"""
        # 获取工具集
        toolset = self.db.query(ToolsetModel).filter(
            ToolsetModel.toolset_id == toolset_id
        ).first()

        if not toolset:
            return []

        # 获取工具
        models = self.db.query(AIToolModel).filter(
            AIToolModel.toolset_id == toolset.id,
            AIToolModel.visible == True
        ).order_by(AIToolModel.order).all()

        return [
            Tool(
                tool_id=m.tool_id,
                name=m.name,
                description=m.description,
                system_prompt=m.system_prompt,
                category=m.category.name if m.category else '',
                icon=m.icon,
                visible=m.visible,
                type=m.type.value,
                welcome_message=m.welcome_message,
                order=m.order,
                toolset_id=m.toolset_id,
                system_prompt_file=None,
                model=m.model,
                content_type=m.content_type,
                media_type=m.media_type
            )
            for m in models
        ]

    def get_all_tools(self) -> List[Tool]:
        """获取所有工具"""
        models = self.db.query(AIToolModel).filter(
            AIToolModel.visible == True
        ).order_by(AIToolModel.order).all()

        return [
            Tool(
                tool_id=m.tool_id,
                name=m.name,
                description=m.description,
                system_prompt=m.system_prompt,
                category=m.category.name if m.category else '',
                icon=m.icon,
                visible=m.visible,
                type=m.type.value,
                welcome_message=m.welcome_message,
                order=m.order,
                toolset_id=m.toolset.toolset_id,
                system_prompt_file=None,
                model=m.model,
                content_type=m.content_type,
                media_type=m.media_type
            )
            for m in models
        ]

    def get_tool_by_id(self, tool_id: str) -> Optional[Tool]:
        """根据 tool_id 获取工具"""
        m = self.db.query(AIToolModel).filter(
            AIToolModel.tool_id == tool_id
        ).first()

        if not m:
            return None

        return Tool(
            tool_id=m.tool_id,
            name=m.name,
            description=m.description,
            system_prompt=m.system_prompt,
            category=m.category.name if m.category else '',
            icon=m.icon,
            visible=m.visible,
            type=m.type.value,
            welcome_message=m.welcome_message,
            order=m.order,
            toolset_id=m.toolset.toolset_id,
            system_prompt_file=None,
            model=m.model,
            content_type=m.content_type,
            media_type=m.media_type
        )

    def get_category_config(self, toolset_id: Optional[str] = None) -> dict:
        """获取分类配置"""
        query = self.db.query(AIToolCategoryModel)

        if toolset_id:
            # 获取工具集
            toolset = self.db.query(ToolsetModel).filter(
                ToolsetModel.toolset_id == toolset_id
            ).first()
            if toolset:
                query = query.filter(AIToolCategoryModel.toolset_id == toolset.id)

        categories = query.all()

        return {
            cat.name: {
                'order': cat.order,
                'icon': cat.icon
            }
            for cat in categories
        }
```

- [ ] **Step 2: 更新 dependencies.py 添加配置服务依赖**

修改 `backend/src/interfaces/dependencies.py`，在文件末尾添加：

```python
def get_config_service():
    """获取配置服务实例（数据库版本）"""
    from src.services.config_service import ConfigService
    db = next(get_db())
    try:
        yield ConfigService(db)
    finally:
        db.close()
```

- [ ] **Step 3: 修改工具列表路由使用数据库服务**

修改 `backend/src/interfaces/routers/tools/list.py`：

```python
# 在 import 部分添加
from src.interfaces.dependencies import get_config_service
from src.services.config_service import ConfigService

# 修改 get_tools 函数
@router.get("/tools", response_model=ToolListResponse, tags=["工具"])
async def get_tools(
    current_user = Depends(get_current_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """获取所有工具列表"""
    # 从数据库加载工具
    tools = config_service.get_all_tools()

    # 按 category 聚合
    category_config = config_service.get_category_config()

    # 使用现有的聚合逻辑
    category_dict = {}
    for tool in tools:
        category_name = tool.category or "未分类"
        if category_name not in category_dict:
            cat_config = category_config.get(category_name, {})
            category_dict[category_name] = {
                'name': category_name,
                'icon': cat_config.get('icon') or tool.icon,
                'order': cat_config.get('order', 999),
                'tools': []
            }
        category_dict[category_name]['tools'].append(tool)

    # 对每个分类内的工具按 order 排序
    for category in category_dict.values():
        category['tools'].sort(key=lambda t: t.order)

    # 转换为列表并按 order 排序
    category_groups = list(category_dict.values())
    category_groups.sort(key=lambda c: c['order'])

    # 转换为响应格式
    for category in category_groups:
        category['tools'] = [
            {
                'tool_id': tool.tool_id,
                'name': tool.name,
                'description': tool.description,
                'icon': tool.icon,
                'category': tool.category,
                'visible': tool.visible,
                'type': tool.type,
                'welcome_message': tool.welcome_message,
                'toolset_id': tool.toolset_id,
                'model': tool.model,
                'content_type': tool.content_type,
                'media_type': tool.media_type,
            }
            for tool in category['tools']
        ]

    return ToolListResponse(categories=category_groups)
```

- [ ] **Step 4: 同样修改 get_toolset_tools 函数**

- [ ] **Step 5: 添加导航模块路由**

在 `backend/src/interfaces/routers/` 下创建 `navigation.py`：

```python
# -*- coding: utf-8 -*-
"""导航模块路由"""
from fastapi import APIRouter, Depends
from src.models import NavigationModuleResponse
from src.interfaces.dependencies import get_config_service
from src.services.config_service import ConfigService
from src.interfaces.auth import get_current_user

router = APIRouter()


@router.get("/navigation", response_model=NavigationModuleResponse, tags=["导航"])
async def get_navigation(
    current_user = Depends(get_current_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """获取导航模块配置"""
    modules = config_service.get_navigation_modules()
    return NavigationModuleResponse(modules=modules)
```

- [ ] **Step 6: 在 main.py 中注册导航路由**

```python
from src.interfaces.routers import navigation as new_navigation_router
app.include_router(new_navigation_router.router)
```

- [ ] **Step 7: 测试现有 API**

```bash
# 启动服务
cd backend && python -m src.main

# 测试导航 API
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/navigation

# 测试工具列表 API
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/tools
```

- [ ] **Step 8: 提交变更**

```bash
git add backend/src/services/config_service.py backend/src/interfaces/dependencies.py backend/src/interfaces/routers/tools/list.py backend/src/interfaces/routers/navigation.py backend/src/main.py
git commit -m "feat: 修改服务层从数据库读取配置

- 添加 ConfigService 从数据库读取配置
- 修改工具列表路由使用数据库服务
- 添加导航模块路由"
```

---

## Phase 4: 后台管理 API

### Task 4.1: 创建导航模块管理 API

**文件:**
- Create: `backend/src/interfaces/routers/admin/navigation.py`

- [ ] **Step 1: 创建导航模块管理路由**

```python
# -*- coding: utf-8 -*-
"""导航模块管理路由（后台）"""
import logging
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.interfaces.dependencies import get_db
from src.interfaces.auth import get_current_user
from src.models import UserInfo
from src.db_models import NavigationModuleModel, NavigationModuleType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/navigation", tags=["导航模块管理"])


async def require_admin(current_user: Annotated[UserInfo, Depends(get_current_user)]) -> UserInfo:
    """管理员权限验证"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


# Request/Response Models
class NavigationModuleItem(BaseModel):
    id: str
    name: str
    type: str
    config_source: str | None = None
    page_path: str | None = None
    icon: str | None = None
    order: int


class NavigationModuleListResponse(BaseModel):
    modules: list[NavigationModuleItem]


class CreateNavigationModuleRequest(BaseModel):
    name: str
    type: str
    config_source: str | None = None
    page_path: str | None = None
    icon: str | None = None
    order: int = 0


class UpdateNavigationModuleRequest(BaseModel):
    name: str | None = None
    type: str | None = None
    config_source: str | None = None
    page_path: str | None = None
    icon: str | None = None
    order: int | None = None


class UpdateOrderRequest(BaseModel):
    order: int


# API Endpoints
@router.get("/modules", response_model=NavigationModuleListResponse)
async def get_navigation_modules(
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取导航模块列表"""
    modules = db.query(NavigationModuleModel).order_by(NavigationModuleModel.order).all()
    return NavigationModuleListResponse(
        modules=[
            NavigationModuleItem(
                id=str(m.id),
                name=m.name,
                type=m.type.value,
                config_source=m.config_source,
                page_path=m.page_path,
                icon=m.icon,
                order=m.order
            )
            for m in modules
        ]
    )


@router.post("/modules", response_model=NavigationModuleItem, status_code=status.HTTP_201_CREATED)
async def create_navigation_module(
    request: CreateNavigationModuleRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建导航模块"""
    module_type = NavigationModuleType.toolset if request.type == 'toolset' else NavigationModuleType.page

    module = NavigationModuleModel(
        name=request.name,
        type=module_type,
        config_source=request.config_source,
        page_path=request.page_path,
        icon=request.icon,
        order=request.order
    )
    db.add(module)
    db.commit()
    db.refresh(module)

    return NavigationModuleItem(
        id=str(module.id),
        name=module.name,
        type=module.type.value,
        config_source=module.config_source,
        page_path=module.page_path,
        icon=module.icon,
        order=module.order
    )


@router.put("/modules/{module_id}", response_model=NavigationModuleItem)
async def update_navigation_module(
    module_id: str,
    request: UpdateNavigationModuleRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新导航模块"""
    module = db.query(NavigationModuleModel).filter(
        NavigationModuleModel.id == module_id
    ).first()

    if not module:
        raise HTTPException(status_code=404, detail="导航模块不存在")

    if request.name is not None:
        module.name = request.name
    if request.type is not None:
        module.type = NavigationModuleType.toolset if request.type == 'toolset' else NavigationModuleType.page
    if request.config_source is not None:
        module.config_source = request.config_source
    if request.page_path is not None:
        module.page_path = request.page_path
    if request.icon is not None:
        module.icon = request.icon
    if request.order is not None:
        module.order = request.order

    db.commit()
    db.refresh(module)

    return NavigationModuleItem(
        id=str(module.id),
        name=module.name,
        type=module.type.value,
        config_source=module.config_source,
        page_path=module.page_path,
        icon=module.icon,
        order=module.order
    )


@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_navigation_module(
    module_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除导航模块"""
    module = db.query(NavigationModuleModel).filter(
        NavigationModuleModel.id == module_id
    ).first()

    if not module:
        raise HTTPException(status_code=404, detail="导航模块不存在")

    db.delete(module)
    db.commit()


@router.patch("/modules/{module_id}/order")
async def update_module_order(
    module_id: str,
    request: UpdateOrderRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新导航模块排序"""
    module = db.query(NavigationModuleModel).filter(
        NavigationModuleModel.id == module_id
    ).first()

    if not module:
        raise HTTPException(status_code=404, detail="导航模块不存在")

    module.order = request.order
    db.commit()

    return {"message": "排序已更新", "order": request.order}
```

- [ ] **Step 2: 在 main.py 中注册路由**

```python
from src.interfaces.routers.admin import navigation as admin_navigation_router
app.include_router(admin_navigation_router.router)
```

- [ ] **Step 3: 测试 API**

```bash
curl -X GET http://localhost:8000/api/v1/admin/navigation/modules \
  -H "Authorization: Bearer <admin-token>"

curl -X POST http://localhost:8000/api/v1/admin/navigation/modules \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "测试模块", "type": "page", "page_path": "/test", "order": 99}'
```

- [ ] **Step 4: 提交变更**

```bash
git add backend/src/interfaces/routers/admin/navigation.py backend/src/main.py
git commit -m "feat: 添加导航模块管理 API"
```

---

### Task 4.2: 创建工具集管理 API

**文件:**
- Create: `backend/src/interfaces/routers/admin/toolsets.py`

- [ ] **Step 1: 创建工具集管理路由**

```python
# -*- coding: utf-8 -*-
"""工具集管理路由（后台）"""
import logging
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.interfaces.dependencies import get_db
from src.interfaces.auth import get_current_user
from src.models import UserInfo
from src.db_models import ToolsetModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/toolsets", tags=["工具集管理"])


async def require_admin(current_user: Annotated[UserInfo, Depends(get_current_user)]) -> UserInfo:
    """管理员权限验证"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


# Request/Response Models
class ToolsetItem(BaseModel):
    id: str
    toolset_id: str
    name: str
    description: str | None = None
    icon: str | None = None
    order: int


class ToolsetListResponse(BaseModel):
    toolsets: list[ToolsetItem]


class CreateToolsetRequest(BaseModel):
    toolset_id: str
    name: str
    description: str | None = None
    icon: str | None = None
    order: int = 0


class UpdateToolsetRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    icon: str | None = None
    order: int | None = None


# API Endpoints
@router.get("", response_model=ToolsetListResponse)
async def get_toolsets(
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取工具集列表"""
    toolsets = db.query(ToolsetModel).order_by(ToolsetModel.order).all()
    return ToolsetListResponse(
        toolsets=[
            ToolsetItem(
                id=str(t.id),
                toolset_id=t.toolset_id,
                name=t.name,
                description=t.description,
                icon=t.icon,
                order=t.order
            )
            for t in toolsets
        ]
    )


@router.post("", response_model=ToolsetItem, status_code=status.HTTP_201_CREATED)
async def create_toolset(
    request: CreateToolsetRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建工具集"""
    # 检查 toolset_id 是否已存在
    existing = db.query(ToolsetModel).filter(
        ToolsetModel.toolset_id == request.toolset_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="工具集ID已存在")

    toolset = ToolsetModel(
        toolset_id=request.toolset_id,
        name=request.name,
        description=request.description,
        icon=request.icon,
        order=request.order
    )
    db.add(toolset)
    db.commit()
    db.refresh(toolset)

    return ToolsetItem(
        id=str(toolset.id),
        toolset_id=toolset.toolset_id,
        name=toolset.name,
        description=toolset.description,
        icon=toolset.icon,
        order=toolset.order
    )


@router.put("/{toolset_id}", response_model=ToolsetItem)
async def update_toolset(
    toolset_id: str,
    request: UpdateToolsetRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新工具集"""
    toolset = db.query(ToolsetModel).filter(
        ToolsetModel.toolset_id == toolset_id
    ).first()

    if not toolset:
        raise HTTPException(status_code=404, detail="工具集不存在")

    if request.name is not None:
        toolset.name = request.name
    if request.description is not None:
        toolset.description = request.description
    if request.icon is not None:
        toolset.icon = request.icon
    if request.order is not None:
        toolset.order = request.order

    db.commit()
    db.refresh(toolset)

    return ToolsetItem(
        id=str(toolset.id),
        toolset_id=toolset.toolset_id,
        name=toolset.name,
        description=toolset.description,
        icon=toolset.icon,
        order=toolset.order
    )


@router.delete("/{toolset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_toolset(
    toolset_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除工具集"""
    toolset = db.query(ToolsetModel).filter(
        ToolsetModel.toolset_id == toolset_id
    ).first()

    if not toolset:
        raise HTTPException(status_code=404, detail="工具集不存在")

    db.delete(toolset)
    db.commit()
```

- [ ] **Step 2: 在 main.py 中注册路由**

```python
from src.interfaces.routers.admin import toolsets as admin_toolsets_router
app.include_router(admin_toolsets_router.router)
```

- [ ] **Step 3: 提交变更**

```bash
git add backend/src/interfaces/routers/admin/toolsets.py backend/src/main.py
git commit -m "feat: 添加工具集管理 API"
```

---

### Task 4.3: 创建工具分类管理 API

**文件:**
- Create: `backend/src/interfaces/routers/admin/ai_tool_categories.py`

- [ ] **Step 1: 创建工具分类管理路由**

```python
# -*- coding: utf-8 -*-
"""AI工具分类管理路由（后台）"""
import logging
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.interfaces.dependencies import get_db
from src.interfaces.auth import get_current_user
from src.models import UserInfo
from src.db_models import AIToolCategoryModel, ToolsetModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/tool-categories", tags=["工具分类管理"])


async def require_admin(current_user: Annotated[UserInfo, Depends(get_current_user)]) -> UserInfo:
    """管理员权限验证"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


# Request/Response Models
class ToolCategoryItem(BaseModel):
    id: str
    toolset_id: str
    toolset_name: str
    name: str
    icon: str | None = None
    order: int


class ToolCategoryListResponse(BaseModel):
    categories: list[ToolCategoryItem]


class CreateToolCategoryRequest(BaseModel):
    toolset_id: str
    name: str
    icon: str | None = None
    order: int = 0


class UpdateToolCategoryRequest(BaseModel):
    name: str | None = None
    icon: str | None = None
    order: int | None = None


class UpdateOrderRequest(BaseModel):
    order: int


# API Endpoints
@router.get("", response_model=ToolCategoryListResponse)
async def get_tool_categories(
    toolset_id: str | None = None,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取工具分类列表"""
    query = db.query(AIToolCategoryModel)

    if toolset_id:
        toolset = db.query(ToolsetModel).filter(
            ToolsetModel.toolset_id == toolset_id
        ).first()
        if toolset:
            query = query.filter(AIToolCategoryModel.toolset_id == toolset.id)

    categories = query.order_by(AIToolCategoryModel.order).all()

    return ToolCategoryListResponse(
        categories=[
            ToolCategoryItem(
                id=str(c.id),
                toolset_id=str(c.toolset_id),
                toolset_name=c.toolset.name,
                name=c.name,
                icon=c.icon,
                order=c.order
            )
            for c in categories
        ]
    )


@router.post("", response_model=ToolCategoryItem, status_code=status.HTTP_201_CREATED)
async def create_tool_category(
    request: CreateToolCategoryRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建工具分类"""
    # 获取工具集
    toolset = db.query(ToolsetModel).filter(
        ToolsetModel.toolset_id == request.toolset_id
    ).first()
    if not toolset:
        raise HTTPException(status_code=404, detail="工具集不存在")

    category = AIToolCategoryModel(
        toolset_id=toolset.id,
        name=request.name,
        icon=request.icon,
        order=request.order
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return ToolCategoryItem(
        id=str(category.id),
        toolset_id=str(category.toolset_id),
        toolset_name=category.toolset.name,
        name=category.name,
        icon=category.icon,
        order=category.order
    )


@router.put("/{category_id}", response_model=ToolCategoryItem)
async def update_tool_category(
    category_id: str,
    request: UpdateToolCategoryRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新工具分类"""
    category = db.query(AIToolCategoryModel).filter(
        AIToolCategoryModel.id == category_id
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    if request.name is not None:
        category.name = request.name
    if request.icon is not None:
        category.icon = request.icon
    if request.order is not None:
        category.order = request.order

    db.commit()
    db.refresh(category)

    return ToolCategoryItem(
        id=str(category.id),
        toolset_id=str(category.toolset_id),
        toolset_name=category.toolset.name,
        name=category.name,
        icon=category.icon,
        order=category.order
    )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool_category(
    category_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除工具分类"""
    category = db.query(AIToolCategoryModel).filter(
        AIToolCategoryModel.id == category_id
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    db.delete(category)
    db.commit()


@router.patch("/{category_id}/order")
async def update_category_order(
    category_id: str,
    request: UpdateOrderRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新分类排序"""
    category = db.query(AIToolCategoryModel).filter(
        AIToolCategoryModel.id == category_id
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    category.order = request.order
    db.commit()

    return {"message": "排序已更新", "order": request.order}
```

- [ ] **Step 2: 在 main.py 中注册路由**

```python
from src.interfaces.routers.admin import ai_tool_categories as admin_categories_router
app.include_router(admin_categories_router.router)
```

- [ ] **Step 3: 提交变更**

```bash
git add backend/src/interfaces/routers/admin/ai_tool_categories.py backend/src/main.py
git commit -m "feat: 添加工具分类管理 API"
```

---

### Task 4.4: 创建 AI工具管理 API

**文件:**
- Create: `backend/src/interfaces/routers/admin/ai_tools.py`

- [ ] **Step 1: 创建 AI工具管理路由**

```python
# -*- coding: utf-8 -*-
"""AI工具管理路由（后台）"""
import logging
from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.interfaces.dependencies import get_db
from src.interfaces.auth import get_current_user
from src.models import UserInfo
from src.db_models import AIToolModel, ToolsetModel, AIToolCategoryModel, AIToolType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/ai-tools", tags=["AI工具管理"])


async def require_admin(current_user: Annotated[UserInfo, Depends(get_current_user)]) -> UserInfo:
    """管理员权限验证"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


# Request/Response Models
class AIToolItem(BaseModel):
    id: str
    tool_id: str
    toolset_id: str
    toolset_name: str
    category_id: str | None = None
    category_name: str | None = None
    name: str
    description: str | None = None
    system_prompt: str | None = None
    icon: str | None = None
    type: str
    content_type: str | None = None
    media_type: str | None = None
    model: str | None = None
    welcome_message: str | None = None
    visible: bool
    order: int


class AIToolListResponse(BaseModel):
    tools: list[AIToolItem]
    total: int


class CreateAIToolRequest(BaseModel):
    tool_id: str
    toolset_id: str
    category_id: str | None = None
    name: str
    description: str | None = None
    system_prompt: str | None = None
    icon: str | None = None
    type: str = "normal"
    content_type: str | None = None
    media_type: str | None = None
    model: str | None = None
    welcome_message: str | None = None
    visible: bool = True
    order: int = 0


class UpdateAIToolRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    icon: str | None = None
    type: str | None = None
    content_type: str | None = None
    media_type: str | None = None
    model: str | None = None
    welcome_message: str | None = None
    visible: bool | None = None
    order: int | None = None
    category_id: str | None = None


class ToggleVisibilityResponse(BaseModel):
    message: str
    visible: bool


class UpdateOrderRequest(BaseModel):
    order: int


# API Endpoints
@router.get("", response_model=AIToolListResponse)
async def get_ai_tools(
    toolset_id: Optional[str] = None,
    category_id: Optional[str] = None,
    visible: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取 AI 工具列表"""
    query = db.query(AIToolModel)

    if toolset_id:
        toolset = db.query(ToolsetModel).filter(
            ToolsetModel.toolset_id == toolset_id
        ).first()
        if toolset:
            query = query.filter(AIToolModel.toolset_id == toolset.id)

    if category_id:
        query = query.filter(AIToolModel.category_id == category_id)

    if visible is not None:
        query = query.filter(AIToolModel.visible == visible)

    total = query.count()

    tools = query.order_by(AIToolModel.order).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return AIToolListResponse(
        tools=[
            AIToolItem(
                id=str(t.id),
                tool_id=t.tool_id,
                toolset_id=str(t.toolset_id),
                toolset_name=t.toolset.name,
                category_id=str(t.category_id) if t.category_id else None,
                category_name=t.category.name if t.category else None,
                name=t.name,
                description=t.description,
                system_prompt=t.system_prompt,
                icon=t.icon,
                type=t.type.value,
                content_type=t.content_type,
                media_type=t.media_type,
                model=t.model,
                welcome_message=t.welcome_message,
                visible=t.visible,
                order=t.order
            )
            for t in tools
        ],
        total=total
    )


@router.post("", response_model=AIToolItem, status_code=status.HTTP_201_CREATED)
async def create_ai_tool(
    request: CreateAIToolRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建 AI 工具"""
    # 检查 tool_id 是否已存在
    existing = db.query(AIToolModel).filter(
        AIToolModel.tool_id == request.tool_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="工具ID已存在")

    # 获取工具集
    toolset = db.query(ToolsetModel).filter(
        ToolsetModel.toolset_id == request.toolset_id
    ).first()
    if not toolset:
        raise HTTPException(status_code=404, detail="工具集不存在")

    # 获取分类（如果提供）
    category = None
    if request.category_id:
        category = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.id == request.category_id
        ).first()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")

    tool_type = AIToolType.media if request.type == 'media' else AIToolType.normal

    tool = AIToolModel(
        tool_id=request.tool_id,
        toolset_id=toolset.id,
        category_id=category.id if category else None,
        name=request.name,
        description=request.description,
        system_prompt=request.system_prompt,
        icon=request.icon,
        type=tool_type,
        content_type=request.content_type,
        media_type=request.media_type,
        model=request.model,
        welcome_message=request.welcome_message,
        visible=request.visible,
        order=request.order
    )
    db.add(tool)
    db.commit()
    db.refresh(tool)

    return AIToolItem(
        id=str(tool.id),
        tool_id=tool.tool_id,
        toolset_id=str(tool.toolset_id),
        toolset_name=tool.toolset.name,
        category_id=str(tool.category_id) if tool.category_id else None,
        category_name=tool.category.name if tool.category else None,
        name=tool.name,
        description=tool.description,
        system_prompt=tool.system_prompt,
        icon=tool.icon,
        type=tool.type.value,
        content_type=tool.content_type,
        media_type=tool.media_type,
        model=tool.model,
        welcome_message=tool.welcome_message,
        visible=tool.visible,
        order=tool.order
    )


@router.put("/{tool_id}", response_model=AIToolItem)
async def update_ai_tool(
    tool_id: str,
    request: UpdateAIToolRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新 AI 工具"""
    tool = db.query(AIToolModel).filter(
        AIToolModel.tool_id == tool_id
    ).first()

    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")

    # 更新分类
    if request.category_id is not None:
        if request.category_id == "":
            tool.category_id = None
        else:
            category = db.query(AIToolCategoryModel).filter(
                AIToolCategoryModel.id == request.category_id
            ).first()
            if not category:
                raise HTTPException(status_code=404, detail="分类不存在")
            tool.category_id = category.id

    # 更新其他字段
    if request.name is not None:
        tool.name = request.name
    if request.description is not None:
        tool.description = request.description
    if request.system_prompt is not None:
        tool.system_prompt = request.system_prompt
    if request.icon is not None:
        tool.icon = request.icon
    if request.type is not None:
        tool.type = AIToolType.media if request.type == 'media' else AIToolType.normal
    if request.content_type is not None:
        tool.content_type = request.content_type
    if request.media_type is not None:
        tool.media_type = request.media_type
    if request.model is not None:
        tool.model = request.model
    if request.welcome_message is not None:
        tool.welcome_message = request.welcome_message
    if request.visible is not None:
        tool.visible = request.visible
    if request.order is not None:
        tool.order = request.order

    db.commit()
    db.refresh(tool)

    return AIToolItem(
        id=str(tool.id),
        tool_id=tool.tool_id,
        toolset_id=str(tool.toolset_id),
        toolset_name=tool.toolset.name,
        category_id=str(tool.category_id) if tool.category_id else None,
        category_name=tool.category.name if tool.category else None,
        name=tool.name,
        description=tool.description,
        system_prompt=tool.system_prompt,
        icon=tool.icon,
        type=tool.type.value,
        content_type=tool.content_type,
        media_type=tool.media_type,
        model=tool.model,
        welcome_message=tool.welcome_message,
        visible=tool.visible,
        order=tool.order
    )


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_tool(
    tool_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除 AI 工具"""
    tool = db.query(AIToolModel).filter(
        AIToolModel.tool_id == tool_id
    ).first()

    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")

    db.delete(tool)
    db.commit()


@router.patch("/{tool_id}/toggle", response_model=ToggleVisibilityResponse)
async def toggle_tool_visibility(
    tool_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """切换工具可见性"""
    tool = db.query(AIToolModel).filter(
        AIToolModel.tool_id == tool_id
    ).first()

    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")

    tool.visible = not tool.visible
    db.commit()

    return ToggleVisibilityResponse(
        message=f"工具已{'显示' if tool.visible else '隐藏'}",
        visible=tool.visible
    )


@router.patch("/{tool_id}/order")
async def update_tool_order(
    tool_id: str,
    request: UpdateOrderRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新工具排序"""
    tool = db.query(AIToolModel).filter(
        AIToolModel.tool_id == tool_id
    ).first()

    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")

    tool.order = request.order
    db.commit()

    return {"message": "排序已更新", "order": request.order}
```

- [ ] **Step 2: 在 main.py 中注册路由**

```python
from src.interfaces.routers.admin import ai_tools as admin_ai_tools_router
app.include_router(admin_ai_tools_router.router)
```

- [ ] **Step 3: 提交变更**

```bash
git add backend/src/interfaces/routers/admin/ai_tools.py backend/src/main.py
git commit -m "feat: 添加 AI 工具管理 API"
```

---

## Phase 5: 前端管理页面

### Task 5.1: 抽取 Markdown 编辑器组件

**文件:**
- Create: `frontend/src/components/editor/MarkdownEditor.vue`
- Modify: `frontend/src/views/MarkdownEditorView.vue`

- [ ] **Step 1: 创建 MarkdownEditor 组件**

```vue
<template>
  <div class="markdown-editor" :class="{ fullscreen: isFullscreen }">
    <!-- 编辑器容器 -->
    <div class="editor-container">
      <!-- 左侧：CodeMirror 编辑器 -->
      <div class="editor-panel" :style="{ width: `${editorWidth}%` }">
        <div ref="editorRef" class="editor-content"></div>
      </div>

      <!-- 可拖动分隔条 -->
      <div
        v-if="!isFullscreen"
        class="resizer"
        @mousedown="startResize"
        @touchstart="startResize"
      >
        <div class="resizer-line"></div>
      </div>

      <!-- 右侧：预览面板 -->
      <div class="preview-container" :style="{ width: isFullscreen ? '100%' : `${100 - editorWidth}%` }">
        <PreviewPanel :artifact="previewArtifact" />
      </div>
    </div>

    <!-- 全屏模式下的关闭按钮 -->
    <button v-if="isFullscreen" @click="exitFullscreen" class="fullscreen-close">
      退出全屏
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { EditorView, keymap, lineNumbers, highlightActiveLineGutter, highlightActiveLine } from '@codemirror/view'
import { EditorState } from '@codemirror/state'
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands'
import { markdown } from '@codemirror/lang-markdown'
import { oneDark } from '@codemirror/theme-one-dark'
import { syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language'
import PreviewPanel from '../preview/PreviewPanel.vue'
import type { Artifact } from '../../types'

interface Props {
  modelValue: string
  fullscreen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  fullscreen: false
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

// 编辑器引用
const editorRef = ref<HTMLElement | null>(null)
let editorView: EditorView | null = null

// 分隔条宽度（百分比）
const editorWidth = ref(50)
const isResizing = ref(false)
const isFullscreen = ref(props.fullscreen)

// 编辑器内容
const editorContent = ref(props.modelValue)

// 预览成果物
const previewArtifact = computed<Artifact>(() => ({
  type: 'markdown',
  content: editorContent.value,
  language: 'markdown',
  timestamp: new Date().toISOString(),
}))

// 监听外部值变化
watch(() => props.modelValue, (newValue) => {
  if (newValue !== editorContent.value && editorView) {
    const transaction = editorView.state.update({
      changes: { from: 0, to: editorView.state.doc.length, insert: newValue },
    })
    editorView.dispatch(transaction)
  }
})

/**
 * 初始化 CodeMirror 编辑器
 */
const initEditor = () => {
  if (!editorRef.value) return

  const startState = EditorState.create({
    doc: editorContent.value,
    extensions: [
      lineNumbers(),
      highlightActiveLineGutter(),
      highlightActiveLine(),
      history(),
      keymap.of([...defaultKeymap, ...historyKeymap]),
      markdown(),
      syntaxHighlighting(defaultHighlightStyle),
      oneDark,
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          editorContent.value = update.state.doc.toString()
          emit('update:modelValue', editorContent.value)
        }
      }),
      EditorView.lineWrapping,
    ],
  })

  editorView = new EditorView({
    state: startState,
    parent: editorRef.value,
  })
}

/**
 * 开始调整大小
 */
const startResize = (e: MouseEvent | TouchEvent) => {
  isResizing.value = true
  e.preventDefault()

  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.addEventListener('touchmove', handleResize)
  document.addEventListener('touchend', stopResize)

  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

/**
 * 调整大小中
 */
const handleResize = (e: MouseEvent | TouchEvent) => {
  if (!isResizing.value) return

  const container = document.querySelector('.markdown-editor .editor-container') as HTMLElement
  if (!container) return

  const containerRect = container.getBoundingClientRect()
  const clientX = 'touches' in e ? (e.touches[0]?.clientX ?? 0) : e.clientX

  const newWidth = ((clientX - containerRect.left) / containerRect.width) * 100
  editorWidth.value = Math.max(30, Math.min(70, newWidth))
}

/**
 * 停止调整大小
 */
const stopResize = () => {
  isResizing.value = false

  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.removeEventListener('touchmove', handleResize)
  document.removeEventListener('touchend', stopResize)

  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

/**
 * 进入全屏模式
 */
const enterFullscreen = () => {
  isFullscreen.value = true
}

/**
 * 退出全屏模式
 */
const exitFullscreen = () => {
  isFullscreen.value = false
}

// 暴露方法
defineExpose({
  enterFullscreen,
  exitFullscreen
})

// 组件挂载时初始化编辑器
onMounted(() => {
  initEditor()
})

// 组件卸载时销毁编辑器
onBeforeUnmount(() => {
  if (editorView) {
    editorView.destroy()
    editorView = null
  }
})
</script>

<style scoped>
.markdown-editor {
  @apply h-full w-full overflow-hidden flex flex-col;
  background-color: theme('colors.gray.50');
}

.markdown-editor.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
}

.editor-container {
  @apply flex-1 flex overflow-hidden relative;
}

.editor-panel {
  @apply flex flex-col border-r border-gray-200 bg-white;
  min-width: 30%;
  max-width: 70%;
}

.resizer {
  @apply flex-shrink-0 w-1 bg-gray-200 hover:bg-blue-400 cursor-col-resize relative transition-colors;
  z-index: 10;
}

.resizer:hover .resizer-line {
  @apply opacity-100;
}

.resizer-line {
  @apply absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-1 h-12 bg-blue-500 rounded-full opacity-0 transition-opacity;
}

.editor-content {
  @apply flex-1 overflow-auto;
}

.editor-content :deep(.cm-editor) {
  @apply h-full;
  font-size: 14px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
}

.editor-content :deep(.cm-scroller) {
  @apply overflow-auto;
}

.editor-content :deep(.cm-content) {
  @apply p-4;
}

.preview-container {
  @apply flex flex-col bg-white;
  min-width: 30%;
  max-width: 70%;
}

.fullscreen-close {
  position: absolute;
  top: 10px;
  right: 10px;
  @apply px-4 py-2 bg-white border border-gray-300 rounded-lg shadow-lg hover:bg-gray-50;
  z-index: 10000;
}

@media (max-width: 767px) {
  .editor-container {
    @apply flex-col;
  }

  .editor-panel,
  .preview-container {
    @apply w-full;
    min-width: unset;
    max-width: unset;
    height: 50%;
  }

  .editor-panel {
    @apply border-r-0 border-b border-gray-200;
  }

  .resizer {
    @apply hidden;
  }
}
</style>
```

- [ ] **Step 2: 修改 MarkdownEditorView.vue 使用新组件**

在 `frontend/src/views/MarkdownEditorView.vue` 中：

```vue
<template>
  <div class="markdown-editor-view">
    <!-- 顶部工具条 -->
    <div class="toolbar">
      <div class="toolbar-title">
        <DocumentTextIcon class="w-5 h-5 text-blue-600" />
        <span>Markdown 编辑器</span>
      </div>
      <div class="toolbar-actions">
        <button class="toolbar-btn" @click="handleClear" title="清空内容">
          <TrashIcon class="w-4 h-4" />
          <span>清空</span>
        </button>
        <button class="toolbar-btn back-btn" @click="handleBack">
          <ArrowLeftIcon class="w-5 h-5" />
          <span>返回</span>
        </button>
      </div>
    </div>

    <!-- 使用新的 MarkdownEditor 组件 -->
    <MarkdownEditor v-model="content" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeftIcon, DocumentTextIcon, TrashIcon } from '@heroicons/vue/24/outline'
import MarkdownEditor from '../components/editor/MarkdownEditor.vue'

const router = useRouter()
const content = ref(`# 欢迎使用 Markdown 编辑器

...（保留原有默认内容）
`)

const handleBack = () => {
  router.push('/common-tools')
}

const handleClear = () => {
  if (confirm('确定要清空所有内容吗？此操作不可撤销。')) {
    content.value = ''
  }
}
</script>

<style scoped>
/* 保留原有样式 */
.markdown-editor-view {
  @apply h-full w-full overflow-hidden flex flex-col;
  background-color: theme('colors.gray.50');
}

.toolbar {
  @apply flex items-center gap-4 px-6 py-3 bg-white border-b border-gray-200;
  flex-shrink: 0;
}

.toolbar-btn {
  @apply flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all;
}

.toolbar-btn:hover {
  @apply shadow-sm;
}

.back-btn {
  @apply text-gray-600 hover:text-gray-900;
}

.toolbar-title {
  @apply flex items-center gap-2 text-lg font-semibold text-gray-900 flex-1;
}

.toolbar-actions {
  @apply flex items-center gap-2;
}
</style>
```

- [ ] **Step 3: 提交变更**

```bash
git add frontend/src/components/editor/MarkdownEditor.vue frontend/src/views/MarkdownEditorView.vue
git commit -m "refactor: 抽取 Markdown 编辑器为可复用组件"
```

---

### Task 5.2: 创建图标选择器组件

**文件:**
- Create: `frontend/src/components/editor/IconSelector.vue`

- [ ] **Step 1: 创建图标选择器组件**

```vue
<template>
  <div v-if="isOpen" class="icon-selector-overlay" @click="close">
    <div class="icon-selector-panel" @click.stop>
      <div class="icon-selector-header">
        <h3>选择图标</h3>
        <button @click="close" class="close-btn">
          <XMarkIcon class="w-5 h-5" />
        </button>
      </div>

      <div class="icon-selector-search">
        <input
          v-model="searchQuery"
          ref="searchInput"
          type="text"
          placeholder="搜索图标名称..."
          class="search-input"
        />
      </div>

      <div class="icon-selector-grid">
        <div
          v-for="icon in filteredIcons"
          :key="icon.name"
          :class="['icon-item', { selected: selectedIcon === icon.name }]"
          @click="selectIcon(icon.name)"
          :title="icon.name"
        >
          <component :is="icon.component" class="w-6 h-6" />
          <span class="icon-name">{{ icon.name }}</span>
        </div>
      </div>

      <div class="icon-selector-footer">
        <button @click="clearSelection" class="clear-btn">清除选择</button>
        <span class="selected-info">{{ selectedIcon || '未选择' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import {
  SparklesIcon, AcademicCapIcon, Cog6ToothIcon, PhotoIcon, DocumentTextIcon,
  ChatBubbleLeftRightIcon, CommandLineIcon, GlobeAltIcon, MusicalNoteIcon,
  VideoCameraIcon, MicrophoneIcon, PaintBrushIcon, CodeBracketIcon,
  CubeIcon, BeakerIcon, BookOpenIcon, PencilIcon, AdjustmentsHorizontalIcon,
  ServerIcon, CloudIcon, LockClosedIcon, XMarkIcon
} from '@heroicons/vue/24/outline'

interface Props {
  modelValue: string | null
  open: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: string | null]
  'update:open': [value: boolean]
}>()

const isOpen = ref(props.open)
const searchQuery = ref('')
const searchInput = ref<HTMLInputElement | null>(null)

// Heroicons 图标列表
const iconList = [
  { name: 'sparkles', component: SparklesIcon },
  { name: 'academic-cap', component: AcademicCapIcon },
  { name: 'cog-6-tooth', component: Cog6ToothIcon },
  { name: 'photo', component: PhotoIcon },
  { name: 'document-text', component: DocumentTextIcon },
  { name: 'chat-bubble-left-right', component: ChatBubbleLeftRightIcon },
  { name: 'command-line', component: CommandLineIcon },
  { name: 'globe-alt', component: GlobeAltIcon },
  { name: 'musical-note', component: MusicalNoteIcon },
  { name: 'video-camera', component: VideoCameraIcon },
  { name: 'microphone', component: MicrophoneIcon },
  { name: 'paint-brush', component: PaintBrushIcon },
  { name: 'code-bracket', component: CodeBracketIcon },
  { name: 'cube', component: CubeIcon },
  { name: 'beaker', component: BeakerIcon },
  { name: 'book-open', component: BookOpenIcon },
  { name: 'pencil', component: PencilIcon },
  { name: 'adjustments-horizontal', component: AdjustmentsHorizontalIcon },
  { name: 'server', component: ServerIcon },
  { name: 'cloud', component: CloudIcon },
  { name: 'lock-closed', component: LockClosedIcon },
]

const selectedIcon = ref(props.modelValue)

// 过滤图标
const filteredIcons = computed(() => {
  if (!searchQuery.value) return iconList
  const query = searchQuery.value.toLowerCase()
  return iconList.filter(icon => icon.name.includes(query))
})

// 监听 open 变化
watch(() => props.open, (newValue) => {
  isOpen.value = newValue
  if (newValue) {
    nextTick(() => {
      searchInput.value?.focus()
    })
  }
})

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  selectedIcon.value = newValue
})

const selectIcon = (iconName: string) => {
  selectedIcon.value = iconName
  emit('update:modelValue', iconName)
  close()
}

const clearSelection = () => {
  selectedIcon.value = null
  emit('update:modelValue', null)
}

const close = () => {
  isOpen.value = false
  emit('update:open', false)
}
</script>

<style scoped>
.icon-selector-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.icon-selector-panel {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.icon-selector-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid theme('colors.gray.200');
}

.icon-selector-header h3 {
  @apply text-lg font-semibold text-gray-900;
  margin: 0;
}

.close-btn {
  @apply p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors;
}

.icon-selector-search {
  padding: 16px 20px;
  border-bottom: 1px solid theme('colors.gray.200');
}

.search-input {
  @apply w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500;
  font-size: 14px;
}

.icon-selector-grid {
  padding: 16px 20px;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
  max-height: 400px;
}

.icon-item {
  @apply flex flex-col items-center justify-center p-4 border border-gray-200 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-all;
  min-height: 80px;
}

.icon-item.selected {
  @apply border-blue-500 bg-blue-50 ring-2 ring-blue-500;
}

.icon-item svg {
  @apply text-gray-700;
}

.icon-item:hover svg,
.icon-item.selected svg {
  @apply text-blue-600;
}

.icon-name {
  @apply text-xs text-gray-500 mt-2 text-center truncate w-full;
}

.icon-selector-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-top: 1px solid theme('colors.gray.200');
}

.clear-btn {
  @apply px-3 py-1.5 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors;
}

.selected-info {
  @apply text-sm text-gray-600;
}
</style>
```

- [ ] **Step 2: 提交变更**

```bash
git add frontend/src/components/editor/IconSelector.vue
git commit -m "feat: 添加图标选择器组件"
```

---

### Task 5.3: 创建导航模块管理页面

**文件:**
- Create: `frontend/src/views/admin/AdminNavigationPage.vue`

- [ ] **Step 1: 创建导航模块管理页面**

```vue
<template>
  <div class="admin-navigation-page">
    <div class="page-header">
      <h1>导航模块管理</h1>
      <button @click="showCreateDialog = true" class="btn-primary">
        新建模块
      </button>
    </div>

    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>排序</th>
            <th>名称</th>
            <th>类型</th>
            <th>图标</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="module in modules" :key="module.id">
            <td>{{ module.order }}</td>
            <td>{{ module.name }}</td>
            <td>
              <span :class="['type-badge', module.type]">
                {{ module.type === 'toolset' ? '工具集' : '页面' }}
              </span>
            </td>
            <td>
              <span v-if="module.icon" class="icon-name">{{ module.icon }}</span>
              <span v-else class="text-gray-400">-</span>
            </td>
            <td>
              <button @click="editModule(module)" class="btn-action">编辑</button>
              <button @click="deleteModule(module.id)" class="btn-action btn-danger">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 创建/编辑对话框 -->
    <div v-if="showCreateDialog || editingModule" class="dialog-overlay" @click="closeDialog">
      <div class="dialog-panel" @click.stop>
        <h2>{{ editingModule ? '编辑模块' : '新建模块' }}</h2>
        <form @submit.prevent="saveModule">
          <div class="form-group">
            <label>名称</label>
            <input v-model="formData.name" type="text" required class="form-input" />
          </div>
          <div class="form-group">
            <label>类型</label>
            <select v-model="formData.type" class="form-select">
              <option value="toolset">工具集</option>
              <option value="page">页面</option>
            </select>
          </div>
          <div v-if="formData.type === 'toolset'" class="form-group">
            <label>配置目录</label>
            <input v-model="formData.config_source" type="text" class="form-input" placeholder="如: tools/ai_tools" />
          </div>
          <div v-if="formData.type === 'page'" class="form-group">
            <label>页面路径</label>
            <input v-model="formData.page_path" type="text" class="form-input" placeholder="如: /common-tools" />
          </div>
          <div class="form-group">
            <label>图标</label>
            <div class="icon-input-group">
              <input v-model="formData.icon" type="text" class="form-input" placeholder="sparkles" />
              <button type="button" @click="showIconSelector = true" class="btn-icon">选择</button>
            </div>
          </div>
          <div class="form-group">
            <label>排序</label>
            <input v-model.number="formData.order" type="number" class="form-input" />
          </div>
          <div class="form-actions">
            <button type="button" @click="closeDialog" class="btn-secondary">取消</button>
            <button type="submit" class="btn-primary">保存</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 图标选择器 -->
    <IconSelector v-model="formData.icon" :open="showIconSelector" @update:open="showIconSelector = $event" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '../../services/apiClient'
import IconSelector from '../../components/editor/IconSelector.vue'

interface NavigationModule {
  id: string
  name: string
  type: string
  config_source: string | null
  page_path: string | null
  icon: string | null
  order: number
}

const modules = ref<NavigationModule[]>([])
const showCreateDialog = ref(false)
const editingModule = ref<NavigationModule | null>(null)
const showIconSelector = ref(false)

const formData = ref({
  name: '',
  type: 'toolset',
  config_source: '',
  page_path: '',
  icon: '',
  order: 0
})

const loadModules = async () => {
  try {
    const response = await apiClient.get('/api/v1/admin/navigation/modules')
    modules.value = response.data.modules
  } catch (error) {
    console.error('加载导航模块失败:', error)
  }
}

const editModule = (module: NavigationModule) => {
  editingModule.value = module
  formData.value = {
    name: module.name,
    type: module.type,
    config_source: module.config_source || '',
    page_path: module.page_path || '',
    icon: module.icon || '',
    order: module.order
  }
}

const saveModule = async () => {
  try {
    if (editingModule.value) {
      await apiClient.put(`/api/v1/admin/navigation/modules/${editingModule.value.id}`, formData.value)
    } else {
      await apiClient.post('/api/v1/admin/navigation/modules', formData.value)
    }
    closeDialog()
    await loadModules()
  } catch (error) {
    console.error('保存失败:', error)
    alert('保存失败，请重试')
  }
}

const deleteModule = async (id: string) => {
  if (!confirm('确定要删除此模块吗？')) return

  try {
    await apiClient.delete(`/api/v1/admin/navigation/modules/${id}`)
    await loadModules()
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败，请重试')
  }
}

const closeDialog = () => {
  showCreateDialog.value = false
  editingModule.value = null
  formData.value = {
    name: '',
    type: 'toolset',
    config_source: '',
    page_path: '',
    icon: '',
    order: 0
  }
}

onMounted(() => {
  loadModules()
})
</script>

<style scoped>
.admin-navigation-page {
  @apply p-6;
}

.page-header {
  @apply flex items-center justify-between mb-6;
}

.page-header h1 {
  @apply text-2xl font-semibold text-gray-900;
}

.table-container {
  @apply bg-white rounded-lg shadow overflow-hidden;
}

.data-table {
  @apply w-full;
}

.data-table th {
  @apply px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50;
}

.data-table td {
  @apply px-6 py-4 whitespace-nowrap text-sm text-gray-900 border-t border-gray-200;
}

.type-badge {
  @apply px-2 py-1 text-xs font-medium rounded-full;
}

.type-badge.toolset {
  @apply bg-blue-100 text-blue-800;
}

.type-badge.page {
  @apply bg-green-100 text-green-800;
}

.btn-action {
  @apply px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-800 mr-2;
}

.btn-action.btn-danger {
  @apply text-red-600 hover:text-red-800;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.dialog-panel {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  padding: 24px;
}

.dialog-panel h2 {
  @apply text-xl font-semibold text-gray-900 mb-4;
}

.form-group {
  @apply mb-4;
}

.form-group label {
  @apply block text-sm font-medium text-gray-700 mb-1;
}

.form-input,
.form-select {
  @apply w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500;
}

.icon-input-group {
  @apply flex gap-2;
}

.btn-icon {
  @apply px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200;
}

.form-actions {
  @apply flex justify-end gap-2 mt-6;
}

.btn-primary {
  @apply px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700;
}

.btn-secondary {
  @apply px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300;
}
</style>
```

- [ ] **Step 2: 添加路由**

在 `frontend/src/router/index.ts` 中添加：

```typescript
{
  path: '/admin/navigation',
  name: 'AdminNavigation',
  component: () => import('../views/admin/AdminNavigationPage.vue'),
  meta: { requiresAuth: true, requiresAdmin: true }
}
```

- [ ] **Step 3: 提交变更**

```bash
git add frontend/src/views/admin/AdminNavigationPage.vue frontend/src/router/index.ts
git commit -m "feat: 添加导航模块管理页面"
```

---

### Task 5.4: 创建工具集管理页面

**文件:**
- Create: `frontend/src/views/admin/AdminToolsetsPage.vue`

- [ ] **Step 1: 创建工具集管理页面**

（类似导航模块管理页面，调整字段为 toolset_id, name, description, icon, order）

- [ ] **Step 2: 添加路由**

- [ ] **Step 3: 提交变更**

```bash
git add frontend/src/views/admin/AdminToolsetsPage.vue frontend/src/router/index.ts
git commit -m "feat: 添加工具集管理页面"
```

---

### Task 5.5: 创建工具分类管理页面

**文件:**
- Create: `frontend/src/views/admin/AdminToolCategoriesPage.vue`

- [ ] **Step 1: 创建工具分类管理页面**

（类似导航模块管理页面，调整字段为 toolset_id, name, icon, order）

- [ ] **Step 2: 添加路由**

- [ ] **Step 3: 提交变更**

```bash
git add frontend/src/views/admin/AdminToolCategoriesPage.vue frontend/src/router/index.ts
git commit -m "feat: 添加工具分类管理页面"
```

---

### Task 5.6: 创建 AI 工具管理页面

**文件:**
- Create: `frontend/src/views/admin/AdminAIToolsPage.vue`

- [ ] **Step 1: 创建 AI 工具管理页面**

```vue
<template>
  <div class="admin-ai-tools-page">
    <div class="page-header">
      <h1>AI 工具管理</h1>
      <button @click="showCreateDialog = true" class="btn-primary">
        新建工具
      </button>
    </div>

    <!-- 筛选器 -->
    <div class="filters">
      <select v-model="filters.toolset_id" class="filter-select" @change="loadTools">
        <option value="">全部工具集</option>
        <option v-for="ts in toolsets" :key="ts.id" :value="ts.toolset_id">
          {{ ts.name }}
        </option>
      </select>
      <select v-model="filters.visible" class="filter-select" @change="loadTools">
        <option value="">全部状态</option>
        <option value="true">可见</option>
        <option value="false">隐藏</option>
      </select>
    </div>

    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>工具ID</th>
            <th>名称</th>
            <th>工具集</th>
            <th>分类</th>
            <th>类型</th>
            <th>可见</th>
            <th>排序</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tool in tools" :key="tool.id">
            <td class="text-xs text-gray-500">{{ tool.tool_id }}</td>
            <td>{{ tool.name }}</td>
            <td>{{ tool.toolset_name }}</td>
            <td>{{ tool.category_name || '-' }}</td>
            <td>
              <span :class="['type-badge', tool.type]">
                {{ tool.type === 'media' ? '媒体' : '普通' }}
              </span>
            </td>
            <td>
              <span :class="['status-badge', { active: tool.visible }]">
                {{ tool.visible ? '可见' : '隐藏' }}
              </span>
            </td>
            <td>{{ tool.order }}</td>
            <td>
              <button @click="editTool(tool)" class="btn-action">编辑</button>
              <button @click="toggleVisibility(tool)" class="btn-action">
                {{ tool.visible ? '隐藏' : '显示' }}
              </button>
              <button @click="deleteTool(tool.id)" class="btn-action btn-danger">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 创建/编辑抽屉 -->
    <div v-if="showCreateDialog || editingTool" class="drawer-overlay" @click="closeDrawer">
      <div class="drawer-panel" @click.stop>
        <div class="drawer-header">
          <h2>{{ editingTool ? '编辑工具' : '新建工具' }}</h2>
          <button @click="closeDrawer" class="close-btn">
            <XMarkIcon class="w-6 h-6" />
          </button>
        </div>

        <div class="drawer-content">
          <form @submit.prevent="saveTool">
            <!-- 基本信息 -->
            <section class="form-section">
              <h3>基本信息</h3>
              <div class="form-row">
                <div class="form-group">
                  <label>工具ID *</label>
                  <input v-model="formData.tool_id" type="text" required class="form-input" :disabled="!!editingTool" />
                </div>
                <div class="form-group">
                  <label>工具集 *</label>
                  <select v-model="formData.toolset_id" required class="form-select" :disabled="!!editingTool">
                    <option value="">请选择</option>
                    <option v-for="ts in toolsets" :key="ts.id" :value="ts.toolset_id">
                      {{ ts.name }}
                    </option>
                  </select>
                </div>
              </div>
              <div class="form-group">
                <label>名称 *</label>
                <input v-model="formData.name" type="text" required class="form-input" />
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>图标</label>
                  <div class="icon-input-group">
                    <input v-model="formData.icon" type="text" class="form-input" placeholder="sparkles" />
                    <button type="button" @click="showIconSelector = true" class="btn-icon">选择</button>
                  </div>
                </div>
                <div class="form-group">
                  <label>分类</label>
                  <select v-model="formData.category_id" class="form-select">
                    <option value="">无分类</option>
                    <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                      {{ cat.name }}
                    </option>
                  </select>
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>模型</label>
                  <input v-model="formData.model" type="text" class="form-input" placeholder="deepseek:deepseek-chat" />
                </div>
                <div class="form-group">
                  <label>类型</label>
                  <select v-model="formData.type" class="form-select">
                    <option value="normal">普通</option>
                    <option value="media">媒体</option>
                  </select>
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>排序</label>
                  <input v-model.number="formData.order" type="number" class="form-input" />
                </div>
                <div class="form-group flex items-center">
                  <label class="checkbox-label">
                    <input v-model="formData.visible" type="checkbox" class="checkbox" />
                    <span>可见</span>
                  </label>
                </div>
              </div>
            </section>

            <!-- 描述 -->
            <section class="form-section">
              <h3>描述</h3>
              <textarea v-model="formData.description" rows="2" class="form-textarea"></textarea>
            </section>

            <!-- 欢迎消息 -->
            <section class="form-section">
              <h3>欢迎消息</h3>
              <textarea v-model="formData.welcome_message" rows="2" class="form-textarea"></textarea>
            </section>

            <!-- 系统提示词 -->
            <section class="form-section">
              <div class="section-header">
                <h3>系统提示词</h3>
                <button type="button" @click="openFullscreenEditor" class="btn-small">
                  全屏编辑
                </button>
              </div>
              <MarkdownEditor v-model="formData.system_prompt" />
            </section>

            <div class="form-actions">
              <button type="button" @click="closeDrawer" class="btn-secondary">取消</button>
              <button type="submit" class="btn-primary">保存</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 全屏编辑器 -->
    <div v-if="showFullscreenEditor" class="fullscreen-editor">
      <div class="fullscreen-header">
        <h2>编辑系统提示词</h2>
        <button @click="closeFullscreenEditor" class="btn-secondary">关闭</button>
      </div>
      <MarkdownEditor v-model="formData.system_prompt" :fullscreen="true" />
    </div>

    <!-- 图标选择器 -->
    <IconSelector v-model="formData.icon" :open="showIconSelector" @update:open="showIconSelector = $event" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import apiClient from '../../services/apiClient'
import MarkdownEditor from '../../components/editor/MarkdownEditor.vue'
import IconSelector from '../../components/editor/IconSelector.vue'

interface AITool {
  id: string
  tool_id: string
  toolset_id: string
  toolset_name: string
  category_id: string | null
  category_name: string | null
  name: string
  description: string | null
  system_prompt: string | null
  icon: string | null
  type: string
  model: string | null
  welcome_message: string | null
  visible: boolean
  order: number
}

interface Toolset {
  id: string
  toolset_id: string
  name: string
}

interface Category {
  id: string
  name: string
}

const tools = ref<AITool[]>([])
const toolsets = ref<Toolset[]>([])
const categories = ref<Category[]>([])

const filters = ref({
  toolset_id: '',
  visible: ''
})

const showCreateDialog = ref(false)
const editingTool = ref<AITool | null>(null)
const showIconSelector = ref(false)
const showFullscreenEditor = ref(false)

const formData = ref({
  tool_id: '',
  toolset_id: '',
  category_id: '',
  name: '',
  description: '',
  system_prompt: '',
  icon: '',
  type: 'normal',
  model: '',
  welcome_message: '',
  visible: true,
  order: 0
})

const loadToolsets = async () => {
  try {
    const response = await apiClient.get('/api/v1/admin/toolsets')
    toolsets.value = response.data.toolsets
  } catch (error) {
    console.error('加载工具集失败:', error)
  }
}

const loadCategories = async () => {
  try {
    const response = await apiClient.get('/api/v1/admin/tool-categories')
    categories.value = response.data.categories
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

const loadTools = async () => {
  try {
    const params: any = {}
    if (filters.value.toolset_id) params.toolset_id = filters.value.toolset_id
    if (filters.value.visible !== '') params.visible = filters.value.visible === 'true'

    const response = await apiClient.get('/api/v1/admin/ai-tools', { params })
    tools.value = response.data.tools
  } catch (error) {
    console.error('加载工具失败:', error)
  }
}

const editTool = (tool: AITool) => {
  editingTool.value = tool
  formData.value = {
    tool_id: tool.tool_id,
    toolset_id: tool.toolset_id,
    category_id: tool.category_id || '',
    name: tool.name,
    description: tool.description || '',
    system_prompt: tool.system_prompt || '',
    icon: tool.icon || '',
    type: tool.type,
    model: tool.model || '',
    welcome_message: tool.welcome_message || '',
    visible: tool.visible,
    order: tool.order
  }
}

const saveTool = async () => {
  try {
    if (editingTool.value) {
      await apiClient.put(`/api/v1/admin/ai-tools/${formData.value.tool_id}`, formData.value)
    } else {
      await apiClient.post('/api/v1/admin/ai-tools', formData.value)
    }
    closeDrawer()
    await loadTools()
  } catch (error) {
    console.error('保存失败:', error)
    alert('保存失败: ' + (error.response?.data?.detail || '请重试'))
  }
}

const toggleVisibility = async (tool: AITool) => {
  try {
    await apiClient.patch(`/api/v1/admin/ai-tools/${tool.tool_id}/toggle`)
    await loadTools()
  } catch (error) {
    console.error('切换状态失败:', error)
  }
}

const deleteTool = async (id: string) => {
  if (!confirm('确定要删除此工具吗？')) return

  try {
    await apiClient.delete(`/api/v1/admin/ai-tools/${id}`)
    await loadTools()
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败，请重试')
  }
}

const closeDrawer = () => {
  showCreateDialog.value = false
  editingTool.value = null
  formData.value = {
    tool_id: '',
    toolset_id: '',
    category_id: '',
    name: '',
    description: '',
    system_prompt: '',
    icon: '',
    type: 'normal',
    model: '',
    welcome_message: '',
    visible: true,
    order: 0
  }
}

const openFullscreenEditor = () => {
  showFullscreenEditor.value = true
}

const closeFullscreenEditor = () => {
  showFullscreenEditor.value = false
}

onMounted(() => {
  loadToolsets()
  loadCategories()
  loadTools()
})
</script>

<style scoped>
.admin-ai-tools-page {
  @apply p-6;
}

.page-header {
  @apply flex items-center justify-between mb-6;
}

.page-header h1 {
  @apply text-2xl font-semibold text-gray-900;
}

.filters {
  @apply flex gap-4 mb-6;
}

.filter-select {
  @apply px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500;
}

.table-container {
  @apply bg-white rounded-lg shadow overflow-hidden;
}

.data-table {
  @apply w-full;
}

.data-table th {
  @apply px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50;
}

.data-table td {
  @apply px-4 py-3 text-sm text-gray-900 border-t border-gray-200;
}

.type-badge {
  @apply px-2 py-1 text-xs font-medium rounded-full;
}

.type-badge.normal {
  @apply bg-gray-100 text-gray-800;
}

.type-badge.media {
  @apply bg-purple-100 text-purple-800;
}

.status-badge {
  @apply px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-600;
}

.status-badge.active {
  @apply bg-green-100 text-green-700;
}

.btn-action {
  @apply px-2 py-1 text-sm font-medium text-blue-600 hover:text-blue-800 mr-1;
}

.btn-action.btn-danger {
  @apply text-red-600 hover:text-red-800;
}

.drawer-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 9999;
}

.drawer-panel {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 600px;
  max-width: 90vw;
  background: white;
  display: flex;
  flex-direction: column;
}

.drawer-header {
  @apply flex items-center justify-between px-6 py-4 border-b border-gray-200;
}

.drawer-header h2 {
  @apply text-xl font-semibold text-gray-900;
}

.drawer-content {
  @apply flex-1 overflow-y-auto p-6;
}

.form-section {
  @apply mb-6 pb-6 border-b border-gray-200;
}

.form-section:last-child {
  @apply border-b-0;
}

.form-section h3 {
  @apply text-sm font-semibold text-gray-900 mb-4;
}

.section-header {
  @apply flex items-center justify-between mb-4;
}

.form-row {
  @apply flex gap-4;
}

.form-row .form-group {
  @apply flex-1;
}

.form-group {
  @apply mb-4;
}

.form-group label {
  @apply block text-sm font-medium text-gray-700 mb-1;
}

.form-input,
.form-select,
.form-textarea {
  @apply w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500;
}

.icon-input-group {
  @apply flex gap-2;
}

.btn-icon {
  @apply px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200;
}

.checkbox-label {
  @apply flex items-center gap-2 cursor-pointer;
}

.checkbox {
  @apply w-4 h-4 text-blue-600 rounded focus:ring-blue-500;
}

.form-actions {
  @apply flex justify-end gap-2 pt-4;
}

.btn-primary {
  @apply px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700;
}

.btn-secondary {
  @apply px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300;
}

.btn-small {
  @apply px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200;
}

.fullscreen-editor {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: white;
  z-index: 10000;
  display: flex;
  flex-direction: column;
}

.fullscreen-header {
  @apply flex items-center justify-between px-6 py-4 border-b border-gray-200;
}

@media (max-width: 768px) {
  .drawer-panel {
    width: 100%;
    max-width: 100%;
  }

  .form-row {
    @apply flex-col gap-2;
  }
}
</style>
```

- [ ] **Step 2: 添加路由**

- [ ] **Step 3: 提交变更**

```bash
git add frontend/src/views/admin/AdminAIToolsPage.vue frontend/src/router/index.ts
git commit -m "feat: 添加 AI 工具管理页面"
```

---

## Phase 6: 测试验证

### Task 6.1: 后端集成测试

**文件:**
- Create: `backend/tests/integration/test_config_api.py`

- [ ] **Step 1: 创建配置 API 测试**

```python
# -*- coding: utf-8 -*-
"""配置管理 API 集成测试"""
import pytest
from fastapi.testclient import TestClient


def test_get_navigation_modules_as_admin(client: TestClient, admin_token_headers):
    """测试获取导航模块列表（管理员）"""
    response = client.get("/api/v1/admin/navigation/modules", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "modules" in data
    assert len(data["modules"]) > 0


def test_get_navigation_modules_as_user(client: TestClient, user_token_headers):
    """测试获取导航模块列表（普通用户应被拒绝）"""
    response = client.get("/api/v1/admin/navigation/modules", headers=user_token_headers)
    assert response.status_code == 403


def test_create_navigation_module(client: TestClient, admin_token_headers):
    """测试创建导航模块"""
    request_data = {
        "name": "测试模块",
        "type": "page",
        "page_path": "/test",
        "icon": "sparkles",
        "order": 99
    }
    response = client.post("/api/v1/admin/navigation/modules", json=request_data, headers=admin_token_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "测试模块"


def test_get_ai_tools(client: TestClient, admin_token_headers):
    """测试获取 AI 工具列表"""
    response = client.get("/api/v1/admin/ai-tools", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert "total" in data


def test_existing_tools_api_still_works(client: TestClient, user_token_headers):
    """测试现有工具 API 仍然工作"""
    response = client.get("/api/v1/tools", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data


def test_existing_navigation_api_still_works(client: TestClient, user_token_headers):
    """测试现有导航 API 仍然工作"""
    response = client.get("/api/v1/navigation", headers=user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "modules" in data
```

- [ ] **Step 2: 运行测试**

```bash
cd backend
pytest tests/integration/test_config_api.py -v
```

- [ ] **Step 3: 提交变更**

```bash
git add backend/tests/integration/test_config_api.py
git commit -m "test: 添加配置管理 API 集成测试"
```

---

### Task 6.2: 端到端测试

**文件:**
- Create: `frontend/tests/e2e/admin-config.spec.ts`

- [ ] **Step 1: 创建 E2E 测试**

```typescript
import { test, expect } from '@playwright/test'

test.describe('后台配置管理', () => {
  test.beforeEach(async ({ page }) => {
    // 登录管理员账号
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('/modules/ai_tools')
  })

  test('导航模块管理页面可访问', async ({ page }) => {
    await page.goto('/admin/navigation')
    await expect(page.locator('h1')).toContainText('导航模块管理')
    await expect(page.locator('.data-table')).toBeVisible()
  })

  test('AI 工具管理页面可访问', async ({ page }) => {
    await page.goto('/admin/ai-tools')
    await expect(page.locator('h1')).toContainText('AI 工具管理')
    await expect(page.locator('.data-table')).toBeVisible()
  })

  test('创建新 AI 工具', async ({ page }) => {
    await page.goto('/admin/ai-tools')
    await page.click('button:has-text("新建工具")')

    // 填写表单
    await page.fill('input[name="tool_id"]', 'test_tool_e2e')
    await page.selectOption('select[name="toolset_id"]', 'ai_tools')
    await page.fill('input[name="name"]', 'E2E 测试工具')
    await page.fill('textarea[name="description"]', '这是 E2E 测试创建的工具')

    // 保存
    await page.click('button[type="submit"]')

    // 验证
    await expect(page.locator('text=E2E 测试工具')).toBeVisible()
  })

  test('现有工具列表 API 仍然工作', async ({ page, request }) => {
    // 测试 API
    const response = await request.get('/api/v1/tools', {
      headers: {
        Authorization: `Bearer ${await page.evaluate(() => localStorage.getItem('token'))}`
      }
    })
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data).toHaveProperty('categories')
  })
})
```

- [ ] **Step 2: 运行 E2E 测试**

```bash
cd frontend
npm run test:e2e -- tests/e2e/admin-config.spec.ts --project=chromium
```

- [ ] **Step 3: 提交变更**

```bash
git add frontend/tests/e2e/admin-config.spec.ts
git commit -m "test: 添加后台配置管理 E2E 测试"
```

---

## 验收检查清单

在标记任务完成前，确保以下所有项目都通过：

- [ ] 所有 YAML 配置成功导入数据库
  - 运行 `migrate_yaml_to_db.py` 无错误
  - 数据库中有正确的数据

- [ ] 现有业务 API 功能正常
  - `/api/v1/tools` 返回正确数据
  - `/api/v1/navigation` 返回正确数据
  - 聊天功能正常工作

- [ ] 前端用户界面无变化
  - 工具选择器显示正常
  - 聊天界面正常工作

- [ ] 后台管理页面可增删改查配置
  - 导航模块管理页面正常
  - 工具集管理页面正常
  - 工具分类管理页面正常
  - AI 工具管理页面正常

- [ ] Markdown 编辑器正常工作
  - 实时预览正常
  - 全屏模式正常
  - 不影响原有 MarkdownEditorView

- [ ] 图标选择器正常工作
  - 可以搜索图标
  - 可以选择图标
  - 可以清除选择

- [ ] 数据迁移脚本可重复执行
  - 多次运行不会重复插入数据

- [ ] 回滚机制可用
  - 删除数据库数据后可以重新运行迁移

---

## 实施注意事项

1. **API 兼容性**: 确保所有现有 API 端点的响应格式完全不变
2. **权限检查**: 所有后台管理 API 都需要验证管理员权限
3. **数据验证**: 创建和更新操作需要验证数据有效性（如 tool_id 唯一性）
4. **级联删除**: 删除工具集时，相关的分类和工具应该被级联删除
5. **错误处理**: 提供清晰的错误消息，特别是中文错误提示
6. **前端组件复用**: MarkdownEditor 组件不应破坏原有功能
