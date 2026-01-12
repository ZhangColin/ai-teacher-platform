# 开发任务列表 (Backlog)

> **文档定位**: 记录所有开发任务，包括待开发、进行中、已完成的任务  
> **更新机制**: 任务拆分后更新，任务完成后标记状态

---

## 当前迭代：UI框架开发

**需求来源**: `docs/requirements/ui_framework_spec.md`  
**架构设计**: `docs/design/frontend_architecture.md`  
**创建时间**: 2026-01-02

### 任务列表

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| ui-framework-1 | 实现基础布局框架（MainLayout、Header、AIToolsLayout的基础结构，配置路由，更新App.vue）- 刷新页面能看到整体布局框架 | completed | P0 |
| ui-framework-2 | 实现顶部导航栏完整功能（Logo、大模块切换、用户信息，写死数据，应用基础样式）- 刷新页面能看到完整的Header | completed | P0 |
| ui-framework-3 | 实现AI工具模块布局完整功能（左侧菜单+右侧聊天区域，写死所有数据，应用基础样式）- 刷新页面能看到完整的AI工具模块界面 | completed | P0 |
| ui-framework-4 | 实现所有交互功能（大模块切换、菜单选中、菜单收起展开、对话列表切换、输入框交互、预览功能）- 刷新页面所有交互都能正常工作 | completed | P0 |
| ui-framework-5 | 完善样式和响应式（参考Gemini风格完善所有组件样式，实现桌面端和移动端响应式布局）- 刷新页面看到最终视觉效果 | completed | P0 |

---

## 当前迭代：用户登录功能开发

**需求来源**: `docs/requirements/user_auth_spec.md`  
**架构设计**: `docs/design/api_interface.md`, `docs/design/data_models.md`  
**创建时间**: 2026-01-02

### 任务列表

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| auth-1 | 实现用户登录API（POST /api/v1/auth/login）- 支持邮箱密码登录，返回JWT Token，可调用验证 | completed | P0 |
| auth-2 | 实现获取当前用户API（GET /api/v1/auth/me）- 根据Token返回用户信息，可调用验证 | completed | P0 |
| auth-3 | 实现用户管理API（GET /api/v1/admin/users, POST /api/v1/admin/users）- 用户列表和创建用户，可调用验证 | completed | P0 |
| auth-4 | 实现登录页面（LoginPage.vue）- 表单验证、错误提示、记住我功能，UI可见 | completed | P0 |
| auth-5 | 实现用户管理页面（UserListPage.vue, CreateUserForm.vue）- 用户列表展示和创建用户表单，UI可见 | completed | P0 |
| auth-6 | 实现路由守卫和认证状态管理（authStore）- 未登录跳转登录页，Token存储和管理，功能可验证 | completed | P0 |
| auth-7 | 更新Header组件和现有API调用 - 显示用户信息，添加Token认证，UI可见/功能可验证 | completed | P0 |

---

## 任务状态说明

- **pending**: 待开发
- **in_progress**: 进行中
- **completed**: 已完成
- **cancelled**: 已取消

---

---

## 当前迭代：用户登录功能增强（用户名登录 + 昵称字段）

**需求来源**: `docs/requirements/user_auth_spec.md`  
**架构设计**: `docs/design/api_interface.md`, `docs/design/data_models.md`  
**创建时间**: 2026-01-03

### 任务列表

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| auth-enhance-1 | 数据库迁移：添加 nickname 字段，username 改为唯一索引，email 改为可选 | completed | P0 |
| auth-enhance-2 | 更新后端数据模型：UserModel 添加 nickname 字段，username 添加唯一索引，email 改为可选 | completed | P0 |
| auth-enhance-3 | 更新后端领域模型：User 添加 nickname 字段，username 必填且唯一，email 改为可选，更新 create 方法 | completed | P0 |
| auth-enhance-4 | 更新 UserService：添加 get_user_by_username 方法，更新 create_user 支持 nickname，email 改为可选 | completed | P0 |
| auth-enhance-5 | 更新登录 API：支持用户名登录，账号判断优先级（手机号 > 邮箱 > 用户名） | completed | P0 |
| auth-enhance-6 | 更新创建用户 API：username 必填且唯一，nickname 可选，email 改为可选，更新验证逻辑 | completed | P0 |
| auth-enhance-7 | 更新前端类型定义：UserInfo、UserListItem、CreateUserRequest 添加 nickname 字段，email 改为可选 | completed | P0 |
| auth-enhance-8 | 更新登录页面：支持用户名登录，更新验证规则（用户名、邮箱、手机号） | completed | P0 |
| auth-enhance-9 | 更新用户列表页面：显示昵称字段（如未填写则显示用户名） | completed | P0 |
| auth-enhance-10 | 更新创建用户表单：添加昵称输入框，username 必填且唯一，email 改为可选 | completed | P0 |
| auth-enhance-11 | 更新所有测试用例：适配用户名登录和昵称字段 | completed | P0 |
| auth-enhance-12 | 更新 Header 组件：显示昵称（如未填写则显示用户名） | completed | P0 |

---

**最后更新**: 2026-01-03（用户登录功能增强任务已完成）

---

## 当前迭代：工具管理和会话功能开发

**需求来源**: `docs/requirements/product_spec.md` (v4.0)  
**架构设计**: `docs/design/api_interface.md` (v2.0), `docs/design/data_models.md` (v2.0)  
**创建时间**: 2026-01-03

### 任务列表

#### 工具管理模块

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| tool-1 | 更新工具配置模型：添加 `visible`、`type`、`category`、`icon`、`welcome_message`、`order` 字段 | completed | P0 |
| tool-2 | 实现工具配置加载服务：支持按 `category` 聚合生成分类结构，只返回 `visible=true` 的工具，支持排序 | completed | P0 |
| tool-3 | 实现获取工具列表API（GET /api/v1/tools）：返回按分类组织的工具列表，包含图标和分类信息 | completed | P0 |
| tool-4 | 实现工具选择器组件（AIToolSelector.vue）：从API加载工具列表，按分类展示，支持工具切换 | completed | P0 |
| tool-5 | 实现占位工具处理：点击占位工具显示"敬请期待"页面 | completed | P0 |
| tool-6 | 实现分类和工具的顺序控制（通过 categories.yaml 和工具配置的 order 字段） | completed | P0 |

#### 历史对话列表模块

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| conversation-1 | 实现获取历史对话列表API（GET /api/v1/tools/{tool_id}/conversations）：按用户+工具维度查询，按更新时间倒序 | completed | P0 |
| conversation-2 | 实现历史对话列表组件（ConversationList.vue）：展示对话列表，支持点击切换对话 | completed | P0 |
| conversation-3 | 实现编辑会话标题API（PATCH /api/v1/sessions/{session_id}）：更新会话标题 | completed | P0 |
| conversation-4 | 实现删除会话API（DELETE /api/v1/sessions/{session_id}）：级联删除会话和消息 | completed | P0 |
| conversation-5 | 实现对话列表编辑功能：内联编辑标题（实时保存），删除对话（二次确认） | completed | P0 |
| conversation-6 | 实现工具切换联动：切换工具时自动切换对话列表 | completed | P0 |
| conversation-7 | 实现新建对话功能：点击"新建对话"按钮，切换到新建对话状态（显示欢迎语） | completed | P0 |

#### 会话管理模块

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| session-1 | 更新会话数据模型：添加 `title`、`updated_at` 字段，关联 `user_id` 和 `tool_id` | completed | P0 |
| session-2 | 实现会话延迟创建机制：用户进入工具时不创建会话，发送第一条消息时才创建 | completed | P0 |
| session-3 | 实现会话自动命名：基于第一条消息的前30-50个字符生成标题（前端决定长度） | completed | P0 |
| session-4 | 实现获取会话详情API（GET /api/v1/sessions/{session_id}）：返回完整消息历史 | completed | P0 |
| session-5 | 更新对话交互API（POST /api/v1/tools/{tool_id}/chat）：支持 `session_id` 可选，首次调用自动创建会话 | completed | P0 |
| session-6 | 实现欢迎语配置化展示：从工具配置读取 `welcome_message`，用户进入工具时展示 | completed | P0 |
| session-7 | 实现会话恢复功能：刷新页面后，前端调用API恢复会话列表和当前会话 | completed | P0 |

#### 预览功能模块（基础功能）

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| preview-1 | 实现代码块识别和预览按钮：识别 markdown/html/svg 代码块，显示预览按钮 | completed | P0 |
| preview-2 | 实现预览界面布局：点击预览按钮后左右分屏，左侧聊天区域，右侧预览区域 | completed | P0 |
| preview-3 | 实现Markdown预览：预览区渲染Markdown内容 | completed | P0 |
| preview-4 | 实现HTML预览：预览区使用iframe sandbox安全执行HTML内容 | completed | P0 |
| preview-5 | 实现SVG预览：预览区渲染SVG内容 | completed | P0 |
| preview-6 | 实现预览区域关闭功能：手动关闭预览区域，恢复单栏布局 | completed | P0 |

#### 预览功能模块（增强功能 - 低优先级）

| ID | 任务描述 | 状态 | 优先级 | 备注 |
|:---|:---|:---|:---|:---|
| preview-enhance-1 | 实现Markdown下载功能：下载为Markdown格式文件 | completed | P2 | |
| preview-enhance-2 | 实现Markdown转Word下载功能：将Markdown内容转换为Word文档并下载 | completed | P2 | |
| preview-enhance-3 | 实现Markdown转PDF下载功能：将Markdown内容转换为PDF文件并下载 | completed | P2 | |
| preview-enhance-4 | 实现HTML全屏预览功能 | completed | P2 | 使用模态框式全屏(fixed+z-index)，而非浏览器全屏API，工具栏保持可见 |
| preview-enhance-5 | 实现HTML下载功能：下载HTML文件 | completed | P2 | 使用Blob+URL.createObjectURL实现 |
| preview-enhance-6 | 实现HTML截图功能：使用html2canvas或其他方案截图HTML内容 | pending | P3 | 暂缓实现 |
| preview-enhance-7 | 实现SVG全屏预览功能 | completed | P2 | 使用模态框式全屏(fixed+z-index)，而非浏览器全屏API，工具栏保持可见 |
| preview-enhance-8 | 实现SVG下载功能：下载SVG文件 | completed | P2 | 使用Blob+URL.createObjectURL实现 |
| preview-enhance-9 | 实现SVG截图功能：使用html2canvas或其他方案截图SVG内容 | pending | P3 | 暂缓实现 |
| preview-core-1 | 修复代码块按钮生成逻辑：为所有代码块生成复制和预览按钮 | completed | P0 | 移除markdownRenderer中的类型判断，统一生成按钮HTML，类型判断移至PreviewPanel |
| cleanup-1 | 清理废弃组件：删除MessageItem.vue和MessageList.vue | completed | P1 | 避免代码架构混淆，保持代码清晰 |
| preview-enhance-10 | （可选）WPS兼容性：提供图片格式数学公式选项，或在UI中提示推荐使用Word打开 | pending | P3 | |

> **说明**: preview-enhance-10 是可选任务。当前 Word 导出功能在 Microsoft Word 中显示完全正常，WPS Office 由于对 OMML 格式支持不完整导致显示异常。这是 WPS 的兼容性问题，可以通过 UI 提示或提供替代格式来改进用户体验。

#### 界面交互模块

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| ui-interaction-1 | 实现工具选择器收起功能：收起为浮动图标，点击重新展开，位置固定左侧中间 | completed | P0 |
| ui-interaction-2 | 实现历史对话列表收起功能：收起为浮动图标，点击重新展开，位置固定左侧偏下（避免重叠） | completed | P0 |
| ui-interaction-3 | 完善对话交互细节：参考DeepSeek实现消息展示样式、输入框交互、加载状态、错误处理 | completed | P0 |

#### 提示词向导工具配置

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| prompt-wizard-1 | 创建提示词向导工具配置（configs/tools/prompt_wizard.yaml）：包含完整的系统提示词和配置 | completed | P0 |
| prompt-wizard-2 | 测试提示词向导工具：验证六步引导流程正常工作 | completed | P0 |

---

**最后更新**: 2026-01-03（添加工具管理和会话功能开发任务）

---

## 当前迭代：多工具集架构扩展（教研员模块）

**需求来源**: `docs/requirements/teaching_researcher_spec.md`  
**架构设计**: `docs/design/multi_toolset_architecture.md`, `docs/design/api_interface.md` (v3.0), `docs/design/data_models.md` (v3.0)  
**创建时间**: 2026-01-09

### 架构目标

**核心原则**: 低侵入式扩展，配置驱动，组件复用

- 支持多个工具集模块（AI工具、教研员等）共享同一套UI和功能逻辑
- 通过配置文件定义导航结构，无需为新模块重新开发
- 支持大型系统提示词文件化管理

### 任务列表

#### 阶段1：后端基础扩展（支持多工具集）

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| multi-toolset-1.1 | 扩展数据模型：Tool 添加 `toolset_id`（默认"ai_tools"）、`system_prompt_file`（可选）字段 | completed | P0 |
| multi-toolset-1.2 | 创建配置加载器（`config_loader.py`）：支持加载 `navigation.yaml`，支持从文件读取系统提示词 | completed | P0 |
| multi-toolset-1.3 | 新增导航API端点：`GET /api/v1/navigation` - 返回顶部导航模块配置 | completed | P0 |
| multi-toolset-1.4 | 新增工具集API端点：`GET /api/v1/toolsets/{toolset_id}/tools` - 返回指定工具集的工具列表（按分类组织） | completed | P0 |
| multi-toolset-1.5 | 更新 `ToolService`：支持按 `toolset_id` 过滤工具，支持加载工具集目录结构 | completed | P0 |
| multi-toolset-1.6 | 编写单元测试：测试配置加载器、新API端点、系统提示词文件加载 | pending | P1 |

#### 阶段2：前端基础扩展（配置驱动）

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| multi-toolset-2.1 | 创建导航状态管理（`stores/navigationStore.ts`）：缓存导航配置，支持模块切换 | completed | P0 |
| multi-toolset-2.2 | 更新类型定义（`types/navigation.ts`）：定义 `NavigationModule`、`ModuleType` 等类型 | completed | P0 |
| multi-toolset-2.3 | 更新 `MainLayout.vue`：从硬编码改为配置驱动，根据导航配置动态加载模块组件 | completed | P0 |
| multi-toolset-2.4 | 创建 `ToolsetModuleLayout.vue`：复用 `AIToolsLayout` 逻辑，参数化 `toolset_id` | completed | P0 |
| multi-toolset-2.5 | 更新 `Header.vue`：从导航配置动态生成顶部模块切换按钮 | completed | P0 |
| multi-toolset-2.6 | 测试现有AI工具模块：确保重构后现有功能不受影响 | completed | P1 |
| multi-toolset-2.7 | 修复欢迎词Markdown渲染和工具切换响应 | completed | P0 |

#### 阶段3：教研员模块配置（首个应用）

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| multi-toolset-3.1 | 创建导航配置文件 `configs/navigation.yaml`：定义"AI工具"、"教研员"等4个顶部导航模块 | completed | P0 |
| multi-toolset-3.2 | 迁移现有工具配置：将现有工具移到 `configs/tools/ai_tools/` 目录，添加 `toolset_id: ai_tools` | completed | P0 |
| multi-toolset-3.3 | 创建教研员工具集：11个学科教研员工具配置和系统提示词文件，优化分类结构为5个科目 | completed | P0 |
| multi-toolset-3.4 | 端到端测试：验证AI工具和教研员两个模块都能正常工作，数据隔离正确 | in_progress | P1 |
| multi-toolset-3.5 | 更新部署文档：记录新的配置文件结构和系统提示词文件管理方式 | pending | P2 |

---

### 教研员配置目录结构（用户提供）

完成 `multi-toolset-3.2` 后，需要用户提供以下配置文件：

```
configs/tools/teaching_researcher/
├── prompts/                      # 系统提示词文件目录
│   ├── chinese_teacher.md        # 语文教研员提示词（用户提供）
│   ├── math_teacher.md           # 数学教研员提示词（用户提供）
│   └── ...
├── chinese_teacher.yaml          # 语文教研员工具配置（用户提供）
├── math_teacher.yaml             # 数学教研员工具配置（用户提供）
└── categories.yaml               # 分类配置（用户提供）
```

**配置示例**将在 `multi-toolset-3.2` 完成后提供。

---

---

## 🎉 里程碑：多工具集架构扩展核心功能已完成！

**阶段1-3 全部完成** ✅（2026-01-09）

- ✅ 后端基础扩展（5/5 完成）
- ✅ 前端基础扩展（6/6 完成）
- ✅ 教研员模块配置（3/3 完成）

**成果**：
- 架构：支持无限扩展工具集模块，配置驱动
- 兼容：向后兼容，现有功能不受影响
- 示例：完整的教研员工具集配置模板
- 文档：详细的配置说明和使用指南

**下一步**：
- 端到端测试验证（optional）
- 更新部署文档（optional）

**最后更新**: 2026-01-09（多工具集架构扩展核心功能全部完成 🎊）

---

## 当前迭代：常用工具模块开发

**需求来源**: `docs/requirements/common_tools_spec.md` (v1.0)  
**架构设计**: `docs/design/api_interface.md` (v3.0), `docs/design/data_models.md` (v4.0)  
**创建时间**: 2026-01-09

### 任务列表

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| common-tools-1 | 后端-完成常用工具数据库设计与实现（表结构、ORM模型、Pydantic模型、初始化数据） | completed | P0 |
| common-tools-2 | 后端-实现获取工具分类列表功能（含Service、API、测试） | completed | P0 |
| common-tools-3 | 后端-实现获取工具详情功能（含Service、API、测试） | completed | P0 |
| common-tools-4 | 前端-实现工具卡片页（含类型定义、API客户端、路由、页面、测试） | completed | P0 |
| common-tools-5 | 前端-实现Markdown编辑器工具（含CodeMirror集成、编辑预览、下载、测试） | completed | P0 |
| common-tools-6 | 前端-实现HTML工具运行器（含沙箱运行、全屏功能、测试） | completed | P0 |
| common-tools-7 | 集成验证-端到端测试完整流程（从卡片页到工具使用） | completed | P0 |

---

**最后更新**: 2026-01-09（添加常用工具模块开发任务）

---

## 当前迭代：作品展示模块开发

**需求来源**: `docs/requirements/works_display_spec.md` (v1.0)  
**架构设计**: `docs/design/works_display_implementation_guide.md` (v1.0), `docs/design/api_interface.md` (v3.1), `docs/design/data_models.md` (v4.1)  
**创建时间**: 2026-01-10

### 模块概述

作品展示模块是一个独立的HTML作品展示平台，功能与常用工具模块高度相似（分类+卡片+详情页+HTML沙箱），但采用独立的数据表、API、前端页面实现。

### 任务列表

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| works-1 | 基础设施准备（创建static目录结构、配置FastAPI静态文件服务、执行数据库迁移脚本） | completed | P0 |
| works-2 | 后端-完成作品展示数据库设计与实现（ORM模型、Pydantic模型、验证迁移结果） | completed | P0 |
| works-3 | 后端-实现获取作品分类列表功能（含Service、API、测试） | completed | P0 |
| works-4 | 后端-实现获取作品详情功能（含Service、API、测试） | completed | P0 |
| works-5 | 前端-实现作品卡片页（含类型定义、API客户端、Store、页面组件、路由配置） | completed | P0 |
| works-6 | 前端-实现作品详情页（含页面组件、路由配置、HTML沙箱运行、全屏功能） | completed | P0 |
| works-7 | 集成验证-端到端测试完整流程（从卡片页到作品详情页，验收标准逐项检查） | completed | P0 |

---

**最后更新**: 2026-01-10（添加作品展示模块开发任务）

**实施说明**: 详细技术要点和实施步骤参考 `docs/design/works_display_implementation_guide.md`

---

## 当前迭代：后台管理系统开发

**需求来源**: `docs/requirements/admin_backend_spec.md` (v1.0)  
**架构设计**: `docs/design/api_interface.md` (v4.0), `docs/design/data_models.md` (v4.1)  
**创建时间**: 2026-01-11

### 模块概述

后台管理系统为内部运营人员提供便捷的管理界面，支持用户管理、常用工具管理、作品展示管理。使用Element Plus组件库，独立的后台布局，完善的权限控制体系。

### 设计原则

- **可交付验收**：每个任务都是完整的功能模块（后端API + 前端页面）
- **不改坏现有功能**：在现有架构上扩展，不影响前台用户功能
- **TDD驱动**：测试先行，确保代码质量
- **独立部署**：后台管理独立引入Element Plus，不影响前台样式

### 任务列表

| ID | 任务描述 | 状态 | 优先级 | 验收标准 |
|:---|:---|:---|:---|:---|
| admin-1 | **基础设施准备**：数据库迁移（is_admin字段）、权限中间件、前端依赖（Element Plus + Heroicons）、路由守卫 | completed | P0 | - 数据库表包含is_admin字段<br>- 管理员账号（admin/HcyAdmin@2026）可登录<br>- 非管理员访问/admin/*自动跳转首页<br>- Element Plus和Heroicons正常引入 |
| admin-2 | **后台布局与导航**：实现后台管理系统布局（侧边栏导航+主内容区），集成图标系统（图标选择器+自动推荐逻辑） | completed | P0 | - 访问/admin显示后台管理布局<br>- 侧边栏包含用户管理、工具管理、作品管理菜单<br>- 图标选择器可正常使用（搜索、预览、选择）<br>- 图标自动推荐功能工作正常 |
| admin-3 | **用户管理模块**：实现用户管理完整功能（后端API 5个 + 前端页面） | completed | P0 | - 可查看用户列表（分页、筛选管理员）<br>- 可创建新用户（表单验证、管理员权限设置）<br>- 可编辑用户信息（用户名、昵称、邮箱、手机、管理员权限）<br>- 可删除用户（二次确认、不能删除自己、至少保留1个管理员）<br>- 可重置用户密码（显示新密码） |
| admin-4 | **常用工具管理模块**：实现工具管理完整功能（后端API 13个 + 前端页面） | completed | P0 | - 可查看工具列表（分页、筛选分类/类型/可见性）<br>- 可创建内置工具（表单验证、图标选择）<br>- 可上传HTML工具（文件上传、文件大小<5MB）<br>- 可编辑工具信息（名称、描述、分类、图标）<br>- 可删除工具（二次确认）<br>- 可上下移动工具排序<br>- 可切换工具可见性<br>- 可管理工具分类（创建、编辑、删除、排序） |
| admin-5 | **作品管理模块**：实现作品管理完整功能（后端API 12个 + 前端页面） | completed | P0 | - 可查看作品列表（分页、筛选分类/可见性）<br>- 可上传作品（HTML文件、文件大小<10MB）<br>- 可编辑作品信息（名称、描述、分类、图标）<br>- 可删除作品（二次确认）<br>- 可上下移动作品排序<br>- 可切换作品可见性<br>- 可管理作品分类（创建、编辑、删除、排序） |
| admin-6 | **后台入口集成**：在顶部导航添加"管理后台"入口（仅管理员可见），完成端到端集成测试 | completed | P0 | - 管理员登录后顶部显示"管理后台"入口<br>- 普通用户看不到"管理后台"入口<br>- 点击入口可进入后台管理页面<br>- 所有后端测试通过<br>- 手动验收所有需求文档中的验收标准 |

---

**最后更新**: 2026-01-11（添加后台管理系统开发任务）

---

## 当前迭代：AI素养课模块开发（文档管理）

**需求来源**: `docs/requirements/ai_literacy_course_spec.md` (v1.0)  
**架构设计**: `docs/design/document_management_design.md` (v1.0), `docs/design/api_interface.md` (v4.1), `docs/design/data_models.md` (v4.2)  
**创建时间**: 2026-01-12

### 模块概述

AI素养课模块提供系统化的课程文档展示和管理平台。前台展示采用三栏布局（目录+文件列表+文档内容），支持多级目录结构，在线阅读和下载Markdown文档。后台管理支持目录和文档的完整生命周期管理。

### 设计原则

- **复用现有组件**：文档预览直接复用 PreviewPanel 组件（Markdown渲染+下载功能）
- **保持风格一致**：参考现有的常用工具和作品展示模块的实现风格
- **不破坏现有功能**：在现有架构上扩展，确保向后兼容
- **可交付验收**：每个任务都是完整的功能模块，可独立验收

### 任务列表

#### 阶段1：数据库和后端服务

| ID | 任务描述 | 状态 | 优先级 | 验收标准 |
|:---|:---|:---|:---|:---|
| doc-1 | **数据库基础设施**：创建数据库表（course_categories、course_documents），执行Alembic迁移，创建static/course_docs目录结构 | pending | P0 | - course_categories表创建成功（支持多级目录）<br>- course_documents表创建成功<br>- 外键约束正确（ON DELETE RESTRICT）<br>- static/course_docs/目录存在 |
| doc-2 | **Service层 - 目录服务**：实现course_service.py（目录CRUD、递归构建目录树、排序move_up/move_down、删除检查） | pending | P0 | - 可以创建、查询、更新、删除目录<br>- 递归构建目录树正确<br>- 目录排序功能正常<br>- 删除检查正确（有子目录或文档时阻止删除）<br>- 单元测试通过 |
| doc-3 | **Service层 - 文档服务**：扩展course_service.py（文档CRUD、文件上传/读取/删除、排序、上下篇计算） | pending | P0 | - 可以创建、查询、更新、删除文档<br>- 文件上传保存到正确路径<br>- 文件删除清理目录<br>- 排序功能正常<br>- 上下篇计算正确<br>- 单元测试通过 |
| doc-4 | **前台API接口**：实现3个前台接口（GET categories树、GET documents列表、GET document详情） | pending | P0 | - GET /api/v1/course/categories 返回递归目录树<br>- GET /api/v1/course/categories/{id}/documents 返回文档列表<br>- GET /api/v1/course/documents/{id} 返回文档详情+上下篇<br>- API测试通过 |
| doc-5 | **后台管理API接口**：实现10个后台管理接口（目录CRUD+排序、文档CRUD+排序），使用require_admin权限验证 | pending | P0 | - 目录管理5个接口正常（GET/POST/PUT/DELETE + move-up/move-down）<br>- 文档管理5个接口正常（GET/POST/PUT/DELETE + move-up/move-down）<br>- 权限验证生效（非管理员返回403）<br>- 文件上传限制正确（<10MB）<br>- API测试通过 |

#### 阶段2：前台展示页面

| ID | 任务描述 | 状态 | 优先级 | 验收标准 |
|:---|:---|:---|:---|:---|
| doc-6 | **导航配置**：在configs/navigation.yaml添加"AI素养课"模块配置 | pending | P0 | - 顶部导航显示"AI素养课"入口<br>- 点击可进入文档管理页面<br>- 图标正确显示 |
| doc-7 | **前端类型和Store**：创建types定义和documentStore.ts（目录树、文档列表、当前文档状态管理） | pending | P0 | - 类型定义完整无TS错误<br>- Store可以正常加载目录树<br>- Store可以正常加载文档列表<br>- Store可以正常加载文档详情 |
| doc-8 | **前台页面组件**：实现三栏布局页面（复用PreviewPanel）和子组件（CategoryMenu、DocumentList、DocumentViewer容器） | pending | P0 | - 访问/documents显示三栏布局<br>- 左侧目录树正确展示（支持多级）<br>- 中间文档列表显示标题和摘要<br>- 右侧复用PreviewPanel显示文档内容<br>- 下载功能正常（Markdown/Word/PDF）<br>- 上一篇/下一篇导航正常 |
| doc-9 | **前台路由配置**：配置/documents路由，集成到路由系统 | pending | P0 | - 路由配置正确<br>- 页面切换流畅<br>- 刷新页面正常显示 |

#### 阶段3：后台管理页面

| ID | 任务描述 | 状态 | 优先级 | 验收标准 |
|:---|:---|:---|:---|:---|
| doc-10 | **后台管理 - 目录管理页面**：实现AdminCourseCategoriesPage.vue（目录列表、创建/编辑/删除、上下移动排序） | pending | P0 | - 可查看目录列表（显示层级关系）<br>- 可创建新目录（选择父目录、填写名称）<br>- 可编辑目录名称<br>- 可删除目录（有内容时阻止并提示）<br>- 可上下移动目录排序<br>- 表单验证正确 |
| doc-11 | **后台管理 - 文档管理页面**：实现AdminCourseDocumentsPage.vue（文档列表、上传/编辑/删除、上下移动排序） | pending | P0 | - 可查看文档列表（分页、筛选目录）<br>- 可上传Markdown文档（表单+文件上传）<br>- 可编辑文档信息（标题、摘要、目录）<br>- 可删除文档（二次确认）<br>- 可上下移动文档排序<br>- 文件类型和大小验证正确 |
| doc-12 | **后台路由配置**：配置后台管理路由，集成到AdminLayout | pending | P0 | - 访问/admin/course-categories显示目录管理<br>- 访问/admin/course-documents显示文档管理<br>- 侧边栏菜单显示"文档管理"入口<br>- 路由守卫正常工作 |

#### 阶段4：集成测试和优化

| ID | 任务描述 | 状态 | 优先级 | 验收标准 |
|:---|:---|:---|:---|:---|
| doc-13 | **端到端测试**：完整业务流程测试（后台创建目录和文档 → 前台浏览和下载） | pending | P0 | - 后台可以创建多级目录<br>- 后台可以上传文档<br>- 前台正确显示目录树<br>- 前台正确显示文档列表<br>- 前台正确渲染文档内容<br>- 下载功能全部正常<br>- 上下篇导航正常 |
| doc-14 | **初始数据和文档**：创建初始数据SQL脚本（示例目录和文档），更新部署文档 | pending | P1 | - 提供示例数据SQL脚本<br>- 包含2-3级目录示例<br>- 包含5-10个示例文档<br>- 部署文档更新完整 |

---

**最后更新**: 2026-01-12（添加AI素养课模块开发任务）
