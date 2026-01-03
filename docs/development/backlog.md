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
| auth-enhance-1 | 数据库迁移：添加 nickname 字段，username 改为唯一索引，email 改为可选 | pending | P0 |
| auth-enhance-2 | 更新后端数据模型：UserModel 添加 nickname 字段，username 添加唯一索引，email 改为可选 | pending | P0 |
| auth-enhance-3 | 更新后端领域模型：User 添加 nickname 字段，username 必填且唯一，email 改为可选，更新 create 方法 | pending | P0 |
| auth-enhance-4 | 更新 UserService：添加 get_user_by_username 方法，更新 create_user 支持 nickname，email 改为可选 | pending | P0 |
| auth-enhance-5 | 更新登录 API：支持用户名登录，账号判断优先级（手机号 > 邮箱 > 用户名） | pending | P0 |
| auth-enhance-6 | 更新创建用户 API：username 必填且唯一，nickname 可选，email 改为可选，更新验证逻辑 | pending | P0 |
| auth-enhance-7 | 更新前端类型定义：UserInfo、UserListItem、CreateUserRequest 添加 nickname 字段，email 改为可选 | pending | P0 |
| auth-enhance-8 | 更新登录页面：支持用户名登录，更新验证规则（用户名、邮箱、手机号） | pending | P0 |
| auth-enhance-9 | 更新用户列表页面：显示昵称字段（如未填写则显示用户名） | pending | P0 |
| auth-enhance-10 | 更新创建用户表单：添加昵称输入框，username 必填且唯一，email 改为可选 | pending | P0 |
| auth-enhance-11 | 更新所有测试用例：适配用户名登录和昵称字段 | pending | P0 |
| auth-enhance-12 | 更新 Header 组件：显示昵称（如未填写则显示用户名） | pending | P0 |

---

**最后更新**: 2026-01-03（添加用户登录功能增强任务）

---

## 当前迭代：工具管理和会话功能开发

**需求来源**: `docs/requirements/product_spec.md` (v4.0)  
**架构设计**: `docs/design/api_interface.md` (v2.0), `docs/design/data_models.md` (v2.0)  
**创建时间**: 2026-01-03

### 任务列表

#### 工具管理模块

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| tool-1 | 更新工具配置模型：添加 `visible`、`type`、`category`、`icon`、`welcome_message` 字段 | pending | P0 |
| tool-2 | 实现工具配置加载服务：支持按 `category` 聚合生成分类结构，只返回 `visible=true` 的工具 | pending | P0 |
| tool-3 | 实现获取工具列表API（GET /api/v1/tools）：返回按分类组织的工具列表，包含图标和分类信息 | pending | P0 |
| tool-4 | 实现工具选择器组件（AIToolSelector.vue）：从API加载工具列表，按分类展示，支持工具切换 | pending | P0 |
| tool-5 | 实现占位工具处理：点击占位工具显示"敬请期待"页面 | pending | P0 |

#### 历史对话列表模块

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| conversation-1 | 实现获取历史对话列表API（GET /api/v1/tools/{tool_id}/conversations）：按用户+工具维度查询，按更新时间倒序 | pending | P0 |
| conversation-2 | 实现历史对话列表组件（ConversationList.vue）：展示对话列表，支持点击切换对话 | pending | P0 |
| conversation-3 | 实现编辑会话标题API（PATCH /api/v1/sessions/{session_id}）：更新会话标题 | pending | P0 |
| conversation-4 | 实现删除会话API（DELETE /api/v1/sessions/{session_id}）：级联删除会话和消息 | pending | P0 |
| conversation-5 | 实现对话列表编辑功能：内联编辑标题（实时保存），删除对话（二次确认） | pending | P0 |
| conversation-6 | 实现工具切换联动：切换工具时自动切换对话列表 | pending | P0 |
| conversation-7 | 实现新建对话功能：点击"新建对话"按钮，切换到新建对话状态（显示欢迎语） | pending | P0 |

#### 会话管理模块

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| session-1 | 更新会话数据模型：添加 `title`、`updated_at` 字段，关联 `user_id` 和 `tool_id` | pending | P0 |
| session-2 | 实现会话延迟创建机制：用户进入工具时不创建会话，发送第一条消息时才创建 | pending | P0 |
| session-3 | 实现会话自动命名：基于第一条消息的前30-50个字符生成标题（前端决定长度） | pending | P0 |
| session-4 | 实现获取会话详情API（GET /api/v1/sessions/{session_id}）：返回完整消息历史 | pending | P0 |
| session-5 | 更新对话交互API（POST /api/v1/tools/{tool_id}/chat）：支持 `session_id` 可选，首次调用自动创建会话 | pending | P0 |
| session-6 | 实现欢迎语配置化展示：从工具配置读取 `welcome_message`，用户进入工具时展示 | pending | P0 |
| session-7 | 实现会话恢复功能：刷新页面后，前端调用API恢复会话列表和当前会话 | pending | P0 |

#### 预览功能模块（基础功能）

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| preview-1 | 实现代码块识别和预览按钮：识别 markdown/html/svg 代码块，显示预览按钮 | pending | P0 |
| preview-2 | 实现预览界面布局：点击预览按钮后左右分屏，左侧聊天区域，右侧预览区域 | pending | P0 |
| preview-3 | 实现Markdown预览：预览区渲染Markdown内容 | pending | P0 |
| preview-4 | 实现HTML预览：预览区使用iframe sandbox安全执行HTML内容 | pending | P0 |
| preview-5 | 实现SVG预览：预览区渲染SVG内容 | pending | P0 |
| preview-6 | 实现预览区域关闭功能：手动关闭预览区域，恢复单栏布局 | pending | P0 |

#### 预览功能模块（增强功能 - 低优先级）

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| preview-enhance-1 | 实现Markdown下载功能：下载为Markdown格式文件 | pending | P2 |
| preview-enhance-2 | 实现Markdown转Word下载功能：将Markdown内容转换为Word文档并下载 | pending | P2 |
| preview-enhance-3 | 实现Markdown转PDF下载功能：将Markdown内容转换为PDF文件并下载 | pending | P2 |
| preview-enhance-4 | 实现HTML全屏预览功能：点击全屏按钮，使用浏览器全屏API或全屏覆盖层 | pending | P2 |
| preview-enhance-5 | 实现HTML下载功能：下载HTML文件 | pending | P2 |
| preview-enhance-6 | 实现HTML截图功能：使用html2canvas或其他方案截图HTML内容 | pending | P2 |
| preview-enhance-7 | 实现SVG全屏预览功能：点击全屏按钮，使用浏览器全屏API或全屏覆盖层 | pending | P2 |
| preview-enhance-8 | 实现SVG下载功能：下载SVG文件 | pending | P2 |
| preview-enhance-9 | 实现SVG截图功能：使用html2canvas或其他方案截图SVG内容 | pending | P2 |

#### 界面交互模块

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| ui-interaction-1 | 实现工具选择器收起功能：收起为浮动图标，点击重新展开，位置固定左侧中间 | pending | P0 |
| ui-interaction-2 | 实现历史对话列表收起功能：收起为浮动图标，点击重新展开，位置固定左侧偏下（避免重叠） | pending | P0 |
| ui-interaction-3 | 完善对话交互细节：参考DeepSeek实现消息展示样式、输入框交互、加载状态、错误处理 | pending | P0 |

#### 提示词向导工具配置

| ID | 任务描述 | 状态 | 优先级 |
|:---|:---|:---|:---|
| prompt-wizard-1 | 创建提示词向导工具配置（configs/tools/prompt_wizard.yaml）：包含完整的系统提示词和配置 | pending | P0 |
| prompt-wizard-2 | 测试提示词向导工具：验证六步引导流程正常工作 | pending | P0 |

---

**最后更新**: 2026-01-03（添加工具管理和会话功能开发任务）

