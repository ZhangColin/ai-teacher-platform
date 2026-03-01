# 旧路由层迁移评估报告

**生成时间**: 2026-03-01
**评估范围**: backend/src/routers/ → backend/src/interfaces/routers/
**评估者**: Claude Code Subagent

---

## 一、执行摘要

### 当前状态
- **旧路由文件**: 9个（共80个端点）
- **新路由文件**: 3个（已迁移6个端点）
- **迁移进度**: 7.5% (6/80)

### 核心发现
1. **已完成迁移**: 工具列表、对话、会话管理（tools.py部分功能）
2. **仍在使用**: 所有其他路由模块（auth, users, admin_tools, works, courses, sessions, common）
3. **未迁移原因**: tools.py中的2个端点仍被前端使用
   - `GET /common-tools` - 常用工具列表（前端CommonToolsView使用）
   - `POST /tools/{tool_id}/generate-media` - 媒体生成（前端MediaChatInterface使用）

---

## 二、详细路由清单

### 2.1 已迁移到interfaces层的路由

#### backend/src/interfaces/routers/tools/

**1. list.py** (2个端点)
- ✅ `GET /tools` - 获取所有工具列表
- ✅ `GET /toolsets/{toolset_id}/tools` - 按工具集获取工具

**2. chat.py** (2个端点)
- ✅ `POST /tools/{tool_id}/chat` - 非流式对话
- ✅ `POST /tools/{tool_id}/chat/stream` - SSE流式对话

**3. conversations.py** (2个端点)
- ✅ `GET /tools/{tool_id}/conversations` - 会话列表
- ✅ `DELETE /tools/{tool_id}/conversations/{conv_id}` - 删除会话

**迁移特点**:
- 采用DDD分层架构（interfaces → application → domain → infrastructure）
- 使用依赖注入（通过interfaces/dependencies.py桥接）
- 统一错误处理（error_handler中间件）
- 符合RESTful设计规范

---

### 2.2 仍在routers中的路由

#### backend/src/routers/tools.py (9个端点)

**未迁移端点**:
- ⚠️ `GET /common-tools` - **常用工具列表**（前端依赖）
  - 使用: frontend/src/views/CommonToolsView.vue
  - API调用: `apiClient.get('/common-tools/categories')`
  - 状态: **需要保留或迁移**

- ⚠️ `POST /tools/{tool_id}/generate-media` - **媒体生成**（前端依赖）
  - 使用: frontend/src/components/media/MediaChatInterface.vue
  - API调用: `mediaApi.generateMedia(toolId, params)`
  - 状态: **需要保留或迁移**

- 🔄 `GET /tools/{tool_id}/chat` - 获取工具对话信息（OPTIONS请求等）
  - 状态: **可废弃**

**已迁移端点**（重复注册，需清理）:
- ✅ `GET /tools` → interfaces/routers/tools/list.py
- ✅ `GET /toolsets/{toolset_id}/tools` → interfaces/routers/tools/list.py
- ✅ `POST /tools/{tool_id}/chat` → interfaces/routers/tools/chat.py
- ✅ `POST /tools/{tool_id}/chat/stream` → interfaces/routers/tools/chat.py
- ✅ `GET /tools/{tool_id}/conversations` → interfaces/routers/tools/conversations.py
- ✅ `DELETE /tools/{tool_id}/conversations/{conv_id}` → interfaces/routers/tools/conversations.py

**问题**: 旧tools.py仍被注册在main.py中，造成端点重复注册。

---

#### backend/src/routers/auth.py (2个端点)
- `POST /login` - 用户登录
- `GET /me` - 获取当前用户信息

**状态**: 未迁移，建议**高优先级迁移**

---

#### backend/src/routers/users.py (6个端点)
- `GET /admin/users` - 用户列表
- `POST /admin/users` - 创建用户
- `GET /admin/users/{user_id}` - 用户详情
- `PATCH /admin/users/{user_id}` - 更新用户
- `DELETE /admin/users/{user_id}` - 删除用户
- `POST /admin/users/{user_id}/reset-password` - 重置密码

**状态**: 未迁移，建议**中优先级迁移**

---

#### backend/src/routers/admin_tools.py (14个端点)

**通用工具管理**:
- `GET /admin/common-tools` - 工具列表
- `POST /admin/common-tools/built-in` - 创建内置工具
- `POST /admin/common-tools/html` - 创建HTML工具
- `PATCH /admin/common-tools/{tool_id}` - 更新工具
- `DELETE /admin/common-tools/{tool_id}` - 删除工具
- `POST /admin/common-tools/{tool_id}/move-up` - 上移工具
- `POST /admin/common-tools/{tool_id}/move-down` - 下移工具
- `POST /admin/common-tools/{tool_id}/toggle-visibility` - 切换可见性

**工具分类管理**:
- `GET /admin/tool-categories` - 分类列表
- `POST /admin/tool-categories` - 创建分类
- `PATCH /admin/tool-categories/{category_id}` - 更新分类
- `DELETE /admin/tool-categories/{category_id}` - 删除分类
- `POST /admin/tool-categories/{category_id}/move-up` - 上移分类
- `POST /admin/tool-categories/{category_id}/move-down` - 下移分类

**状态**: 未迁移，建议**中优先级迁移**

---

#### backend/src/routers/works.py (15个端点)

**教案学案**:
- `GET /works/categories` - 分类列表
- `GET /works/{work_id}` - 教案详情

**管理员功能**:
- `GET /admin/works` - 教案列表
- `POST /admin/works` - 创建教案
- `PATCH /admin/works/{work_id}` - 更新教案
- `DELETE /admin/works/{work_id}` - 删除教案
- `POST /admin/works/{work_id}/move-up` - 上移教案
- `POST /admin/works/{work_id}/move-down` - 下移教案
- `POST /admin/works/{work_id}/toggle-visibility` - 切换可见性

**分类管理**:
- `GET /admin/work-categories` - 分类列表
- `POST /admin/work-categories` - 创建分类
- `PATCH /admin/work-categories/{category_id}` - 更新分类
- `DELETE /admin/work-categories/{category_id}` - 删除分类
- `POST /admin/work-categories/{category_id}/move-up` - 上移分类
- `POST /admin/work-categories/{category_id}/move-down` - 下移分类

**状态**: 未迁移，建议**中优先级迁移**

---

#### backend/src/routers/courses.py (15个端点)

**课程文档**:
- `GET /documents/categories` - 分类树
- `GET /documents/category/{category_id}/documents` - 文档列表
- `GET /documents/{doc_id}` - 文档详情

**管理员功能**:
- `GET /admin/course-categories` - 分类列表
- `POST /admin/course-categories` - 创建分类
- `PATCH /admin/course-categories/{category_id}` - 更新分类
- `DELETE /admin/course-categories/{category_id}` - 删除分类
- `POST /admin/course-categories/{category_id}/move-up` - 上移分类
- `POST /admin/course-categories/{category_id}/move-down` - 下移分类

**文档管理**:
- `GET /admin/course-documents` - 文档列表
- `POST /admin/course-documents` - 创建文档
- `PATCH /admin/course-documents/{doc_id}` - 更新文档
- `DELETE /admin/course-documents/{doc_id}` - 删除文档
- `POST /admin/course-documents/{doc_id}/move-up` - 上移文档
- `POST /admin/course-documents/{doc_id}/move-down` - 下移文档

**状态**: 未迁移，建议**低优先级迁移**（业务相对独立）

---

#### backend/src/routers/sessions.py (4个端点)
- `GET /sessions/{session_id}` - 会话详情
- `PATCH /sessions/{session_id}` - 更新会话
- `DELETE /sessions/{session_id}` - 删除会话
- `GET /agents/{agent_id}/sessions` - Agent会话列表（已废弃）

**状态**: 未迁移，建议**高优先级迁移**

---

#### backend/src/routers/common.py (5个端点)
- `GET /navigation` - 导航配置
- `POST /convert/markdown-to-word` - Markdown转Word
- `GET /tasks/{task_id}` - 任务状态查询
- `GET /common-tools/categories` - 常用工具分类
- `GET /common-tools/tools/{tool_id}` - 常用工具详情

**状态**: 未迁移，建议**低优先级迁移**（工具性质较强）

---

#### backend/src/routers/dependencies.py (0个端点)
- 状态: **依赖注入文件，不需要迁移**

---

## 三、迁移建议与优先级

### 3.1 立即处理（P0 - 阻塞问题）

#### 问题1: tools.py端点重复注册
**现状**: 旧tools.py中的6个已迁移端点仍在main.py中注册

**影响**:
- 端点冲突（虽然FastAPI后注册覆盖先注册）
- 代码混乱（新旧路由并存）
- 维护困难

**解决方案**:
```python
# main.py 中删除或注释以下行：
# app.include_router(tools_router)  # 第86行

# 或者：从tools.py中删除已迁移的6个端点
```

**建议**: **立即清理**，避免混淆

---

#### 问题2: tools.py中2个被前端依赖的端点

**选项A: 迁移到interfaces层**
```python
# backend/src/interfaces/routers/tools/
# ├── list.py (已存在)
# ├── chat.py (已存在)
# ├── conversations.py (已存在)
# ├── common.py (新建) - GET /common-tools
# └── media.py (新建) - POST /tools/{tool_id}/generate-media
```

**优点**:
- 统一架构（所有工具相关路由在interfaces层）
- 符合DDD分层原则

**缺点**:
- 需要更新前端API调用路径
- 测试工作量大

**选项B: 保留在旧routers层**
```python
# backend/src/routers/tools.py (精简版)
# 只保留：
# - GET /common-tools
# - POST /tools/{tool_id}/generate-media
```

**优点**:
- 最小化变更
- 前端无需修改

**缺点**:
- 架构不统一
- 长期维护困难

**建议**: **选项A（迁移）**，理由：
1. 只有2个端点，迁移成本低
2. 前端API调用只需要更新路径（/api/v1/common-tools → /api/v1/tools/common）
3. 统一架构对长期维护有利

---

### 3.2 高优先级迁移（P1 - 核心功能）

#### 1. auth.py (2个端点)
**原因**: 认证是核心功能，应优先迁移

**建议结构**:
```python
# backend/src/interfaces/routers/auth/
# ├── __init__.py
# ├── login.py - POST /login
# └── me.py - GET /me
```

---

#### 2. sessions.py (4个端点)
**原因**: 会话管理是核心功能，与已迁移的tools/chat紧密相关

**建议结构**:
```python
# backend/src/interfaces/routers/sessions/
# ├── __init__.py
# ├── detail.py - GET/PATCH/DELETE /sessions/{session_id}
# └── list.py - GET /agents/{agent_id}/sessions (废弃)
```

---

### 3.3 中优先级迁移（P2 - 管理功能）

#### 1. admin_tools.py (14个端点)
**原因**: 管理员功能，需要规范化

**建议结构**:
```python
# backend/src/interfaces/routers/admin/
# ├── tools/
# │   ├── __init__.py
# │   ├── list.py - GET /admin/common-tools
# │   ├── create_built_in.py - POST /admin/common-tools/built-in
# │   ├── create_html.py - POST /admin/common-tools/html
# │   ├── update.py - PATCH /admin/common-tools/{tool_id}
# │   ├── delete.py - DELETE /admin/common-tools/{tool_id}
# │   └── categories/
# │       ├── __init__.py
# │       ├── list.py - GET /admin/tool-categories
# │       ├── create.py - POST /admin/tool-categories
# │       └── ...
```

---

#### 2. works.py (15个端点)
**原因**: 教案管理是核心业务功能

**建议结构**:
```python
# backend/src/interfaces/routers/works/
# ├── public/
# │   ├── categories.py - GET /works/categories
# │   └── detail.py - GET /works/{work_id}
# └── admin/
#     ├── list.py - GET /admin/works
#     ├── create.py - POST /admin/works
#     └── ...
```

---

#### 3. users.py (6个端点)
**原因**: 用户管理是基础功能

**建议结构**:
```python
# backend/src/interfaces/routers/admin/
# └── users/
#     ├── __init__.py
#     ├── list.py - GET /admin/users
#     ├── create.py - POST /admin/users
#     └── ...
```

---

### 3.4 低优先级迁移（P3 - 边缘功能）

#### 1. courses.py (15个端点)
**原因**: 课程文档模块相对独立，可延后迁移

---

#### 2. common.py (5个端点)
**原因**: 通用工具性质，功能杂散，可延后迁移

---

## 四、迁移路线图

### Phase 1: 清理重复注册（1小时）
- [ ] 从main.py删除tools_router注册
- [ ] 或从tools.py删除已迁移的6个端点
- [ ] 验证测试全部通过

### Phase 2: 迁移tools.py剩余端点（4小时）
- [ ] 创建interfaces/routers/tools/common.py
- [ ] 创建interfaces/routers/tools/media.py
- [ ] 更新前端API调用路径
- [ ] 集成测试验证
- [ ] 删除旧tools.py

### Phase 3: 迁移核心功能（8小时）
- [ ] 迁移auth.py (2h)
- [ ] 迁移sessions.py (2h)
- [ ] 迁移users.py (2h)
- [ ] 集成测试验证 (2h)

### Phase 4: 迁移管理功能（12小时）
- [ ] 迁移admin_tools.py (4h)
- [ ] 迁移works.py (4h)
- [ ] 集成测试验证 (4h)

### Phase 5: 迁移边缘功能（8小时）
- [ ] 迁移courses.py (4h)
- [ ] 迁移common.py (4h)

**总计**: 约33小时（4-5个工作日）

---

## 五、风险评估

### 高风险
- **tools.py端点删除**: 可能导致前端功能中断
  - 缓解措施: 充分测试，灰度发布

### 中风险
- **auth.py迁移**: 认证功能故障导致用户无法登录
  - 缓解措施: 先在测试环境验证，保留回滚方案

### 低风险
- **其他路由迁移**: 业务影响相对较小
  - 缓解措施: 逐个迁移，充分测试

---

## 六、总结与建议

### 当前问题
1. ✅ 新旧路由并存，架构混乱
2. ⚠️ 端点重复注册，维护困难
3. 🔄 tools.py中2个端点未迁移（前端依赖）

### 核心建议
1. **立即处理**: 清理tools.py重复注册（P0）
2. **短期目标**: 迁移tools.py剩余端点（P0）
3. **中期目标**: 迁移核心功能（auth, sessions, users）（P1）
4. **长期目标**: 完成所有路由迁移（P2-P3）

### 架构建议
- **统一分层**: 所有路由都应遵循DDD分层架构
- **模块化**: 按业务领域拆分路由文件（tools/admin/works/courses）
- **依赖注入**: 使用interfaces/dependencies.py统一管理依赖
- **错误处理**: 所有新路由使用error_handler中间件

### 测试策略
- **单元测试**: 每个路由文件必须有对应的测试文件
- **集成测试**: 验证端到端功能
- **E2E测试**: 使用Playwright验证前端交互

---

## 附录：端点统计表

| 路由文件 | 端点数 | 已迁移 | 未迁移 | 迁移进度 |
|---------|--------|--------|--------|----------|
| tools.py | 9 | 6 | 3 | 67% |
| auth.py | 2 | 0 | 2 | 0% |
| users.py | 6 | 0 | 6 | 0% |
| admin_tools.py | 14 | 0 | 14 | 0% |
| works.py | 15 | 0 | 15 | 0% |
| courses.py | 15 | 0 | 15 | 0% |
| sessions.py | 4 | 0 | 4 | 0% |
| common.py | 5 | 0 | 5 | 0% |
| **总计** | **80** | **6** | **74** | **7.5%** |

---

**报告结束**
