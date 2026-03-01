# 接口层完整迁移计划

**创建日期**: 2026-03-01
**目标**: 将所有路由从旧架构（`routers/`）迁移到新DDD架构（`interfaces/`）
**策略**: 分3批完成，每批独立测试验证

---

## 📋 背景

### 当前问题
- 路由分裂：50%在新架构，50%在旧架构
- 依赖混乱：新代码依赖旧代码
- 维护困难：不知道该在哪个目录添加新功能
- 违背DDD原则：新旧架构混杂

### 迁移目标
```
✅ 旧架构 routers/ → 完全清空（保留dependencies.py）
✅ 新架构 interfaces/ → 100%完成
✅ 架构统一，边界清晰
✅ 所有测试通过（866+）
```

### 当前完成度
- **接口层**: ~24% (944行/4007行)
- **待迁移**: 2900行代码，68个API端点

---

## 🎯 总体策略

### 迁移原则
1. **分批进行**：每批独立测试，降低风险
2. **保持测试通过**：每批完成后所有测试必须通过
3. **遵循DDD**：使用interfaces层标准模式
4. **保留dependencies.py**：旧架构的依赖注入桥接层

### 新架构标准模式
```python
# interfaces/routers/{module}/{feature}.py
from fastapi import APIRouter, Depends
from src.interfaces.auth import get_current_user
from src.interfaces.dependencies import get_xxx_service

router = APIRouter()

@router.post("/path")
async def endpoint(
    current_user: Annotated[UserInfo, Depends(get_current_user)]
):
    service = get_xxx_service()
    # 业务逻辑
    return response
```

---

## 📦 第1批：高优先级核心功能

**目标**: 迁移核心认证和会话管理功能
**预计时间**: 2-3小时
**风险**: 高（涉及核心功能）

### Task 1.1: 迁移认证路由 (auth.py)
**文件**: `routers/auth.py` (125行)
**目标**: `interfaces/routers/auth/auth.py`

**端点列表**:
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息

**迁移要求**:
1. 创建 `interfaces/routers/auth/` 目录
2. 创建 `auth.py` 文件，迁移所有端点
3. 使用 `interfaces/auth.py` 中的 `get_current_user`（已存在）
4. 使用 `interfaces/dependencies.py` 获取服务
5. 删除旧 `routers/auth.py`
6. 在 `main.py` 中注册新路由
7. 运行测试验证

**验收标准**:
- ✅ 所有端点功能不变
- ✅ 866个测试全部通过
- ✅ 新架构代码符合DDD规范
- ✅ 旧文件已删除

### Task 1.2: 迁移会话管理路由 (sessions.py)
**文件**: `routers/sessions.py` (129行)
**目标**: `interfaces/routers/sessions/sessions.py`

**端点列表**:
- `GET /api/v1/sessions/{session_id}` - 获取会话详情
- `DELETE /api/v1/sessions/{session_id}` - 删除会话

**注意**:
- 部分功能已在 `interfaces/routers/tools/conversations.py` 实现
- 需要检查是否有重复
- 如果重复，只保留新架构中的实现

**迁移要求**:
1. 检查与 `conversations.py` 的功能重叠
2. 迁移未实现的端点
3. 或删除已在新架构中的端点
4. 更新main.py路由注册
5. 运行测试验证

**验收标准**:
- ✅ 所有端点功能不变
- ✅ 866个测试全部通过
- ✅ 无功能重复

### Task 1.3: 清理tools.py剩余部分
**文件**: `routers/tools.py` (600行)
**目标**: 删除已在新架构中实现的端点

**已迁移的端点**（需要删除）:
- `GET /tools` → `interfaces/routers/tools/list.py`
- `GET /toolsets/{toolset_id}/tools` → `interfaces/routers/tools/list.py`
- `POST /tools/{tool_id}/chat/stream` → `interfaces/routers/tools/chat.py`
- `POST /tools/{tool_id}/chat` → `interfaces/routers/tools/chat.py`
- `GET /tools/{tool_id}/conversations` → `interfaces/routers/tools/conversations.py`
- `DELETE /tools/{tool_id}/conversations/{conv_id}` → `interfaces/routers/tools/conversations.py`
- `GET /tools/{tool_id}/conversations/{conv_id}` → `interfaces/routers/tools/conversations.py`
- `POST /tools/{tool_id}/generate-media` → `interfaces/routers/tools/media.py`

**剩余端点**（需要迁移或确认是否使用）:
- 检查是否有其他未迁移的端点
- 如果有，迁移到新架构
- 如果没有，删除整个tools.py文件

**验收标准**:
- ✅ 旧tools.py已删除或仅保留未迁移端点
- ✅ 866个测试全部通过
- ✅ 前端功能不受影响

---

## 📦 第2批：中优先级用户管理

**目标**: 迁移用户和管理员功能
**预计时间**: 1-2小时
**风险**: 中

### Task 2.1: 迁移用户管理路由 (users.py)
**文件**: `routers/users.py` (265行)
**目标**: `interfaces/routers/users/users.py`

**端点列表**:
- `GET /api/v1/admin/users` - 获取用户列表
- `GET /api/v1/admin/users/{user_id}` - 获取用户详情
- `PUT /api/v1/admin/users/{user_id}` - 更新用户信息
- `DELETE /api/v1/admin/users/{user_id}` - 删除用户

**迁移要求**:
1. 创建 `interfaces/routers/users/` 目录
2. 创建 `users.py` 文件
3. 添加管理员权限验证
4. 运行测试验证

**验收标准**:
- ✅ 所有端点功能不变
- ✅ 866个测试全部通过
- ✅ 管理员权限验证正确

### Task 2.2: 迁移管理员工具路由 (admin_tools.py)
**文件**: `routers/admin_tools.py` (429行)
**目标**: `interfaces/routers/admin/tools.py`

**端点列表**:
- `GET /api/v1/admin/common-tools` - 获取内置工具列表
- `POST /api/v1/admin/common-tools` - 创建内置工具
- `PUT /api/v1/admin/common-tools/{tool_id}` - 更新内置工具
- `DELETE /api/v1/admin/common-tools/{tool_id}` - 删除内置工具
- `GET /api/v1/admin/tool-categories` - 获取工具分类
- `POST /api/v1/admin/tool-categories` - 创建工具分类
- `PUT /api/v1/admin/tool-categories/{category_id}` - 更新工具分类
- `DELETE /api/v1/admin/tool-categories/{category_id}` - 删除工具分类

**迁移要求**:
1. 创建 `interfaces/routers/admin/` 目录
2. 创建 `tools.py` 文件
3. 添加管理员权限验证
4. 运行测试验证

**验收标准**:
- ✅ 所有端点功能不变
- ✅ 866个测试全部通过
- ✅ 管理员权限验证正确

---

## 📦 第3批：低优先级业务功能

**目标**: 迁移剩余业务功能
**预计时间**: 1-2小时
**风险**: 低

### Task 3.1: 迁移教案作品路由 (works.py)
**文件**: `routers/works.py` (475行)
**目标**: `interfaces/routers/works/works.py`

**端点列表**:
- `GET /api/v1/works` - 获取教案列表
- `GET /api/v1/works/{work_id}` - 获取教案详情
- `POST /api/v1/works` - 创建教案
- `PUT /api/v1/works/{work_id}` - 更新教案
- `DELETE /api/v1/works/{work_id}` - 删除教案
- `GET /api/v1/work-categories` - 获取教案分类
- `POST /api/v1/work-categories` - 创建教案分类

**迁移要求**:
1. 创建 `interfaces/routers/works/` 目录
2. 创建 `works.py` 文件
3. 运行测试验证

**验收标准**:
- ✅ 所有端点功能不变
- ✅ 866个测试全部通过

### Task 3.2: 迁移课程文档路由 (courses.py)
**文件**: `routers/courses.py` (471行)
**目标**: `interfaces/routers/courses/courses.py`

**端点列表**:
- `GET /api/v1/documents` - 获取课程文档树
- `GET /api/v1/documents/{category_id}` - 获取分类详情
- `POST /api/v1/documents` - 创建课程文档
- `PUT /api/v1/documents/{category_id}` - 更新课程文档
- `DELETE /api/v1/documents/{category_id}` - 删除课程文档

**迁移要求**:
1. 创建 `interfaces/routers/courses/` 目录
2. 创建 `courses.py` 文件
3. 运行测试验证

**验收标准**:
- ✅ 所有端点功能不变
- ✅ 866个测试全部通过

### Task 3.3: 清理common.py
**文件**: `routers/common.py` (431行)

**分析**:
- 该文件包含媒体生成相关端点
- 功能已被 `interfaces/routers/tools/media.py` 替代
- 需要确认前端是否还在使用旧端点

**操作**:
1. 检查前端是否使用common.py中的端点
2. 如果未使用，直接删除
3. 如果仍在使用，将前端切换到新端点后删除
4. 运行测试验证

**验收标准**:
- ✅ 旧common.py已删除
- ✅ 866个测试全部通过
- ✅ 前端功能不受影响

---

## 🎯 最终验收

### 完成标准
1. ✅ 旧架构 `routers/` 仅保留 `dependencies.py` 和 `__init__.py`
2. ✅ 所有路由都在 `interfaces/routers/` 中
3. ✅ 866个测试全部通过
4. ✅ 接口层完成度达到 100%
5. ✅ 前端功能完全正常

### 最终清理
- 删除空的 `__pycache__` 目录
- 更新架构文档
- 提交代码

---

## 📊 进度跟踪

| 批次 | 任务 | 状态 | 完成时间 |
|------|------|------|----------|
| 第1批 | Task 1.1: 认证路由迁移 | ⏳ 待开始 | - |
| 第1批 | Task 1.2: 会话管理迁移 | ⏳ 待开始 | - |
| 第1批 | Task 1.3: 清理tools.py | ⏳ 待开始 | - |
| 第2批 | Task 2.1: 用户管理迁移 | ⏳ 待开始 | - |
| 第2批 | Task 2.2: 管理员工具迁移 | ⏳ 待开始 | - |
| 第3批 | Task 3.1: 教案作品迁移 | ⏳ 待开始 | - |
| 第3批 | Task 3.2: 课程文档迁移 | ⏳ 待开始 | - |
| 第3批 | Task 3.3: 清理common.py | ⏳ 待开始 | - |

---

**计划创建人**: Claude Code
**计划版本**: v1.0
**最后更新**: 2026-03-01
