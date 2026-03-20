# 配置文件数据库化设计文档

**日期**: 2026-03-20
**状态**: 设计阶段
**作者**: Claude Code

---

## 1. 概述

### 1.1 目标

将系统中的 YAML 配置文件迁移到数据库存储，并提供后台管理页面进行维护。

### 1.2 变更范围

| 配置类型 | 当前位置 | 迁移目标 |
|---------|---------|---------|
| 导航模块 | `configs/navigation.yaml` | `navigation_modules` 表 |
| 工具集 | YAML 目录结构 | `toolsets` 表 |
| 工具分类 | `categories.yaml` | `ai_tool_categories` 表 |
| AI工具 | `*.yaml` 文件 | `ai_tools` 表 |
| 系统提示词 | `prompts/*.md` 或内嵌 | `ai_tools.system_prompt` 字段 |

### 1.3 设计原则

1. **API 兼容性**: 现有业务 API 完全保持不变
2. **向后兼容**: YAML 文件保留作为备份
3. **渐进式迁移**: 通过 Alembic 迁移 + 数据导入脚本
4. **功能不变**: 前端用户界面和功能不受影响

---

## 2. 数据库设计

### 2.1 导航模块表 (navigation_modules)

```sql
CREATE TABLE navigation_modules (
    id CHAR(36) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    type ENUM('toolset', 'page') NOT NULL,
    config_source VARCHAR(100) NULL,
    page_path VARCHAR(100) NULL,
    icon VARCHAR(50) NULL,
    `order` INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

### 2.2 工具集表 (toolsets)

```sql
CREATE TABLE toolsets (
    id CHAR(36) PRIMARY KEY,
    toolset_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    icon VARCHAR(50) NULL,
    `order` INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

### 2.3 工具分类表 (ai_tool_categories)

```sql
CREATE TABLE ai_tool_categories (
    id CHAR(36) PRIMARY KEY,
    toolset_id CHAR(36) NOT NULL,
    name VARCHAR(50) NOT NULL,
    icon VARCHAR(50) NULL,
    `order` INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (toolset_id) REFERENCES toolsets(id) ON DELETE CASCADE
);
```

### 2.4 AI工具表 (ai_tools)

```sql
CREATE TABLE ai_tools (
    id CHAR(36) PRIMARY KEY,
    tool_id VARCHAR(50) UNIQUE NOT NULL,
    toolset_id CHAR(36) NOT NULL,
    category_id CHAR(36) NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    system_prompt TEXT NULL,
    icon VARCHAR(50) NULL,
    type ENUM('normal', 'media') NOT NULL DEFAULT 'normal',
    content_type VARCHAR(20) NULL,
    media_type VARCHAR(20) NULL,
    model VARCHAR(100) NULL,
    welcome_message TEXT NULL,
    visible BOOLEAN NOT NULL DEFAULT TRUE,
    `order` INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (toolset_id) REFERENCES toolsets(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES ai_tool_categories(id) ON DELETE SET NULL
);
```

### 2.5 ER 图

```
NavigationModule (导航模块)
    ├─ [type = 'toolset'] → Toolset

Toolset (工具集)
    ├─ 1:N → AiToolCategory (工具分类)
    └─ 1:N → AiTool (AI工具)

AiToolCategory (工具分类)
    └─ 1:N → AiTool (AI工具)
```

---

## 3. 后端 API 设计

### 3.1 导航模块管理 API

| 方法 | 路径 | 说明 |
|-----|------|-----|
| GET | `/api/v1/admin/navigation/modules` | 获取导航模块列表 |
| POST | `/api/v1/admin/navigation/modules` | 创建导航模块 |
| PUT | `/api/v1/admin/navigation/modules/:id` | 更新导航模块 |
| DELETE | `/api/v1/admin/navigation/modules/:id` | 删除导航模块 |
| PATCH | `/api/v1/admin/navigation/modules/:id/order` | 调整排序 |

### 3.2 工具集管理 API

| 方法 | 路径 | 说明 |
|-----|------|-----|
| GET | `/api/v1/admin/toolsets` | 获取工具集列表 |
| POST | `/api/v1/admin/toolsets` | 创建工具集 |
| PUT | `/api/v1/admin/toolsets/:id` | 更新工具集 |
| DELETE | `/api/v1/admin/toolsets/:id` | 删除工具集 |
| GET | `/api/v1/admin/toolsets/:id/categories` | 获取工具集的分类 |

### 3.3 工具分类管理 API

| 方法 | 路径 | 说明 |
|-----|------|-----|
| GET | `/api/v1/admin/tool-categories` | 获取分类列表 |
| POST | `/api/v1/admin/tool-categories` | 创建分类 |
| PUT | `/api/v1/admin/tool-categories/:id` | 更新分类 |
| DELETE | `/api/v1/admin/tool-categories/:id` | 删除分类 |
| PATCH | `/api/v1/admin/tool-categories/:id/order` | 调整排序 |

### 3.4 AI工具管理 API

| 方法 | 路径 | 说明 |
|-----|------|-----|
| GET | `/api/v1/admin/ai-tools` | 获取工具列表（支持筛选） |
| POST | `/api/v1/admin/ai-tools` | 创建工具 |
| PUT | `/api/v1/admin/ai-tools/:id` | 更新工具 |
| DELETE | `/api/v1/admin/ai-tools/:id` | 删除工具 |
| PATCH | `/api/v1/admin/ai-tools/:id/toggle` | 切换 visible 状态 |
| PATCH | `/api/v1/admin/ai-tools/:id/order` | 调整排序 |

### 3.5 现有 API 保持不变

以下 API 端点**完全保持不变**，内部实现改为从数据库读取：

- `/api/v1/navigation` - 获取导航模块
- `/api/v1/tools` - 获取工具列表
- `/api/v1/toolsets` - 获取工具集
- `/api/v1/tools/:tool_id` - 获取单个工具

---

## 4. 前端页面设计

### 4.1 路由结构

```
/admin/navigation         → 导航模块管理页面
/admin/toolsets          → 工具集管理页面
/admin/tool-categories   → 工具分类管理页面
/admin/ai-tools          → AI工具管理页面
```

### 4.2 页面布局

每个管理页面采用统一的表格布局：

```
┌─────────────────────────────────────────────────────┐
│  页面标题                    [新建] 按钮             │
├─────────────────────────────────────────────────────┤
│  ┌──────┬─────────┬────────┬────────┬────────────┐  │
│  │ 拖拽 │  名称   │ 图标   │ 排序   │  操作      │  │
│  ├──────┼─────────┼────────┼────────┼────────────┤  │
│  │ ☰    │ AI模型能│ sparkles│   1    │ [编辑][删除]│  │
│  └──────┴─────────┴────────┴────────┴────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 4.3 AI工具编辑器

AI工具字段较多，使用抽屉式编辑器：

- **基本信息**: 工具ID、名称、图标、分类、模型、可见性、排序
- **描述**: 文本框
- **系统提示词**: Markdown 编辑器（支持全屏编辑）
- **欢迎消息**: 文本框

### 4.4 组件复用

#### MarkdownEditor 组件

从 `MarkdownEditorView.vue` 抽取核心编辑器逻辑为独立组件：

```
MarkdownEditorView.vue (原有页面，保持不变)
    └── 使用 MarkdownEditor.vue (新组件)

AdminAIToolForm.vue (新的后台表单)
    └── 使用 MarkdownEditor.vue (新组件)
```

#### IconSelector 组件

新建图标选择器组件，支持：
- 搜索图标名称
- 分页显示 Heroicons 图标
- 点击选择

---

## 5. 数据迁移方案

### 5.1 迁移步骤

**步骤1: 创建新表**
```bash
alembic revision -m "add ai tool config tables"
alembic upgrade head
```

**步骤2: 运行数据迁移脚本**
```bash
python backend/scripts/migrate_yaml_to_db.py
```

**步骤3: 验证**
- 启动服务，检查工具列表是否正常
- 测试聊天功能是否正常

### 5.2 迁移脚本逻辑

1. 读取 `configs/navigation.yaml` → 插入 `navigation_modules`
2. 遍历 `configs/tools/` 子目录 → 插入 `toolsets`
3. 读取每个工具集的 `categories.yaml` → 插入 `ai_tool_categories`
4. 读取每个工具集的 `*.yaml` → 插入 `ai_tools`
5. 处理 `system_prompt_file` → 读取 `prompts/*.md` 内容

### 5.3 回滚方案

如果迁移后出现问题：
- 删除数据库数据，重新运行迁移脚本
- 或启动时检测数据库为空，自动从 YAML 加载

### 5.4 YAML 文件处理

迁移完成后：
- YAML 文件**保留**作为备份
- 不再作为运行时配置源
- 可选：添加 `--reload-yaml` 参数支持重新导入

---

## 6. 实施顺序

1. **数据库模型**: 创建 4 个新 SQLAlchemy 模型
2. **Alembic 迁移**: 创建数据库表
3. **数据迁移脚本**: YAML → 数据库
4. **服务层改造**: ConfigLoader、ToolService 改为从数据库读取
5. **后台 API**: 创建 4 组管理 API
6. **前端页面**: 创建 4 个管理页面 + 组件
7. **测试验证**: 功能测试、回归测试

---

## 7. 验收标准

- [ ] 所有 YAML 配置成功导入数据库
- [ ] 现有业务 API 功能正常
- [ ] 前端用户界面无变化
- [ ] 后台管理页面可增删改查配置
- [ ] Markdown 编辑器正常工作
- [ ] 图标选择器正常工作
- [ ] 数据迁移脚本可重复执行
- [ ] 回滚机制可用
