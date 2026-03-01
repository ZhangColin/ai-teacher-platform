# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 提供在此代码库中工作的指导。

## 🌏 语言规则

**重要：在与此项目相关的所有交流中，必须使用中文。**

- ✅ 使用中文回复用户的所有问题和请求
- ✅ 代码注释使用中文编写
- ✅ 变量命名使用英文（遵循代码规范），但注释和文档必须使用中文
- ✅ Git commit 消息使用中文
- ✅ 测试描述和文档使用中文

**原因：** 这是一个面向中文用户的 AI 智能备课平台项目，团队成员主要使用中文交流。使用中文可以确保沟通效率和质量。

## 项目概述

AI 智能备课平台是一个基于大语言模型（Kimi/DeepSeek）的教育辅助平台，帮助教师通过自然语言对话创建交互式 HTML5 课件、SVG 可视化图表和 Markdown 教学设计。平台采用模块化工具集架构，AI 工具通过 YAML 配置文件定义，而非硬编码。

## 开发命令

### 后端 (FastAPI + Python 3.10+)
```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 环境配置
cp .env.example .env  # 编辑 .env 填入 API 密钥和数据库 URL

# 运行开发服务器
python -m src.main  # 运行在 http://localhost:8000

# 运行测试
pytest                          # 运行所有测试
pytest tests/test_auth_api.py   # 运行指定测试文件
pytest -v                       # 详细输出
pytest -k "test_login"          # 运行匹配模式的测试

# 数据库迁移
alembic upgrade head            # 应用迁移
alembic revision --autogenerate -m "描述"  # 创建迁移
```

### 前端 (Vue 3 + TypeScript + Vite)
```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev          # 运行在 http://localhost:5173

# 生产构建
npm run build        # 类型检查 + 构建

# 运行测试
npm run test         # 运行 Vitest
npm run test:ui      # Vitest UI 模式
npm run test:coverage # 覆盖率报告

# 类型检查
npx vue-tsc --noEmit # 检查类型但不构建
```

## 架构设计

### 模块化工具集系统

平台的核心创新是**配置驱动的工具集架构**。AI 工具不是硬编码的，而是通过 `configs/` 目录中的 YAML 配置文件定义：

```
configs/
├── navigation.yaml           # 顶部导航模块配置
└── tools/
    ├── ai_tools/             # AI模型能力工具集
    │   ├── categories.yaml
    │   └── *.yaml           # 各个工具的配置
    └── teaching_researcher/  # AI教研员工具集
        ├── categories.yaml
        ├── prompts/          # 系统提示词 markdown 文件
        └── *.yaml           # 各个工具的配置
```

**添加新工具的步骤：**
1. 在 `configs/tools/<toolset>/tool_name.yaml` 创建 YAML 配置
2. 创建系统提示词文件（通过 `system_prompt_file` 引用）
3. 如需要，在 `categories.yaml` 中添加分类
4. 后端通过 `src/services/tool_service.py` 中的 `ToolService` 自动加载配置

**工具配置结构：**
```yaml
tool_id: unique_identifier
name: "显示名称"
description: "工具描述"
category: "分类名称"
icon: "heroicon-name"
visible: true
type: "normal" | "media"  # media 工具支持多模态输入输出
order: 1
toolset_id: toolset_name
system_prompt_file: "prompts/file.md"
model: "deepseek:deepseek-chat"  # provider:module 格式
welcome_message: |
  多行欢迎消息
```

### 后端结构 (FastAPI)

```
backend/src/
├── main.py                    # 应用入口，路由注册
├── database.py                # SQLAlchemy 会话管理
├── db_models.py              # ORM 模型（用户、会话、消息、成果物等）
├── models.py                 # API 请求/响应的 Pydantic 模型
├── config_loader.py          # YAML 配置加载工具
│
├── routers/                  # API 端点
│   ├── auth.py              # /api/v1/auth/* (登录、注册)
│   ├── users.py             # /api/v1/admin/users/*
│   ├── tools.py             # /api/v1/tools/*, /api/v1/toolsets/*
│   ├── sessions.py          # /api/v1/sessions/*
│   ├── admin_tools.py       # /api/v1/admin/common-tools/*
│   ├── works.py             # /api/v1/works/*
│   ├── courses.py           # /api/v1/documents/*
│   ├── common.py            # 媒体生成端点
│   └── dependencies.py      # FastAPI 依赖（认证、数据库会话）
│
└── services/                 # 业务逻辑层
    ├── ai_service.py        # LLM 集成（OpenAI SDK）
    ├── auth_service.py      # JWT、密码哈希
    ├── session_service.py   # 会话/消息管理
    ├── tool_service.py      # 从 YAML 加载工具配置
    ├── common_tool_service.py # 内置/HTML 工具 CRUD
    ├── work_service.py      # 教案作品 CRUD
    ├── course_service.py    # 课程文档 CRUD
    ├── artifact_parser.py   # 从 LLM 响应中提取成果物
    └── title_generator.py   # AI 驱动的会话标题生成
```

**关键架构模式：**
- **路由 → 服务 → 模型**：路由层处理 HTTP，服务层包含业务逻辑，模型层处理数据
- **依赖注入**：`dependencies.py` 中的 `get_current_user()` 和 `get_db()`
- **成果物解析**：LLM 响应可包含结构化的"成果物"（HTML、SVG、Markdown），通过 `artifact_parser.py` 中的正则表达式提取
- **多提供商 AI**：通过环境变量配置支持 Kimi 和 DeepSeek

### 前端结构 (Vue 3 Composition API)

```
frontend/src/
├── main.ts                   # 应用入口
├── App.vue                   # 根组件
│
├── router/index.ts          # Vue Router 配置（hash 模式）
├── services/apiClient.ts    # Axios 封装，带认证拦截器
│
├── stores/                  # Pinia 状态管理
│   ├── authStore.ts        # 用户认证状态、令牌管理
│   ├── sessionStore.ts     # 当前会话、消息、成果物
│   ├── agentStore.ts       # 已废弃，使用 toolStore
│   ├── navigationStore.ts  # 顶部导航模块，来自 /api/v1/navigation
│   ├── coursesStore.ts     # 课程文档状态
│   └── worksStore.ts       # 教案作品状态
│
├── layouts/                 # 页面布局组件
│   ├── MainLayout.vue      # 工具集布局（侧边栏 + 聊天区）
│   ├── AdminLayout.vue     # 管理后台布局
│   ├── CommonToolsLayout.vue # 内置工具查看器
│   ├── WorksLayout.vue     # 教案展示区
│   └── DocumentsLayout.vue # 课程文档树形视图
│
├── views/                   # 页面组件
│   ├── LoginPage.vue
│   ├── AgentListView.vue    # 已废弃
│   ├── AgentDetailView.vue  # 已废弃
│   ├── MediaChatView.vue    # 多模态聊天（图片生成）
│   ├── HtmlToolView.vue     # HTML 工具预览
│   └── admin/               # 管理 CRUD 页面
│
├── components/
│   ├── ChatInterface.vue   # 聊天区 + 输入 + 会话列表
│   ├── MediaChatInterface.vue  # 多模态变体
│   ├── ChatPanel.vue       # 聊天消息显示
│   ├── PreviewPanel.vue    # 成果物渲染（HTML/SVG/Markdown）
│   ├── SidebarMenu.vue     # 工具分类侧边栏
│   ├── AIToolSelector.vue  # 工具选择下拉框
│   ├── ModuleSwitcher.vue  # 顶部导航模块切换器
│   └── media/              # 媒体专用组件
│       ├── ImageGallery.vue
│       ├── ImageLightbox.vue
│       └── GeneratingIndicator.vue
│
├── types/                   # TypeScript 类型定义
│   ├── index.ts            # 主要 API 类型
│   ├── media.ts            # 多模态类型
│   └── navigation.ts       # 导航配置类型
│
└── utils/
    ├── markdownRenderer.ts # Markdown 转 HTML，支持 KaTeX
    └── sessionStorage.ts   # Session storage 工具
```

**关键前端模式：**
- **基于路由的模块**：`/modules/:moduleId` 映射到 `configs/navigation.yaml` 中的工具集
- **流式聊天**：使用 SSE（`ApiService.chatStream()`）实现实时 LLM 响应
- **成果物渲染**：`PreviewPanel.vue` 检测成果物类型并相应渲染
- **管理员权限守卫**：路由守卫检查 `authStore.user?.is_admin` 用于 `/admin/*` 路由

### 数据库模型 (SQLAlchemy)

`backend/src/db_models.py` 中的核心模型：

```
UserModel (users)
  ├── SessionModel (sessions) ──┬──> MessageModel (messages)
  │                             └──> ArtifactModel (artifacts)
  │
ToolCategoryModel (tool_categories)
  └──> CommonToolModel (common_tools)

WorkCategoryModel (work_categories)
  └──> WorkModel (works)

CourseCategoryModel (course_categories)  # 自引用树形结构
  └──> CourseDocumentModel (course_documents)
```

**关系说明：**
- 用户 → 会话 → 消息 → 成果物（级联删除）
- 所有分类模型都有 order 字段用于手动排序
- CourseCategory 通过 `parent_id` 自引用形成树形结构

### 认证与授权

- **基于 JWT**：令牌存储在 `localStorage`/`sessionStorage`
- **管理员检查**：`UserModel.is_admin` 布尔字段
- **受保护路由**：路由守卫检查 `authStore.isAuthenticated`
- **API 中间件**：`dependencies.py:get_current_user()` 验证 JWT 并返回用户
- **自动刷新**：`apiClient.ts` 中的响应拦截器在 401 时清除令牌

## 配置文件

### 后端环境变量 (.env)
必需变量：
- `DATABASE_URL`：MySQL 连接字符串
- `JWT_SECRET_KEY`：JWT 签名密钥
- `CURRENT_PROVIDER`："kimi" 或 "deepseek"
- `KIMI_API_KEY` 或 `DEEPSEEK_API_KEY`：LLM 提供商凭证

完整模板见 `backend/.env.example`。

### 前端 (vite.config.ts)
- 代理 `/api` → `http://127.0.0.1:8000`（后端）
- 代理 `/static` → `http://127.0.0.1:8000`（静态文件）
- 别名 `@` → `./src`

## 测试

- **后端**：pytest 配合 `pytest-asyncio` 进行异步测试
- **前端**：Vitest 配合 `@vue/test-utils` 和 `@testing-library/jest-dom`
- 测试配置：`backend/pytest.ini`、`frontend/vite.config.ts`（test: 部分）

## ⚠️ 测试铁律（重要）

> **测试的目的是保证代码质量，而不是制造虚假的信心。**

### 核心原则

1. **写了测试一定要执行通过**
   - 提交前必须运行测试，确保所有新测试都能通过
   - **绝不允许"从未通过"的测试进入代码库**
   - 如果测试无法通过，要么修复代码，要么删除测试，不能让其留在代码中

2. **通过的测试，轻易不该被修改**
   - 测试一旦通过，就成为了系统行为的契约
   - 修改测试必须有充分理由（如需求变更、发现bug）
   - 不能为了"让测试通过"而修改测试本身

3. **发现通不过的测试，一定要确认**
   - 首先确认：这是否发现了真实的bug？
   - 如果是bug → 修复代码，让测试通过
   - 如果不是bug → 确认需求变更，再更新测试
   - **不允许**：跳过测试、注释测试、为了通过而修改测试断言

### 禁止行为

❌ **禁止：**
- 跳过失败的测试（`@pytest.mark.skip`）
- 注释掉失败的测试
- 为了通过测试而修改测试的断言
- 提交从未通过的新测试
- 将失败的测试留在代码库中"以后再修"

✅ **正确做法：**
- 测试失败 → 确认是bug还是测试问题
- 是bug → 修复代码

---

## ⚠️ 任务执行铁律（非常重要）

> **任务必须完整完成，不能偷工减料，不能擅作主张。**

### 核心原则

1. **完成任务，不要"差不多"**
   - 如果计划说完成13个模块，就必须完成13个模块
   - 如果验收标准是80%覆盖率，就必须达到80%
   - **不允许**完成4个就说"大部分完成了"

2. **有问题必须确认**
   - 遇到问题、偏差、困难时，必须询问用户
   - **不能擅自决定**"这个模块不重要可以跳过"
   - **不能擅自决定**"45%已经够好了"
   - **不能擅自决定**"先合并吧，以后再补"

3. **验收必须严格执行**
   - 计划中的验收标准必须100%达成
   - 在验收通过之前，不能提交、不能合并、不能说"完成了"
   - 验收未通过 = 任务未完成

4. **进度必须透明**
   - 实时报告进度，不要隐瞒未完成的部分
   - 如果某个模块确实无法完成，说明原因并询问用户
   - 不要等用户验收时才发现"只完成了31%"

### 2026-03-01 事件教训

**错误示范**（绝对禁止）：
- ❌ 计划完成13个模块，实际只完成4个（31%）
- ❌ 覆盖率目标80%，实际只有45%
- ❌ 用户说"太快了"，但已经合并到dev分支
- ❌ 用户问"都完成了吗"，才发现只完成了31%
- ❌ 把"偷工减料"包装成"阶段性成果"

**正确做法**：
- ✅ 13个模块就必须完成13个，一个不少
- ✅ 45%未达标就是未达标，不能说"关键模块已达标"
- ✅ 遇到问题立即询问："这个模块很复杂，预计需要10小时，是否继续？"
- ✅ 验收时提供完整清单："13个模块完成情况：✅4个，❌9个"
- ✅ 在验收通过前，明确说明："还有9个模块未完成，是否继续？"

### 禁止行为（任务执行）

❌ **绝对禁止**：
- 擅自决定"这个模块不重要可以跳过"
- 擅自决定"45%已经够好了"
- 擅自决定"先合并，以后再补"
- 把"部分完成"说成"阶段性成果"
- 隐瞒未完成的部分，等用户发现

✅ **必须做到**：
- 严格执行计划，完成所有要求的模块
- 达到所有验收标准，一个都不能少
- 进度透明，实时汇报未完成部分
- 有问题立刻确认，不要擅作主张

### 验收检查清单

在说"任务完成"之前，必须检查：
- [ ] 计划中的所有模块是否都完成了？
- [ ] 验收标准是否都达成了？
- [ ] 有没有未完成的部分？
- [ ] 如果有未完成，是否已经告知用户并得到确认？

只有当所有这些都"是"的时候，才能说"任务完成"。
- 是测试问题 → 修复测试或删除测试
- 所有测试必须在提交前通过

### 测试验证命令

每次提交代码前，必须运行：

```bash
# 后端测试（约2秒）
cd backend && python3 -m pytest tests/unit/ tests/integration/ -v

# E2E测试（约6秒）- 最重要！
cd frontend && npm run test:e2e -- tests/e2e/chat.spec.ts --project=chromium
```

**预期结果：**
- 后端：154 passed
- E2E：10 passed

### 历史教训

2026-03-01：删除了5个从未通过的集成测试（commit 527d82f）
- 这些测试在本会话中添加，从一开始就没通过
- 违反了"写了测试一定要执行通过"的原则
- E2E测试已经覆盖相同功能，这些测试没有价值

**记住：测试不能稳定通过，就失去了所有意义。**

## 常见任务

### 添加新的 AI 工具（工具集）
1. 创建目录：`configs/tools/my_toolset/`
2. 创建 `categories.yaml` 定义工具分类
3. 创建 `my_tool.yaml` 定义工具配置
4. 创建 `prompts/my_prompt.md` 定义系统提示词
5. 在 `configs/navigation.yaml` 的 `modules` 下添加工具集
6. 重启后端以加载新配置

### 调试 LLM 响应
- 检查 `backend/src/services/ai_service.py` 了解提供商逻辑
- 成果物解析在 `artifact_parser.py` - 提取 HTML/SVG 的正则模式
- 前端流式处理在 `services/apiClient.ts:chatStream()`

### 数据库迁移
修改 `db_models.py` 后：
```bash
cd backend
alembic revision --autogenerate -m "描述"
alembic upgrade head
```
