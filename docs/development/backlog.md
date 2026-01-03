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

