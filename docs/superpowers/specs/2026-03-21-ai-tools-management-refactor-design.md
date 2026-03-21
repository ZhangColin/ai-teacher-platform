# AI 工具管理架构重构设计

**日期：** 2026-03-21
**作者：** Claude
**状态：** 设计中

## 一、背景

当前系统中，AI 工具的管理存在以下问题：

1. **概念冗余**：导航模块、工具集、AI工具分类 三层概念重叠，导致管理界面复杂
2. **菜单过多**：后台有"工具集管理"和"AI工具分类管理"两个独立菜单，与"导航模块管理"功能重复
3. **数据关系不清晰**：工具集作为独立实体，实际上与导航模块的 toolset 类型是同一概念

## 二、目标

1. **简化数据模型**：删除 `toolsets` 表，合并到 `navigation_modules`
2. **简化后台菜单**：只保留"导航模块管理"和"AI工具管理"
3. **统一数据源**：所有配置从数据库读取，不再使用 YAML 配置文件
4. **保持前端兼容**：前端功能不变，API 响应格式保持兼容

## 三、数据模型设计

### 3.1 新的数据关系

```
NavigationModule（导航模块）
  ├── type = "ai_tools" 时
  │     └── AIToolCategory（分类）
  │           └── AITool（AI工具）
  └── type = "page" 时
        （独立页面，无子项）
```

### 3.2 数据模型变更

| 表名 | 变更类型 | 说明 |
|------|----------|------|
| `navigation_modules` | 修改 | 增加关系到分类和工具 |
| `toolsets` | **删除** | 合并到 navigation_modules |
| `ai_tool_categories` | 修改 | `toolset_id` → `navigation_module_id` |
| `ai_tools` | 修改 | `toolset_id` → `navigation_module_id` |

### 3.3 新的 ORM 模型

```python
class NavigationModuleType(enum.Enum):
    """导航模块类型枚举"""
    ai_tools = "ai_tools"  # 原(toolset)改为(ai_tools)
    page = "page"


class NavigationModuleModel(Base):
    """导航模块数据库模型"""
    __tablename__ = "navigation_modules"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False)
    type = Column(Enum(NavigationModuleType), nullable=False)
    config_source = Column(String(100), nullable=True)  # 保留，用于兼容
    page_path = Column(String(100), nullable=True)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 新增：对于 type=ai_tools 的模块，关联其分类和工具
    categories = relationship("AIToolCategoryModel",
                             back_populates="navigation_module",
                             cascade="all, delete-orphan",
                             foreign_keys="AIToolCategoryModel.navigation_module_id")

    tools = relationship("AIToolModel",
                        back_populates="navigation_module",
                        cascade="all, delete-orphan",
                        foreign_keys="AIToolModel.navigation_module_id")


class AIToolCategoryModel(Base):
    """AI工具分类数据库模型"""
    __tablename__ = "ai_tool_categories"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # 修改：toolset_id → navigation_module_id
    navigation_module_id = Column(CHAR(36),
                                  ForeignKey("navigation_modules.id", ondelete="CASCADE"),
                                  nullable=False, index=True)
    name = Column(String(50), nullable=False)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系修改
    navigation_module = relationship("NavigationModuleModel", back_populates="categories")
    tools = relationship("AIToolModel", back_populates="category")


class AIToolModel(Base):
    """AI工具数据库模型"""
    __tablename__ = "ai_tools"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String(50), unique=True, nullable=False, index=True)
    # 修改：toolset_id → navigation_module_id
    navigation_module_id = Column(CHAR(36),
                                  ForeignKey("navigation_modules.id", ondelete="CASCADE"),
                                  nullable=False, index=True)
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

    # 关系修改
    navigation_module = relationship("NavigationModuleModel", back_populates="tools")
    category = relationship("AIToolCategoryModel", back_populates="tools")

    # 联合索引修改
    __table_args__ = (
        Index("idx_ai_tool_navigation_module_order", "navigation_module_id", "order"),
        Index("idx_ai_tool_category_order", "category_id", "order"),
    )
```

## 四、API 设计

### 4.1 前端用户 API

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/v1/navigation` | GET | 获取导航配置（不变） |
| `/api/v1/navigation-modules/{module_id}/tools` | GET | 获取导航模块下的分类及工具 |
| `/api/v1/navigation-modules/tools` | GET | 获取所有导航模块的工具 |

**响应格式示例：**

```json
// GET /api/v1/navigation-modules/{module_id}/tools
{
  "categories": [
    {
      "name": "内容生成",
      "icon": "sparkles",
      "tools": [
        {
          "tool_id": "text_gen",
          "name": "文字对话",
          "description": "与AI进行自然对话",
          "icon": "chat-bubble-left-right",
          "type": "normal",
          "model": "deepseek:deepseek-chat",
          "welcome_message": "你好！我是你的AI助手",
          "content_type": "text",
          "media_type": null,
          "visible": true
        }
      ]
    }
  ]
}
```

### 4.2 后台管理 API

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/v1/admin/navigation-modules` | GET | 导航模块列表 |
| `/api/v1/admin/navigation-modules` | POST | 创建导航模块 |
| `/api/v1/admin/navigation-modules/{id}` | GET | 导航模块详情 |
| `/api/v1/admin/navigation-modules/{id}` | PUT | 更新导航模块 |
| `/api/v1/admin/navigation-modules/{id}` | DELETE | 删除导航模块 |
| `/api/v1/admin/navigation-modules/{id}/categories` | GET | 获取模块的分类列表 |
| `/api/v1/admin/navigation-modules/{id}/categories` | POST | 创建分类 |
| `/api/v1/admin/navigation-modules/{id}/categories/{category_id}` | PUT | 更新分类 |
| `/api/v1/admin/navigation-modules/{id}/categories/{category_id}` | DELETE | 删除分类 |
| `/api/v1/admin/ai-tools` | GET | AI工具列表 |
| `/api/v1/admin/ai-tools` | POST | 创建AI工具 |
| `/api/v1/admin/ai-tools/{tool_id}` | GET | AI工具详情 |
| `/api/v1/admin/ai-tools/{tool_id}` | PUT | 更新AI工具 |
| `/api/v1/admin/ai-tools/{tool_id}` | DELETE | 删除AI工具 |
| `/api/v1/admin/ai-tools/{tool_id}/move-up` | POST | 上移工具 |
| `/api/v1/admin/ai-tools/{tool_id}/move-down` | POST | 下移工具 |
| `/api/v1/admin/ai-tools/{tool_id}/toggle-visibility` | POST | 切换可见性 |

**删除的 API：**

- `/api/v1/admin/toolsets/*` - 全部删除
- `/api/v1/admin/ai-tool-categories/*` - 全部删除

### 4.3 关联字段显示规则

所有关联关系在 API 响应和前端界面中显示**友好名称**，而非 GUID：

| 关联字段 | 显示内容 | 数据来源 | 示例 |
|----------|----------|----------|------|
| navigation_module | `navigation_module_name` | `navigation_modules.name` | "AI模型能力" |
| category | `category_name` | `ai_tool_categories.name` | "内容生成" |
| model | `model` 字段格式 | 格式: `{provider_code}:{model_code}` | "deepseek:deepseek-chat" |

**说明：**
- AI 工具的 `model` 字段存储格式为 `provider_code:model_code`（如 `deepseek:deepseek-chat`）
- 前端显示时，如需显示供应商名称，可通过 `provider_code` 关联 `model_providers` 表获取 `provider_name`
- 或者在 API 响应中直接返回解析后的 `provider_name` 和 `model_name`

## 五、后台管理界面设计

### 5.1 菜单结构

| 菜单项 | 功能 |
|--------|------|
| 导航模块管理 | 管理所有导航模块，AI工具类型可管理分类 |
| AI工具管理 | 维护具体AI工具 |

**删除的菜单：**
- ~~工具集管理~~
- ~~AI工具分类管理~~

### 5.2 导航模块管理页面

**列表表格：**

| 列 | 说明 |
|----|------|
| 排序 | order |
| 名称 | 导航模块显示名称 |
| 类型 | 下拉：AI工具 / 页面 |
| 图标 | icon |
| 操作 | 编辑、删除 |

**编辑对话框：**
- 名称
- 类型（下拉：AI工具 / 页面）
- 图标（图标选择器）
- 排序（数字输入）
- **AI工具类型特有**：分类管理按钮（类似模型供应商的"模型"按钮）

**分类管理对话框：**
- 显示该模块下的分类列表
- 可添加、编辑、删除、排序分类
- 分类字段：名称、图标、排序

### 5.3 AI工具管理页面

**筛选条件：**

| 条件 | 说明 |
|------|------|
| 导航模块 | 下拉选择（级联控制分类选项） |
| 分类 | 根据选中模块显示对应分类（必选） |
| 可见性 | 全部/可见/隐藏 |

**列表表格：**

| 列 | 说明 |
|----|------|
| 排序 | order |
| 图标 | icon |
| 导航模块 | `navigation_module_name` |
| 分类 | `category_name` |
| 工具ID | tool_id |
| 工具名称 | name |
| 类型 | normal/media |
| 可见 | visible 开关 |
| 操作 | 编辑、上移、下移、删除 |

**编辑/创建表单：**
- 所属导航模块（必选，下拉）
- 分类（必选，根据导航模块级联）
- 工具ID（创建后不可修改）
- 工具名称
- 工具描述
- 图标
- 工具类型（normal/placeholder）
- 内容类型（text/multimodal）
- 媒体类型（image/audio/video，多模态时显示）
- AI模型
- 欢迎语
- 可见性
- 排序
- 系统提示词

## 六、数据迁移计划

### 6.1 迁移步骤

1. **添加新列**
   - `navigation_modules` 表：无变更
   - `ai_tool_categories` 表：添加 `navigation_module_id` 列
   - `ai_tools` 表：添加 `navigation_module_id` 列

2. **数据映射**
   - 根据 `navigation_modules.config_source`（如 `tools/ai_tools`）与 `toolsets.toolset_id` 的对应关系
   - 将 `toolsets.id` 映射到 `navigation_modules.id`
   - 更新 `ai_tool_categories.navigation_module_id`
   - 更新 `ai_tools.navigation_module_id`

3. **删除旧列和表**
   - `ai_tool_categories.toolset_id`
   - `ai_tools.toolset_id`
   - `toolsets` 表

4. **更新枚举**
   - `NavigationModuleType.toolset` → `NavigationModuleType.ai_tools`

### 6.2 迁移脚本

```python
# 伪代码示例
def migrate_toolsets_to_navigation_modules(db: Session):
    """
    迁移 toolsets 到 navigation_modules

    映射规则：
    - navigation_modules.config_source 格式: "tools/{toolset_id}"
    - 例如: "tools/ai_tools" -> toolset_id = "ai_tools"
    - 例如: "tools/teaching_researcher" -> toolset_id = "teaching_researcher"
    """
    # 1. 建立 toolset_id 到 navigation_module_id 的映射
    mapping = {}
    for nav_module in db.query(NavigationModuleModel).filter(
        NavigationModuleModel.type == "ai_tools"  # 迁移前类型为 "toolset"
    ).all():
        if not nav_module.config_source:
            continue
        # 从 config_source 提取 toolset_id
        # 格式: "tools/ai_tools" -> "ai_tools"
        parts = nav_module.config_source.strip().split("/")
        if len(parts) >= 2:
            toolset_id = parts[-1]  # 取最后一部分
        else:
            toolset_id = nav_module.config_source

        toolset = db.query(ToolsetModel).filter(
            ToolsetModel.toolset_id == toolset_id
        ).first()
        if toolset:
            mapping[toolset.id] = nav_module.id

    # 2. 更新 ai_tool_categories
    for category in db.query(AIToolCategoryModel).all():
        if category.toolset_id in mapping:
            category.navigation_module_id = mapping[category.toolset_id]

    # 3. 更新 ai_tools
    for tool in db.query(AIToolModel).all():
        if tool.toolset_id in mapping:
            tool.navigation_module_id = mapping[tool.toolset_id]

    # 4. 删除 toolsets 表
    # (在 alembic 迁移中处理)
```

### 6.3 回滚方案

如果迁移失败，执行以下回滚步骤：

1. **恢复数据库**：从迁移前的备份恢复
   ```bash
   # 迁移前执行备份
   mysqldump -u root -p ai_teacher_platform > backup_before_migration.sql

   # 回滚时恢复
   mysql -u root -p ai_teacher_platform < backup_before_migration.sql
   ```

2. **代码回滚**：回退到迁移前的 git commit
   ```bash
   git revert <migration-commit>
   ```

3. **注意事项**：
   - 迁移前务必备份数据库
   - 在测试环境先验证迁移脚本
   - 生产环境迁移时选择低峰期进行

## 七、前端组件变更

### 7.1 组件变更列表

| 组件 | 变更 |
|------|------|
| `AdminLayout.vue` | 删除"工具集"和"AI工具分类"菜单项 |
| `AdminNavigationModulesPage.vue` | 新增分类管理对话框 |
| `AdminToolsetsPage.vue` | **删除** |
| `AdminAIToolCategoriesPage.vue` | **删除** |
| `AdminAIToolsPage.vue` | 修改筛选条件、列表列、表单字段 |
| `navigationStore.ts` | 更新 API 路径、枚举值 |
| `apiClient.ts` | 更新 API 路径 |
| `router/index.ts` | 删除工具集和分类相关路由 |
| `types/index.ts` | 更新类型定义 |

### 7.2 路由变更

**删除的路由：**
- `/admin/toolsets`
- `/admin/ai-tool-categories`

**新增/修改的路由：**
- `/admin/navigation-modules` - 导航模块管理（可能已存在，需增强）

## 八、配置文件处理

### 8.1 配置文件状态

| 文件 | 状态 |
|------|------|
| `configs/navigation.yaml` | **废弃**，数据迁移到数据库后可删除 |
| `configs/tools/ai_tools/categories.yaml` | **废弃** |
| `configs/tools/ai_tools/*.yaml` | **废弃** |
| `configs/tools/teaching_researcher/*` | **废弃** |

### 8.2 迁移策略

1. 保留现有配置文件作为初始化数据源
2. 编写迁移脚本将 YAML 配置导入数据库
3. 确认数据库数据正常后，可删除配置文件

## 九、验收标准

1. ✅ 数据库迁移成功，无数据丢失
2. ✅ 后台管理界面功能正常：
   - 导航模块管理可创建、编辑、删除 AI 工具类型模块
   - 导航模块管理可维护分类
   - AI 工具管理可创建、编辑、删除工具
   - 所有筛选和级联功能正常
3. ✅ 前端用户界面功能正常：
   - 导航切换正常
   - 工具列表显示正常
   - 聊天功能正常
4. ✅ 所有 API 响应中的关联字段显示友好名称
5. ✅ 后端测试通过
6. ✅ E2E 测试通过

## 十、实施步骤

1. **数据库迁移** - 创建 alembic 迁移脚本
2. **后端 API 改造** - 修改路由和服务层
3. **后台管理界面** - 修改/删除前端组件
4. **前端用户界面** - 更新 API 调用路径
5. **测试验证** - 运行后端测试和 E2E 测试
6. **清理配置文件** - 确认无问题后删除
