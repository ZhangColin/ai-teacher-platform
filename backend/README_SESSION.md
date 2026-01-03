# 会话管理模块 - 快速启动指南

## 1. 数据库迁移

在开始使用会话管理功能之前，需要先创建数据库表。

### 方式一：使用 Alembic 迁移（推荐）

```bash
cd backend
source ai-teacher-platform-backend/bin/activate
alembic upgrade head
```

### 方式二：手动执行 SQL

如果 Alembic 迁移失败，可以手动执行 SQL：

```bash
mysql -u root -p ai_teacher_platform < migrations/create_sessions_tables.sql
```

## 2. 验证表创建

执行以下 SQL 验证表是否创建成功：

```sql
SHOW TABLES;
-- 应该看到：users, sessions, messages, artifacts

DESCRIBE sessions;
DESCRIBE messages;
DESCRIBE artifacts;
```

## 3. 启动服务

```bash
cd backend
source ai-teacher-platform-backend/bin/activate
uvicorn src.main:app --reload
```

## 4. API 接口

### 4.1 获取历史对话列表
```
GET /api/v1/tools/{tool_id}/conversations
```

### 4.2 获取会话详情
```
GET /api/v1/sessions/{session_id}
```

### 4.3 更新会话标题
```
PATCH /api/v1/sessions/{session_id}
Body: { "title": "新标题" }
```

### 4.4 删除会话
```
DELETE /api/v1/sessions/{session_id}
```

### 4.5 对话交互（延迟创建会话）
```
POST /api/v1/tools/{tool_id}/chat
Body: {
  "message": "用户消息",
  "session_id": null  // 首次调用为 null，自动创建会话
}
```

## 5. 功能特性

- ✅ 会话延迟创建：用户发送第一条消息时才创建会话
- ✅ 会话自动命名：基于第一条消息的前50个字符自动生成标题
- ✅ 消息持久化：所有消息保存到数据库
- ✅ 会话恢复：刷新页面后可通过 API 恢复会话列表和消息历史
- ✅ 用户隔离：每个用户只能访问自己的会话

## 6. 注意事项

- 所有 API 都需要 JWT Token 认证
- 会话删除会级联删除关联的消息和成果物
- 会话标题最大长度为 200 个字符

