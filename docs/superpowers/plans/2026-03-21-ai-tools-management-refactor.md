# AI 工具管理架构重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 简化 AI 工具管理架构，删除 toolsets 表，合并到 navigation_modules，实现统一的数据库驱动管理

**架构：**
- 删除 `toolsets` 表，将 `ai_tool_categories` 和 `ai_tools` 的外键从 `toolset_id` 改为 `navigation_module_id`
- 后台管理界面简化为"导航模块管理"和"AI工具管理"两个菜单
- 前端 API 路径从 `/toolsets/{toolset_id}/tools` 改为 `/navigation-modules/{module_id}/tools`

**技术栈：**
- 后端：FastAPI + SQLAlchemy + Alembic + MySQL
- 前端：Vue 3 + TypeScript + Element Plus + Pinia

---

## 文件结构

### 创建的文件
- `backend/alembic/versions/YYYYMMDD_HHMMSS_merge_toolsets_to_navigation_modules.py` - 数据库迁移脚本
- `backend/src/interfaces/routers/admin/navigation_categories.py` - 导航模块分类管理路由（新建）
- `frontend/src/views/admin/AdminNavigationModulesPage.vue` - 替换现有的 AdminNavigationPage.vue

### 修改的文件
- `backend/src/db_models.py` - 修改 NavigationModuleModel, AIToolCategoryModel, AIToolModel
- `backend/src/models.py` - 更新 Pydantic 模型
- `backend/src/interfaces/routers/navigation.py` - 更新前端用户 API
- `backend/src/interfaces/routers/admin/navigation.py` - 增强导航模块管理 API
- `backend/src/interfaces/routers/admin/ai_tools.py` - 更新 AI 工具 API
- `backend/src/main.py` - 路由注册
- `frontend/src/services/apiClient.ts` - 更新 API 调用
- `frontend/src/stores/navigationStore.ts` - 更新状态管理
- `frontend/src/views/admin/AdminAIToolsPage.vue` - 更新 AI 工具管理页面
- `frontend/src/views/admin/AdminLayout.vue` - 删除菜单项
- `frontend/src/router/index.ts` - 删除路由
- `frontend/src/types/index.ts` - 更新类型定义

### 删除的文件
- `backend/src/interfaces/routers/admin/toolsets.py` - 工具集管理路由
- `backend/src/interfaces/routers/admin/ai_tool_categories.py` - AI工具分类管理路由
- `frontend/src/views/admin/AdminToolsetsPage.vue` - 工具集管理页面
- `frontend/src/views/admin/AdminAIToolCategoriesPage.vue` - AI工具分类管理页面

---

## 第一阶段：数据库迁移

### Task 1: 创建 Alembic 迁移脚本

**Files:**
- Create: `backend/alembic/versions/{timestamp}_merge_toolsets_to_navigation_modules.py`

- [ ] **Step 1: 检查当前数据库版本**

运行: `cd backend && alembic current`
预期: 显示当前数据库版本，应该是 `705c676a8b9f` 或更新版本

- [ ] **Step 2: 备份数据库**

运行: `mysqldump -u root -p ai_teacher_platform > backup_before_migration.sql`
预期: 创建备份文件

- [ ] **Step 3: 生成迁移模板**

运行: `cd backend && alembic revision -m "merge_toolsets_to_navigation_modules"`
预期: 生成新的迁移文件

- [ ] **Step 4: 编写迁移脚本**

编辑生成的迁移文件，内容如下：

```python
# merge_toolsets_to_navigation_modules.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, select

# revision identifiers, used by Alembic.
revision = '0010_merge_toolsets'
down_revision = '705c676a8b9f'  # 最新迁移的 ID
branch_labels = None
depends_on = None


def upgrade():
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


def downgrade():
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
```

- [ ] **Step 3: 提交迁移脚本**

```bash
git add backend/alembic/versions/
git commit -m "feat: 添加 toolsets 合并到 navigation_modules 的迁移脚本"
```

---

## 第二阶段：数据模型修改

### Task 2: 修改 db_models.py

**Files:**
- Modify: `backend/src/db_models.py`

- [ ] **Step 1: 修改 NavigationModuleType 枚举**

找到 `class NavigationModuleType(enum.Enum)`，将 `toolset = "toolset"` 改为 `ai_tools = "ai_tools"`

```python
class NavigationModuleType(enum.Enum):
    """导航模块类型枚举"""
    ai_tools = "ai_tools"  # 修改：toolset -> ai_tools
    page = "page"
```

- [ ] **Step 2: 修改 NavigationModuleModel 添加关系**

在 `class NavigationModuleModel` 中添加 categories 和 tools 关系：

```python
class NavigationModuleModel(Base):
    """导航模块数据库模型"""
    __tablename__ = "navigation_modules"

    # ... 现有字段保持不变 ...

    # 新增：关系到分类和工具
    categories = relationship("AIToolCategoryModel",
                             back_populates="navigation_module",
                             cascade="all, delete-orphan",
                             foreign_keys="AIToolCategoryModel.navigation_module_id")

    tools = relationship("AIToolModel",
                        back_populates="navigation_module",
                        cascade="all, delete-orphan",
                        foreign_keys="AIToolModel.navigation_module_id")
```

- [ ] **Step 3: 修改 AIToolCategoryModel**

找到 `class AIToolCategoryModel`，将 `toolset_id` 改为 `navigation_module_id`：

```python
class AIToolCategoryModel(Base):
    """AI工具分类数据库模型"""
    __tablename__ = "ai_tool_categories"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # 修改：toolset_id -> navigation_module_id
    navigation_module_id = Column(CHAR(36),
                                  ForeignKey("navigation_modules.id", ondelete="CASCADE"),
                                  nullable=False, index=True)
    name = Column(String(50), nullable=False)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 修改：关系
    navigation_module = relationship("NavigationModuleModel", back_populates="categories")
    tools = relationship("AIToolModel", back_populates="category")
```

- [ ] **Step 4: 修改 AIToolModel**

找到 `class AIToolModel`，将 `toolset_id` 改为 `navigation_module_id`：

```python
class AIToolModel(Base):
    """AI工具数据库模型"""
    __tablename__ = "ai_tools"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String(50), unique=True, nullable=False, index=True)
    # 修改：toolset_id -> navigation_module_id
    navigation_module_id = Column(CHAR(36),
                                  ForeignKey("navigation_modules.id", ondelete="CASCADE"),
                                  nullable=False, index=True)
    category_id = Column(CHAR(36), ForeignKey("ai_tool_categories.id", ondelete="SET NULL"), nullable=True)
    # ... 其他字段保持不变 ...

    # 修改：关系
    navigation_module = relationship("NavigationModuleModel", back_populates="tools")
    category = relationship("AIToolCategoryModel", back_populates="tools")

    # 修改：联合索引
    __table_args__ = (
        Index("idx_ai_tool_navigation_module_order", "navigation_module_id", "order"),
        Index("idx_ai_tool_category_order", "category_id", "order"),
    )
```

- [ ] **Step 5: 删除 ToolsetModel**

删除整个 `class ToolsetModel` 定义

- [ ] **Step 6: 运行后端测试验证**

运行: `cd backend && python -m pytest tests/ -v -x`
预期: 测试通过（部分测试可能需要后续更新）

- [ ] **Step 7: 提交**

```bash
git add backend/src/db_models.py
git commit -m "refactor: 修改数据模型，合并 toolsets 到 navigation_modules"
```

---

### Task 3: 更新 Pydantic 模型

**Files:**
- Modify: `backend/src/models.py`

- [ ] **Step 1: 更新 NavigationModule 类型**

找到 `NavigationModule` 类，更新 type 字段的类型：

```python
class NavigationModule(BaseModel):
    """导航模块配置（用于顶部导航栏）"""
    name: str = Field(..., description="模块显示名称")
    type: Literal["ai_tools", "page"] = Field(..., description="模块类型：ai_tools=AI工具，page=独立页面")  # 修改
    # ... 其他字段保持不变 ...
```

- [ ] **Step 2: 更新 Tool 类**

找到 `Tool` 类，将 `toolset_id` 改为 `navigation_module_id`：

```python
class Tool(BaseModel):
    """工具配置实体（聚合根）"""
    tool_id: str = Field(..., description="工具唯一标识符")
    name: str = Field(..., description="工具名称")
    description: Optional[str] = Field(None, description="工具描述")
    # ... 其他字段 ...
    navigation_module_id: str = Field("ai_tools", description="所属导航模块ID")  # 修改
    # ... 其他字段保持不变 ...
```

- [ ] **Step 3: 删除 Toolset 相关模型**

删除以下类（如果存在）：
- `AdminToolsetListItem`
- `CreateToolsetRequest`
- `UpdateToolsetRequest`
- `AdminToolsetListResponse`
- `CreateToolsetResponse`
- `UpdateToolsetResponse`
- `MoveToolsetResponse`

- [ ] **Step 4: 添加导航模块分类相关模型**

在适当位置添加：

```python
# ========== 导航模块分类管理 ==========

class AdminNavigationModuleCategoryListItem(BaseModel):
    """导航模块分类列表项"""
    id: str = Field(..., description="分类ID")
    navigation_module_id: str = Field(..., description="所属导航模块ID")
    navigation_module_name: str = Field(..., description="导航模块名称")
    name: str = Field(..., description="分类名称")
    icon: Optional[str] = Field(None, description="图标")
    order: int = Field(..., description="排序")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class AdminNavigationModuleCategoryListResponse(BaseModel):
    """导航模块分类列表响应"""
    categories: List[AdminNavigationModuleCategoryListItem]


class CreateNavigationModuleCategoryRequest(BaseModel):
    """创建导航模块分类请求"""
    navigation_module_id: str = Field(..., description="所属导航模块ID")
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    icon: Optional[str] = Field(None, max_length=50, description="图标")
    order: int = Field(0, ge=0, description="排序")


class CreateNavigationModuleCategoryResponse(BaseModel):
    """创建导航模块分类响应"""
    id: str = Field(..., description="分类ID")
    message: str = Field(..., description="响应消息")


class UpdateNavigationModuleCategoryRequest(BaseModel):
    """更新导航模块分类请求"""
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    icon: Optional[str] = Field(None, max_length=50, description="图标")
    order: int = Field(..., ge=0, description="排序")


class UpdateNavigationModuleCategoryResponse(BaseModel):
    """更新导航模块分类响应"""
    id: str = Field(..., description="分类ID")
    message: str = Field(..., description="响应消息")
```

- [ ] **Step 5: 更新 AITool 相关模型**

修改 `AdminAIToolListItem`、`CreateAIToolRequest` 等：

```python
class AdminAIToolListItem(BaseModel):
    """AI工具列表项"""
    id: str = Field(..., description="工具ID")
    tool_id: str = Field(..., description="工具标识符")
    navigation_module_id: str = Field(..., description="所属导航模块ID")  # 修改
    navigation_module_name: str = Field(..., description="导航模块名称")  # 新增
    category_id: Optional[str] = Field(None, description="分类ID")
    category_name: Optional[str] = Field(None, description="分类名称")
    # ... 其他字段 ...


class CreateAIToolRequest(BaseModel):
    """创建AI工具请求"""
    tool_id: str = Field(..., pattern=r'^[a-z0-9_]+$', description="工具标识符")
    navigation_module_id: str = Field(..., description="所属导航模块ID")  # 修改
    category_id: str = Field(..., description="分类ID（必选）")  # 修改为必选
    # ... 其他字段 ...


class UpdateAIToolRequest(BaseModel):
    """更新AI工具请求"""
    navigation_module_id: str = Field(..., description="所属导航模块ID")  # 修改
    category_id: str = Field(..., description="分类ID（必选）")  # 修改为必选
    # ... 其他字段 ...
```

- [ ] **Step 6: 提交**

```bash
git add backend/src/models.py
git commit -m "refactor: 更新 Pydantic 模型，toolset -> navigation_module"
```

---

## 第三阶段：后端 API 改造

### Task 4: 修改前端用户 API

**Files:**
- Modify: `backend/src/interfaces/routers/navigation.py`
- Modify: `backend/src/interfaces/routers/tools/list.py`

**说明：** 本次重构将完全废弃从 YAML 配置文件读取数据的方式，`ConfigService` 将不再被前端用户 API 使用。所有数据改为从数据库读取。

- [ ] **Step 1: 更新 navigation.py**

修改返回的 type 枚举值：

```python
# navigation.py
# 在 _model_to_response 函数中，确保返回 "ai_tools" 而不是 "toolset"
def _model_to_response(model: NavigationModuleModel) -> NavigationModule:
    return NavigationModule(
        name=model.name,
        type="ai_tools" if model.type.value == "toolset" else model.type.value,  # 兼容处理
        # ...
    )
```

- [ ] **Step 2: 创建新的工具列表路由**

修改 `backend/src/interfaces/routers/tools/list.py`，将 `/toolsets/{toolset_id}/tools` 改为 `/navigation-modules/{module_id}/tools`：

```python
# list.py
@router.get("/navigation-modules/{module_id}/tools", response_model=ToolListResponse, tags=["工具"])
async def get_navigation_module_tools(
    module_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定导航模块的工具列表

    Args:
        module_id: 导航模块ID

    Returns:
        该模块的工具列表，按分类组织
    """
    from src.db_models import NavigationModuleModel, AIToolModel, AIToolCategoryModel

    # 查找导航模块
    nav_module = db.query(NavigationModuleModel).filter(
        NavigationModuleModel.id == module_id
    ).first()

    if not nav_module:
        raise HTTPException(status_code=404, detail="导航模块不存在")

    # 查询该模块下的工具
    tools = db.query(AIToolModel).filter(
        AIToolModel.navigation_module_id == module_id,
        AIToolModel.visible == True
    ).order_by(AIToolModel.order).all()

    # 查询分类
    categories = db.query(AIToolCategoryModel).filter(
        AIToolCategoryModel.navigation_module_id == module_id
    ).order_by(AIToolCategoryModel.order).all()

    # 构建分类字典
    categories_dict = {cat.id: cat for cat in categories}

    # 按分类聚合工具
    category_groups = {}
    for tool in tools:
        cat_id = tool.category_id or "uncategorized"
        if cat_id not in category_groups:
            if cat_id == "uncategorized":
                category_groups[cat_id] = {
                    'name': '未分类',
                    'icon': None,
                    'tools': []
                }
            elif cat_id in categories_dict:
                category_groups[cat_id] = {
                    'name': categories_dict[cat_id].name,
                    'icon': categories_dict[cat_id].icon,
                    'tools': []
                }

        category_groups[cat_id]['tools'].append({
            'tool_id': tool.tool_id,
            'name': tool.name,
            'description': tool.description,
            'icon': tool.icon,
            'category': categories_dict[tool.category_id].name if tool.category_id in categories_dict else '',
            'visible': tool.visible,
            'type': tool.type.value,
            'welcome_message': tool.welcome_message,
            'navigation_module_id': str(tool.navigation_module_id),  # 修改
            'model': tool.model,
            'content_type': tool.content_type,
            'media_type': tool.media_type,
        })

    # 转换为列表并排序
    result_list = []
    for cat in categories:
        if str(cat.id) in category_groups:
            result_list.append(category_groups[str(cat.id)])

    return ToolListResponse(categories=result_list)


@router.get("/navigation-modules/tools", response_model=ToolListResponse, tags=["工具"])
async def get_all_tools(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有导航模块的工具列表"""
    from src.db_models import AIToolModel, AIToolCategoryModel, NavigationModuleModel

    tools = db.query(AIToolModel).filter(
        AIToolModel.visible == True
    ).all()

    categories = db.query(AIToolCategoryModel).all()
    nav_modules = db.query(NavigationModuleModel).all()

    # 构建字典
    categories_dict = {cat.id: cat for cat in categories}
    nav_modules_dict = {nav.id: nav for nav in nav_modules}

    # 按分类聚合
    category_groups = {}
    for tool in tools:
        cat_id = tool.category_id or "uncategorized"
        if cat_id not in category_groups:
            if cat_id == "uncategorized":
                category_groups[cat_id] = {
                    'name': '未分类',
                    'icon': None,
                    'tools': []
                }
            elif cat_id in categories_dict:
                category_groups[cat_id] = {
                    'name': categories_dict[cat_id].name,
                    'icon': categories_dict[cat_id].icon,
                    'tools': []
                }

        category_groups[cat_id]['tools'].append({
            'tool_id': tool.tool_id,
            'name': tool.name,
            'description': tool.description,
            'icon': tool.icon,
            'category': categories_dict[tool.category_id].name if tool.category_id in categories_dict else '',
            'visible': tool.visible,
            'type': tool.type.value,
            'welcome_message': tool.welcome_message,
            'navigation_module_id': str(tool.navigation_module_id),
            'model': tool.model,
            'content_type': tool.content_type,
            'media_type': tool.media_type,
        })

    result_list = list(category_groups.values())
    result_list.sort(key=lambda x: x.get('order', 999))

    return ToolListResponse(categories=result_list)
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/interfaces/routers/navigation.py backend/src/interfaces/routers/tools/list.py
git commit -m "refactor: 更新前端用户 API，toolset -> navigation_module"
```

---

### Task 5: 创建导航模块分类管理路由

**Files:**
- Create: `backend/src/interfaces/routers/admin/navigation_categories.py`

- [ ] **Step 1: 创建导航模块分类管理路由文件**

创建新文件 `backend/src/interfaces/routers/admin/navigation_categories.py`：

```python
# -*- coding: utf-8 -*-
"""导航模块分类管理路由

提供导航模块下分类的管理接口
"""
import logging
from typing import Annotated, List
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from src.models import (
    UserInfo,
    AdminNavigationModuleCategoryListResponse,
    AdminNavigationModuleCategoryListItem,
    CreateNavigationModuleCategoryRequest,
    CreateNavigationModuleCategoryResponse,
    UpdateNavigationModuleCategoryRequest,
    UpdateNavigationModuleCategoryResponse,
)
from src.db_models import (
    NavigationModuleModel,
    AIToolCategoryModel,
)
from src.database import get_db
from src.interfaces.dependencies import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["管理员-导航模块分类"])


def _model_to_response(model: AIToolCategoryModel, nav_module: NavigationModuleModel) -> AdminNavigationModuleCategoryListItem:
    """将数据库模型转换为响应模型"""
    return AdminNavigationModuleCategoryListItem(
        id=str(model.id),
        navigation_module_id=str(model.navigation_module_id),
        navigation_module_name=nav_module.name,
        name=model.name,
        icon=model.icon,
        order=model.order,
        created_at=model.created_at.isoformat(),
        updated_at=model.updated_at.isoformat(),
    )


@router.get("/navigation-modules/{module_id}/categories", response_model=AdminNavigationModuleCategoryListResponse)
async def get_categories(
    module_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取导航模块的分类列表"""
    try:
        # 验证导航模块存在
        nav_module = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.id == module_id
        ).first()
        if not nav_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="导航模块不存在"
            )

        categories = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.navigation_module_id == module_id
        ).order_by(AIToolCategoryModel.order).all()

        return AdminNavigationModuleCategoryListResponse(
            categories=[_model_to_response(c, nav_module) for c in categories]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分类列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/navigation-modules/{module_id}/categories",
             response_model=CreateNavigationModuleCategoryResponse,
             status_code=status.HTTP_201_CREATED)
async def create_category(
    module_id: str,
    request: CreateNavigationModuleCategoryRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建导航模块分类"""
    try:
        # 验证导航模块存在且类型为 ai_tools
        nav_module = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.id == module_id
        ).first()
        if not nav_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="导航模块不存在"
            )
        if nav_module.type.value != "ai_tools" and nav_module.type.value != "toolset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有AI工具类型的导航模块才能创建分类"
            )

        # 检查名称是否重复
        existing = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.navigation_module_id == module_id,
            AIToolCategoryModel.name == request.name
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"分类名称 '{request.name}' 已存在"
            )

        # 创建分类
        db_category = AIToolCategoryModel(
            id=str(uuid.uuid4()),
            navigation_module_id=module_id,
            name=request.name,
            icon=request.icon,
            order=request.order,
        )
        db.add(db_category)
        db.commit()

        return CreateNavigationModuleCategoryResponse(
            id=str(db_category.id),
            message="创建分类成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建分类失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/navigation-modules/{module_id}/categories/{category_id}",
            response_model=UpdateNavigationModuleCategoryResponse)
async def update_category(
    module_id: str,
    category_id: str,
    request: UpdateNavigationModuleCategoryRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新导航模块分类"""
    try:
        category = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.id == category_id,
            AIToolCategoryModel.navigation_module_id == module_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类不存在"
            )

        # 检查名称是否重复
        existing = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.navigation_module_id == module_id,
            AIToolCategoryModel.name == request.name,
            AIToolCategoryModel.id != category_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"分类名称 '{request.name}' 已存在"
            )

        category.name = request.name
        category.icon = request.icon
        category.order = request.order
        category.updated_at = datetime.now()
        db.commit()

        return UpdateNavigationModuleCategoryResponse(
            id=str(category.id),
            message="更新分类成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新分类失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/navigation-modules/{module_id}/categories/{category_id}",
               status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    module_id: str,
    category_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除导航模块分类"""
    try:
        category = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.id == category_id,
            AIToolCategoryModel.navigation_module_id == module_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类不存在"
            )

        db.delete(category)
        db.commit()

        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除分类失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

- [ ] **Step 2: 注册路由**

修改 `backend/src/main.py`，添加新路由：

```python
# main.py
from src.interfaces.routers.admin import navigation_categories as new_admin_nav_categories_router

# 在路由注册部分添加
app.include_router(new_admin_nav_categories_router.router)
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/interfaces/routers/admin/navigation_categories.py backend/src/main.py
git commit -m "feat: 添加导航模块分类管理路由"
```

---

### Task 6: 更新导航模块管理路由

**Files:**
- Modify: `backend/src/interfaces/routers/admin/navigation.py`

- [ ] **Step 1: 更新类型枚举处理**

修改 `backend/src/interfaces/routers/admin/navigation.py` 中的类型处理：

```python
# navigation.py
# 在验证部分，更新类型检查
if request.type == "ai_tools" and not request.config_source:  # 修改：toolset -> ai_tools
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="ai_tools类型必须指定config_source"
    )
```

- [ ] **Step 2: 更新响应类型**

确保返回的 type 值为 "ai_tools"：

```python
def _model_to_response(model: NavigationModuleModel) -> AdminNavigationModuleListItem:
    type_value = model.type.value
    # 兼容处理：如果是 toolset，返回 ai_tools
    if type_value == "toolset":
        type_value = "ai_tools"
    return AdminNavigationModuleListItem(
        id=str(model.id),
        name=model.name,
        type=type_value,
        # ...
    )
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/interfaces/routers/admin/navigation.py
git commit -m "refactor: 更新导航模块管理路由类型枚举"
```

---

### Task 7: 更新 AI 工具管理路由

**Files:**
- Modify: `backend/src/interfaces/routers/admin/ai_tools.py`

- [ ] **Step 1: 更新工具列表查询**

修改查询逻辑，从 `toolset_id` 改为 `navigation_module_id`：

```python
# ai_tools.py
@router.get("/ai-tools", response_model=AdminAIToolListResponse)
async def get_ai_tools(
    navigation_module_id: Optional[str] = None,  # 修改：toolset_id -> navigation_module_id
    category_id: Optional[str] = None,
    visible: Optional[bool] = None,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取AI工具列表"""
    try:
        query = db.query(AIToolModel)

        if navigation_module_id:
            # 修改：使用 navigation_module_id
            query = query.filter(AIToolModel.navigation_module_id == navigation_module_id)

        if category_id:
            query = query.filter(AIToolModel.category_id == category_id)

        if visible is not None:
            query = query.filter(AIToolModel.visible == visible)

        tools = query.order_by(AIToolModel.order).all()

        # 构建响应，包含导航模块名称
        result = []
        for tool in tools:
            nav_module = db.query(NavigationModuleModel).filter(
                NavigationModuleModel.id == tool.navigation_module_id
            ).first()
            category = db.query(AIToolCategoryModel).filter(
                AIToolCategoryModel.id == tool.category_id
            ).first() if tool.category_id else None

            result.append(AdminAIToolListItem(
                id=str(tool.id),
                tool_id=tool.tool_id,
                navigation_module_id=str(tool.navigation_module_id),
                navigation_module_name=nav_module.name if nav_module else "",
                category_id=str(tool.category_id) if tool.category_id else None,
                category_name=category.name if category else None,
                # ... 其他字段 ...
            ))

        return AdminAIToolListResponse(tools=result)
    except Exception as e:
        logger.error(f"获取AI工具列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 2: 更新创建工具**

```python
@router.post("/ai-tools", response_model=CreateAIToolResponse, status_code=201)
async def create_ai_tool(
    request: CreateAIToolRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建AI工具"""
    try:
        # 验证导航模块存在
        nav_module = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.id == request.navigation_module_id  # 修改
        ).first()
        if not nav_module:
            raise HTTPException(status_code=404, detail="导航模块不存在")

        # 验证分类存在且属于该导航模块
        category = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.id == request.category_id,
            AIToolCategoryModel.navigation_module_id == request.navigation_module_id  # 新增验证
        ).first()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在或不属于该导航模块")

        # 创建工具
        db_tool = AIToolModel(
            tool_id=request.tool_id,
            navigation_module_id=request.navigation_module_id,  # 修改
            category_id=request.category_id,
            # ... 其他字段 ...
        )
        db.add(db_tool)
        db.commit()

        return CreateAIToolResponse(
            id=str(db_tool.id),
            message="创建工具成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建AI工具失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 3: 更新其他方法**

类似地更新 update、delete、move_up、move_down 等方法

- [ ] **Step 4: 提交**

```bash
git add backend/src/interfaces/routers/admin/ai_tools.py
git commit -m "refactor: 更新AI工具管理路由，toolset -> navigation_module"
```

---

### Task 8: 删除旧的路由文件

**Files:**
- Delete: `backend/src/interfaces/routers/admin/toolsets.py`
- Delete: `backend/src/interfaces/routers/admin/ai_tool_categories.py`
- Modify: `backend/src/main.py`

- [ ] **Step 1: 删除路由文件**

```bash
rm backend/src/interfaces/routers/admin/toolsets.py
rm backend/src/interfaces/routers/admin/ai_tool_categories.py
```

- [ ] **Step 2: 更新 main.py 删除路由注册**

修改 `backend/src/main.py`，删除以下行：

```python
# 删除这些行
from src.interfaces.routers.admin import toolsets as new_admin_toolsets_router
from src.interfaces.routers.admin import ai_tool_categories as new_admin_ai_categories_router

app.include_router(new_admin_toolsets_router.router)
app.include_router(new_admin_ai_categories_router.router)
```

同时清理 main.py 中与这些路由相关的注释（约第 88-129 行），删除所有提及 `toolsets` 或 `ai_tool_categories` 路由迁移的注释。

- [ ] **Step 3: 清理 main.py 中的遗留注释**

检查 main.py，删除所有与已删除路由相关的注释行。

- [ ] **Step 4: 运行后端测试**

运行: `cd backend && python -m pytest tests/ -v -x`
预期: 测试通过（部分测试可能需要更新）

- [ ] **Step 5: 提交**

```bash
git add backend/src/interfaces/routers/admin/ backend/src/main.py
git commit -m "refactor: 删除 toolsets 和 ai_tool_categories 管理路由"
```

---

## 第四阶段：前端改造

### Task 9: 更新前端类型定义

**Files:**
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: 更新 NavigationModule 类型**

```typescript
// types/index.ts
export type ModuleType = 'ai_tools' | 'page'  // 修改：'toolset' -> 'ai_tools'
```

- [ ] **Step 2: 删除 Toolset 相关类型**

删除以下类型定义：
- `AdminToolsetListItem`
- `CreateToolsetRequest`
- `UpdateToolsetRequest`
- `AdminToolsetListResponse`
- `CreateToolsetResponse`
- `UpdateToolsetResponse`
- `MoveToolsetResponse`

- [ ] **Step 3: 添加导航模块分类相关类型**

```typescript
// ========== 导航模块分类管理 ==========

export interface AdminNavigationModuleCategoryListItem {
  id: string
  navigation_module_id: string
  navigation_module_name: string
  name: string
  icon: string | null
  order: number
  created_at: string
  updated_at: string
}

export interface AdminNavigationModuleCategoryListResponse {
  categories: AdminNavigationModuleCategoryListItem[]
}

export interface CreateNavigationModuleCategoryRequest {
  navigation_module_id: string
  name: string
  icon?: string
  order: number
}

export interface CreateNavigationModuleCategoryResponse {
  id: string
  message: string
}

export interface UpdateNavigationModuleCategoryRequest {
  name: string
  icon?: string
  order: number
}

export interface UpdateNavigationModuleCategoryResponse {
  id: string
  message: string
}
```

- [ ] **Step 4: 更新 AITool 相关类型**

```typescript
// 修改 AdminAIToolListItem
export interface AdminAIToolListItem {
  id: string
  tool_id: string
  navigation_module_id: string  // 修改：toolset_id -> navigation_module_id
  navigation_module_name: string  // 新增
  category_id: string | null
  category_name: string | null
  name: string
  description: string
  system_prompt: string
  icon: string | null
  type: 'normal' | 'placeholder'
  content_type: 'text' | 'multimodal' | null
  media_type: 'image' | 'audio' | 'video' | null
  model: string | null
  welcome_message: string | null
  visible: boolean
  order: number
}

// 修改 CreateAIToolRequest
export interface CreateAIToolRequest {
  tool_id: string
  navigation_module_id: string  // 修改
  category_id: string  // 必选
  name: string
  description: string
  system_prompt: string
  icon?: string
  type: 'normal' | 'placeholder'
  content_type: 'text' | 'multimodal'
  media_type?: 'image' | 'audio' | 'video'
  model?: string
  welcome_message?: string
  visible: boolean
  order: number
}

// 类似地修改 UpdateAIToolRequest
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/types/index.ts
git commit -m "refactor: 更新前端类型定义，toolset -> navigation_module"
```

---

### Task 10: 更新 API 客户端

**Files:**
- Modify: `frontend/src/services/apiClient.ts`

- [ ] **Step 1: 删除 Toolset 相关 API**

删除以下方法：
- `getAdminToolsets()`
- `createAdminToolset()`
- `updateAdminToolset()`
- `deleteAdminToolset()`
- `moveAdminToolsetUp()`
- `moveAdminToolsetDown()`

- [ ] **Step 2: 删除 AI Tool Categories 相关 API**

删除以下方法：
- `getAdminAIToolCategories()`
- `createAdminAIToolCategory()`
- `updateAdminAIToolCategory()`
- `deleteAdminAIToolCategory()`
- `moveAdminAIToolCategoryUp()`
- `moveAdminAIToolCategoryDown()`

- [ ] **Step 3: 添加导航模块分类 API**

```typescript
// apiClient.ts

// 导航模块分类管理
getAdminNavigationModuleCategories(moduleId: string) {
  return this.apiClient.get<AdminNavigationModuleCategoryListResponse>(
    `/admin/navigation-modules/${moduleId}/categories`
  )
}

createAdminNavigationModuleCategory(moduleId: string, request: CreateNavigationModuleCategoryRequest) {
  return this.apiClient.post<CreateNavigationModuleCategoryResponse>(
    `/admin/navigation-modules/${moduleId}/categories`,
    request
  )
}

updateAdminNavigationModuleCategory(moduleId: string, categoryId: string, request: UpdateNavigationModuleCategoryRequest) {
  return this.apiClient.put<UpdateNavigationModuleCategoryResponse>(
    `/admin/navigation-modules/${moduleId}/categories/${categoryId}`,
    request
  )
}

deleteAdminNavigationModuleCategory(moduleId: string, categoryId: string) {
  return this.apiClient.delete(`/admin/navigation-modules/${moduleId}/categories/${categoryId}`)
}
```

- [ ] **Step 4: 更新 AI 工具 API**

修改参数名 `toolsetId` -> `navigationModuleId`：

```typescript
// 修改 getAdminAITools
getAdminAITools(
  navigationModuleId?: string,  // 修改参数名
  categoryId?: string,
  visible?: boolean
) {
  const params = new URLSearchParams()
  if (navigationModuleId) params.append('navigation_module_id', navigationModuleId)  // 修改
  if (categoryId) params.append('category_id', categoryId)
  if (visible !== undefined) params.append('visible', String(visible))
  return this.apiClient.get<AdminAIToolListResponse>(`/admin/ai-tools?${params}`)
}
```

- [ ] **Step 5: 更新工具列表 API**

```typescript
// 修改 getToolsByToolset -> getToolsByNavigationModule
getToolsByNavigationModule(moduleId: string) {
  return this.apiClient.get<ToolListResponse>(`/navigation-modules/${moduleId}/tools`)
}

// 添加 getAllTools
getAllTools() {
  return this.apiClient.get<ToolListResponse>('/navigation-modules/tools')
}
```

- [ ] **Step 6: 提交**

```bash
git add frontend/src/services/apiClient.ts
git commit -m "refactor: 更新 API 客户端，toolset -> navigation_module"
```

---

### Task 11: 更新 navigationStore

**Files:**
- Modify: `frontend/src/stores/navigationStore.ts`

- [ ] **Step 1: 更新枚举值处理**

```typescript
// navigationStore.ts
// 更新 getModuleId 函数
function getModuleId(module: NavigationModule): string {
  if (module.type === 'ai_tools' && module.config_source) {  // 修改：toolset -> ai_tools
    const parts = module.config_source.split('/')
    return parts[parts.length - 1]?.replace(/_/g, '-') || ''
  }
  // ... 其他保持不变
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/stores/navigationStore.ts
git commit -m "refactor: 更新 navigationStore 枚举值"
```

---

### Task 12: 增强导航模块管理页面

**Files:**
- Modify: `frontend/src/views/admin/AdminNavigationPage.vue`（直接修改现有文件）
- Modify: `frontend/src/router/index.ts`

**说明：** 直接修改现有的 `AdminNavigationPage.vue` 文件，增加分类管理功能，而不是创建新文件。

- [ ] **Step 1: 备份现有文件（可选）**

```bash
cp frontend/src/views/admin/AdminNavigationPage.vue frontend/src/views/admin/AdminNavigationPage.vue.bak
```

- [ ] **Step 2: 修改导航模块管理页面**

修改 `frontend/src/views/admin/AdminNavigationPage.vue`，在现有基础上增加分类管理功能：

```vue
<template>
  <div class="admin-navigation-modules-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>导航模块管理</h3>
          <el-button type="primary" @click="handleCreate">创建导航模块</el-button>
        </div>
      </template>

      <!-- 导航模块列表表格 -->
      <el-table :data="modules" v-loading="loading" style="width: 100%">
        <el-table-column prop="order" label="排序" width="80" />
        <el-table-column label="图标" width="80">
          <template #default="{ row }">
            <HeroIcon v-if="row.icon" :icon-name="row.icon" class="w-6 h-6" />
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="模块名称" width="200" />
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.type === 'ai_tools' ? 'primary' : 'success'">
              {{ row.type === 'ai_tools' ? 'AI工具' : '页面' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="配置来源/页面路径" min-width="200">
          <template #default="{ row }">
            <span v-if="row.type === 'ai_tools'">{{ row.config_source || '-' }}</span>
            <span v-else>{{ row.page_path || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button
              v-if="row.type === 'ai_tools'"
              size="small"
              @click="handleManageCategories(row)"
            >
              分类
            </el-button>
            <el-button size="small" @click="handleMoveUp(row)" :disabled="row.order === 0">
              上移
            </el-button>
            <el-button size="small" @click="handleMoveDown(row)">下移</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑导航模块对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑导航模块' : '创建导航模块'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="模块名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入模块名称" />
        </el-form-item>
        <el-form-item label="模块类型" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio value="ai_tools">AI工具</el-radio>
            <el-radio value="page">独立页面</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item
          label="配置来源"
          prop="config_source"
          v-if="form.type === 'ai_tools'"
        >
          <el-input
            v-model="form.config_source"
            placeholder="请输入配置来源（如：tools/ai_tools）"
          />
        </el-form-item>
        <el-form-item label="页面路径" prop="page_path" v-else>
          <el-input
            v-model="form.page_path"
            placeholder="请输入页面路径（如：/common-tools）"
          />
        </el-form-item>
        <el-form-item label="图标">
          <IconSelector v-model="form.icon" />
        </el-form-item>
        <el-form-item label="排序" prop="order">
          <el-input-number v-model="form.order" :min="0" :max="999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEditing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 分类管理对话框 -->
    <el-dialog
      v-model="categoriesDialogVisible"
      :title="`${currentModule?.name} - 分类管理`"
      width="800px"
    >
      <div class="categories-header">
        <el-button type="primary" size="small" @click="handleCreateCategory">添加分类</el-button>
      </div>
      <el-table :data="categories" v-loading="categoriesLoading" size="small">
        <el-table-column prop="order" label="排序" width="80" />
        <el-table-column label="图标" width="60">
          <template #default="{ row }">
            <HeroIcon v-if="row.icon" :icon-name="row.icon" class="w-5 h-5" />
          </template>
        </el-table-column>
        <el-table-column prop="name" label="分类名称" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEditCategory(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDeleteCategory(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 创建/编辑分类对话框 -->
    <el-dialog
      v-model="categoryFormDialogVisible"
      :title="isEditingCategory ? '编辑分类' : '添加分类'"
      width="500px"
    >
      <el-form ref="categoryFormRef" :model="categoryForm" :rules="categoryRules" label-width="100px">
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="categoryForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="图标">
          <IconSelector v-model="categoryForm.icon" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="categoryForm.order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryFormDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitCategory" :loading="categorySubmitting">
          {{ isEditingCategory ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { ApiService } from '../../services/apiClient'
import type {
  AdminNavigationModuleListItem,
  CreateNavigationModuleRequest,
  UpdateNavigationModuleRequest,
  AdminNavigationModuleCategoryListItem,
  CreateNavigationModuleCategoryRequest,
  UpdateNavigationModuleCategoryRequest,
} from '../../types'
import IconSelector from '../../components/admin/IconSelector.vue'
import HeroIcon from '../../components/HeroIcon.vue'

const modules = ref<AdminNavigationModuleListItem[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEditing = ref(false)
const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = reactive<CreateNavigationModuleRequest & { id?: string }>({
  name: '',
  type: 'ai_tools',
  config_source: '',
  page_path: '',
  icon: '',
  order: 0,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入模块名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择模块类型', trigger: 'change' }],
  config_source: [{ required: true, message: '请输入配置来源', trigger: 'blur' }],
  page_path: [{ required: true, message: '请输入页面路径', trigger: 'blur' }],
}

// 分类管理
const categoriesDialogVisible = ref(false)
const categories = ref<AdminNavigationModuleCategoryListItem[]>([])
const categoriesLoading = ref(false)
const currentModule = ref<AdminNavigationModuleListItem | null>(null)

const categoryFormDialogVisible = ref(false)
const isEditingCategory = ref(false)
const categoryFormRef = ref<FormInstance>()
const categorySubmitting = ref(false)

const categoryForm = reactive<CreateNavigationModuleCategoryRequest & { id?: string }>({
  navigation_module_id: '',
  name: '',
  icon: '',
  order: 0,
})

const categoryRules: FormRules = {
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }],
}

// 加载导航模块
async function loadModules() {
  loading.value = true
  try {
    const response = await ApiService.getAdminNavigationModules()
    modules.value = response.modules
  } catch (error: any) {
    ElMessage.error(error.message || '加载导航模块失败')
  } finally {
    loading.value = false
  }
}

// 创建
function handleCreate() {
  isEditing.value = false
  Object.assign(form, {
    name: '',
    type: 'ai_tools',
    config_source: '',
    page_path: '',
    icon: '',
    order: modules.value.length,
  })
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

// 编辑
function handleEdit(module: AdminNavigationModuleListItem) {
  isEditing.value = true
  Object.assign(form, module)
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

// 提交
async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEditing.value && form.id) {
        await ApiService.updateAdminNavigationModule(form.id, {
          name: form.name,
          type: form.type,
          config_source: form.config_source,
          page_path: form.page_path,
          icon: form.icon,
          order: form.order,
        } as UpdateNavigationModuleRequest)
        ElMessage.success('更新成功')
      } else {
        await ApiService.createAdminNavigationModule({
          name: form.name,
          type: form.type,
          config_source: form.config_source,
          page_path: form.page_path,
          icon: form.icon,
          order: form.order,
        } as CreateNavigationModuleRequest)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadModules()
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 上移
async function handleMoveUp(module: AdminNavigationModuleListItem) {
  try {
    await ApiService.moveAdminNavigationModuleUp(module.id)
    ElMessage.success('上移成功')
    loadModules()
  } catch (error: any) {
    ElMessage.error(error.message || '上移失败')
  }
}

// 下移
async function handleMoveDown(module: AdminNavigationModuleListItem) {
  try {
    await ApiService.moveAdminNavigationModuleDown(module.id)
    ElMessage.success('下移成功')
    loadModules()
  } catch (error: any) {
    ElMessage.error(error.message || '下移失败')
  }
}

// 删除
async function handleDelete(module: AdminNavigationModuleListItem) {
  try {
    await ElMessageBox.confirm(
      `确定要删除导航模块 "${module.name}" 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await ApiService.deleteAdminNavigationModule(module.id)
    ElMessage.success('删除成功')
    loadModules()
  } catch {
    // 用户取消
  }
}

// 分类管理
async function handleManageCategories(module: AdminNavigationModuleListItem) {
  currentModule.value = module
  categoriesDialogVisible.value = true
  await loadCategories(module.id)
}

async function loadCategories(moduleId: string) {
  categoriesLoading.value = true
  try {
    const response = await ApiService.getAdminNavigationModuleCategories(moduleId)
    categories.value = response.categories
  } catch (error: any) {
    ElMessage.error(error.message || '加载分类失败')
  } finally {
    categoriesLoading.value = false
  }
}

function handleCreateCategory() {
  isEditingCategory.value = false
  Object.assign(categoryForm, {
    navigation_module_id: currentModule.value!.id,
    name: '',
    icon: '',
    order: categories.value.length,
  })
  categoryFormRef.value?.clearValidate()
  categoryFormDialogVisible.value = true
}

function handleEditCategory(category: AdminNavigationModuleCategoryListItem) {
  isEditingCategory.value = true
  Object.assign(categoryForm, category)
  categoryFormRef.value?.clearValidate()
  categoryFormDialogVisible.value = true
}

async function handleSubmitCategory() {
  if (!categoryFormRef.value) return

  await categoryFormRef.value.validate(async (valid) => {
    if (!valid) return

    categorySubmitting.value = true
    try {
      if (isEditingCategory.value && categoryForm.id) {
        await ApiService.updateAdminNavigationModuleCategory(
          currentModule.value!.id,
          categoryForm.id,
          {
            name: categoryForm.name,
            icon: categoryForm.icon,
            order: categoryForm.order,
          } as UpdateNavigationModuleCategoryRequest
        )
        ElMessage.success('更新分类成功')
      } else {
        await ApiService.createAdminNavigationModuleCategory(
          currentModule.value!.id,
          {
            navigation_module_id: currentModule.value!.id,
            name: categoryForm.name,
            icon: categoryForm.icon,
            order: categoryForm.order,
          } as CreateNavigationModuleCategoryRequest
        )
        ElMessage.success('创建分类成功')
      }
      categoryFormDialogVisible.value = false
      loadCategories(currentModule.value!.id)
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      categorySubmitting.value = false
    }
  })
}

async function handleDeleteCategory(category: AdminNavigationModuleCategoryListItem) {
  try {
    await ElMessageBox.confirm(
      `确定要删除分类 "${category.name}" 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await ApiService.deleteAdminNavigationModuleCategory(
      currentModule.value!.id,
      category.id
    )
    ElMessage.success('删除成功')
    loadCategories(currentModule.value!.id)
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  loadModules()
})
</script>

<style scoped>
.admin-navigation-modules-page {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.categories-header {
  margin-bottom: 16px;
}
</style>
```

- [ ] **Step 2: 更新路由**

修改 `frontend/src/router/index.ts`：

```typescript
// router/index.ts
// 修改路由路径和组件
{
  path: 'navigation-modules',
  name: 'admin-navigation-modules',
  component: () => import('@/views/admin/AdminNavigationModulesPage.vue'),
  meta: { requiresAdmin: true }
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/admin/AdminNavigationModulesPage.vue frontend/src/router/index.ts
git commit -m "feat: 创建新的导航模块管理页面，支持分类管理"
```

---

### Task 13: 更新 AI 工具管理页面

**Files:**
- Modify: `frontend/src/views/admin/AdminAIToolsPage.vue`

- [ ] **Step 1: 更新筛选条件**

将 `toolset` 改为 `navigation_module`：

```vue
<!-- AdminAIToolsPage.vue -->
<template>
  <!-- ... -->
  <div class="filter-bar">
    <el-select
      v-model="filterNavigationModuleId"  <!-- 修改变量名 -->
      placeholder="筛选导航模块"
      clearable
      @change="handleFilterChange"
      style="width: 200px"
    >
      <el-option
        v-for="module in navigationModules"  <!-- 修改变量名 -->
        :key="module.id"
        :label="module.name"
        :value="module.id"
      />
    </el-select>
    <el-select
      v-model="filterCategoryId"
      placeholder="筛选分类"
      clearable
      @change="handleFilterChange"
      style="width: 200px"
      :disabled="!filterNavigationModuleId"
    >
      <el-option
        v-for="category in categories"
        :key="category.id"
        :label="category.name"
        :value="category.id"
      />
    </el-select>
    <!-- ... -->
  </div>

  <!-- 列表 -->
  <el-table :data="tools" v-loading="loading" style="width: 100%; margin-top: 16px">
    <!-- ... -->
    <el-table-column prop="navigation_module_name" label="导航模块" width="150" />  <!-- 修改 -->
    <el-table-column prop="category_name" label="分类" width="150">
      <template #default="{ row }">
        {{ row.category_name || '-' }}
      </template>
    </el-table-column>
    <!-- ... -->
  </el-table>

  <!-- 表单 -->
  <el-form ref="formRef" :model="form" :rules="rules" label-width="140px">
    <el-form-item label="所属导航模块" prop="navigation_module_id">  <!-- 修改 -->
      <el-select
        v-model="form.navigation_module_id"  <!-- 修改 -->
        placeholder="请选择导航模块"
        style="width: 100%"
        @change="handleNavigationModuleChange"  <!-- 修改 -->
      >
        <el-option
          v-for="module in navigationModules"  <!-- 修改 -->
          :key="module.id"
          :label="module.name"
          :value="module.id"
        />
      </el-select>
    </el-form-item>
    <el-form-item label="分类" prop="category_id">  <!-- 修改为必选 -->
      <el-select
        v-model="form.category_id"
        placeholder="请选择分类"
        style="width: 100%"
      >
        <el-option
          v-for="category in availableCategories"
          :key="category.id"
          :label="category.name"
          :value="category.id"
        />
      </el-select>
    </el-form-item>
    <!-- ... -->
  </el-form>
</template>
```

- [ ] **Step 2: 更新脚本逻辑**

```typescript
// AdminAIToolsPage.vue
<script setup lang="ts">
// 修改变量名
const filterNavigationModuleId = ref<string>()  // 修改
const filterCategoryId = ref<string>()
const filterVisible = ref<boolean>()

const navigationModules = ref<AdminNavigationModuleListItem[]>([])  // 修改类型
const categories = ref<AdminNavigationModuleCategoryListItem[]>([])  // 修改类型

const form = reactive<CreateAIToolRequest & { id?: string }>({
  tool_id: '',
  navigation_module_id: '',  // 修改
  category_id: '',  // 必选
  // ...
})

// 修改可用分类计算属性
const availableCategories = computed(() => {
  if (!form.navigation_module_id) return []  // 修改
  return categories.value.filter(
    (c) => c.navigation_module_id === form.navigation_module_id  // 修改
  )
})

// 修改加载函数
async function loadNavigationModules() {  // 修改函数名
  try {
    const response = await ApiService.getAdminNavigationModules()
    navigationModules.value = response.modules
  } catch (error: any) {
    ElMessage.error(error.message || '加载导航模块失败')
  }
}

async function loadCategories() {
  try {
    // 只加载当前筛选的导航模块的分类，避免 N+1 查询
    if (!filterNavigationModuleId.value) {
      categories.value = []
      return
    }
    const response = await ApiService.getAdminNavigationModuleCategories(filterNavigationModuleId.value)
    categories.value = response.categories
  } catch (error: any) {
    ElMessage.error(error.message || '加载分类失败')
  }
}

// 修改筛选变化处理
function handleFilterChange() {
  if (filterNavigationModuleId.value) {
    const moduleCategories = categories.value.filter(
      (c) => c.navigation_module_id === filterNavigationModuleId.value
    )
    if (
      filterCategoryId.value &&
      !moduleCategories.find((c) => c.id === filterCategoryId.value)
    ) {
      filterCategoryId.value = undefined
    }
  } else {
    filterCategoryId.value = undefined
  }
  loadTools()
}

// 修改导航模块变化处理
function handleNavigationModuleChange() {
  form.category_id = ''  // 清空分类
}

// 修改加载工具函数
async function loadTools() {
  loading.value = true
  try {
    const response = await ApiService.getAdminAITools(
      filterNavigationModuleId.value,  // 修改
      filterCategoryId.value,
      filterVisible.value
    )
    tools.value = response.tools
  } catch (error: any) {
    ElMessage.error(error.message || '加载工具列表失败')
  } finally {
    loading.value = false
  }
}

// 修改创建处理
function handleCreate() {
  isEditing.value = false
  Object.assign(form, {
    tool_id: '',
    navigation_module_id: filterNavigationModuleId.value || '',  // 修改
    category_id: '',  // 必选
    // ...
  })
  formRef.value?.clearValidate()
  drawerVisible.value = true
}

// 修改表单验证规则
const rules: FormRules = {
  navigation_module_id: [{ required: true, message: '请选择所属导航模块', trigger: 'change' }],  // 修改
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],  // 新增
  // ...
}
</script>
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/admin/AdminAIToolsPage.vue
git commit -m "refactor: 更新AI工具管理页面，toolset -> navigation_module"
```

---

### Task 14: 删除旧的管理页面和更新布局

**Files:**
- Delete: `frontend/src/views/admin/AdminToolsetsPage.vue`
- Delete: `frontend/src/views/admin/AdminAIToolCategoriesPage.vue`
- Modify: `frontend/src/layouts/AdminLayout.vue`

- [ ] **Step 1: 删除旧页面**

```bash
rm frontend/src/views/admin/AdminToolsetsPage.vue
rm frontend/src/views/admin/AdminAIToolCategoriesPage.vue
```

- [ ] **Step 2: 更新 AdminLayout**

修改 `frontend/src/layouts/AdminLayout.vue`，删除旧菜单项：

```vue
<!-- AdminLayout.vue -->
<template>
  <!-- ... -->
  <el-menu>
    <!-- 删除这些菜单项 -->
    <!-- <el-menu-item index="/admin/toolsets">工具集</el-menu-item> -->
    <!-- <el-menu-item index="/admin/ai-tool-categories">AI工具分类</el-menu-item> -->

    <!-- 保留或修改为 -->
    <el-menu-item index="/admin/navigation-modules">导航模块</el-menu-item>
    <el-menu-item index="/admin/ai-tools">AI工具</el-menu-item>
    <!-- ... -->
  </el-menu>
</template>
```

- [ ] **Step 3: 更新路由**

修改 `frontend/src/router/index.ts`，删除旧路由：

```typescript
// router/index.ts
// 删除这些路由
// {
//   path: 'toolsets',
//   name: 'admin-toolsets',
//   component: () => import('@/views/admin/AdminToolsetsPage.vue'),
//   meta: { requiresAdmin: true }
// },
// {
//   path: 'ai-tool-categories',
//   name: 'admin-ai-tool-categories',
//   component: () => import('@/views/admin/AdminAIToolCategoriesPage.vue'),
//   meta: { requiresAdmin: true }
// },
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/layouts/AdminLayout.vue frontend/src/router/index.ts
git commit -m "refactor: 删除工具集和AI工具分类管理页面"
```

---

### Task 15: 更新前端用户界面

**Files:**
- Modify: `frontend/src/components/AIToolSelector.vue`（如果使用工具列表API）
- Modify: `frontend/src/components/ModelSelector.vue`（如果使用工具列表API）
- Modify: `frontend/src/layouts/MainLayout.vue`（如果使用工具列表API）
- Modify: `frontend/src/stores/navigationStore.ts`（已在前面的任务中处理）

**说明：** 根据代码搜索，以下文件可能使用工具列表相关的API：
- `frontend/src/components/AIToolSelector.vue`
- `frontend/src/components/ModelSelector.vue`
- `frontend/src/layouts/MainLayout.vue`

- [ ] **Step 1: 检查每个文件是否使用旧 API**

对每个文件运行以下检查：
- 是否调用 `getToolsByToolset()`
- 是否使用 `toolset_id` 参数

- [ ] **Step 2: 更新 API 调用**

将 `getToolsByToolset(toolsetId)` 改为 `getToolsByNavigationModule(moduleId)`

示例：
```typescript
// 修改前
const response = await apiClient.get<ToolListResponse>(`/toolsets/${toolsetId}/tools`)

// 修改后
const response = await apiClient.get<ToolListResponse>(`/navigation-modules/${moduleId}/tools`)
```

- [ ] **Step 3: 运行类型检查**

```bash
cd frontend
npx vue-tsc --noEmit
```

预期：无类型错误

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/ frontend/src/views/
git commit -m "refactor: 更新前端用户界面API调用"
```

---

## 第五阶段：测试验证

### Task 16: 运行数据库迁移

**Files:**
- Execute: Database migration

- [ ] **Step 1: 备份数据库**

```bash
mysqldump -u root -p ai_teacher_platform > backup_before_refactor.sql
```

- [ ] **Step 2: 运行迁移**

```bash
cd backend
alembic upgrade head
```

预期：迁移成功，无错误

- [ ] **Step 3: 验证数据**

```bash
mysql -u root -p ai_teacher_platform
```

```sql
-- 检查 navigation_modules 表
SELECT id, name, type FROM navigation_modules;

-- 检查 ai_tool_categories 表是否有 navigation_module_id
SELECT id, name, navigation_module_id FROM ai_tool_categories;

-- 检查 ai_tools 表是否有 navigation_module_id
SELECT id, tool_id, name, navigation_module_id FROM ai_tools;

-- 确认 toolsets 表已删除
SHOW TABLES LIKE 'toolsets';
```

- [ ] **Step 4: 提交迁移记录**

```bash
git add backend/alembic/versions/
git commit -m "chore: 应用数据库迁移"
```

---

### Task 17: 后端测试

**Files:**
- Test: `backend/tests/`

- [ ] **Step 1: 运行单元测试**

```bash
cd backend
python -m pytest tests/unit/ -v
```

预期：大部分测试通过

- [ ] **Step 2: 运行集成测试**

```bash
python -m pytest tests/integration/ -v
```

预期：大部分测试通过

- [ ] **Step 3: 修复失败的测试**

根据失败信息更新测试用例

- [ ] **Step 4: 提交测试修复**

```bash
git add backend/tests/
git commit -m "test: 更新测试用例以适配新的数据模型"
```

---

### Task 18: 前端测试

**Files:**
- Test: `frontend/`

- [ ] **Step 1: 类型检查**

```bash
cd frontend
npx vue-tsc --noEmit
```

预期：无类型错误

- [ ] **Step 2: 单元测试**

```bash
npm run test
```

预期：测试通过

- [ ] **Step 3: 提交测试修复**

```bash
git add frontend/
git commit -m "test: 更新前端测试"
```

---

### Task 19: E2E 测试

**Files:**
- Test: `frontend/tests/e2e/`

- [ ] **Step 1: 更新 E2E 测试**

修改使用旧路径的测试用例

- [ ] **Step 2: 运行 E2E 测试**

```bash
cd frontend
npm run test:e2e -- tests/e2e/chat.spec.ts --project=chromium
```

预期：测试通过

- [ ] **Step 3: 提交测试修复**

```bash
git add frontend/tests/e2e/
git commit -m "test: 更新E2E测试"
```

---

## 第六阶段：清理

### Task 20: 清理配置文件

**Files:**
- Delete: `configs/navigation.yaml`
- Delete: `configs/tools/` (可选，确认后删除)

- [ ] **Step 1: 确认数据库数据正常**

确保所有数据已正确迁移到数据库

- [ ] **Step 2: 删除或归档配置文件**

```bash
# 归档配置文件
mkdir -p archive/configs
mv configs/navigation.yaml archive/configs/
mv configs/tools archive/configs/
```

- [ ] **Step 3: 删除 config_service.py 中不再需要的代码**

如果 `ConfigService` 只用于配置文件读取，可以删除或简化

- [ ] **Step 4: 提交**

```bash
git add archive/
git commit -m "chore: 归档已废弃的配置文件"
```

---

### Task 21: 更新文档

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md` (如果需要)

- [ ] **Step 1: 更新 CLAUDE.md**

更新项目架构说明，反映新的数据模型

- [ ] **Step 2: 提交**

```bash
git add CLAUDE.md README.md
git commit -m "docs: 更新项目文档以反映新的架构"
```

---

## 验收检查清单

完成所有任务后，逐项检查：

- [ ] 数据库迁移成功，无数据丢失
- [ ] `toolsets` 表已删除
- [ ] `ai_tool_categories` 和 `ai_tools` 使用 `navigation_module_id`
- [ ] 后台管理界面功能正常：
  - [ ] 导航模块管理可创建、编辑、删除 AI 工具类型模块
  - [ ] 导航模块管理可维护分类
  - [ ] AI 工具管理可创建、编辑、删除工具
  - [ ] 所有筛选和级联功能正常
- [ ] 前端用户界面功能正常：
  - [ ] 导航切换正常
  - [ ] 工具列表显示正常
  - [ ] 聊天功能正常
- [ ] 所有 API 响应中的关联字段显示友好名称
- [ ] 后端测试通过
- [ ] E2E 测试通过
