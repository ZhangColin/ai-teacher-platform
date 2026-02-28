# 开发数据库设置指南

## 数据库信息

- **数据库名**: `hcy_studio`
- **主机**: `localhost:3306`
- **字符集**: `utf8mb4` / `utf8mb4_unicode_ci`

## 管理员账号

平台有两个管理员账号可供使用：

### 账号 1（系统管理员）
- **用户名**: `admin`
- **邮箱**: `admin@example.com`
- **密码**: `HcyAdmin@2026`
- **权限**: 管理员

### 账号 2（初始用户）
- **用户名**: `colin`
- **昵称**: 文野
- **邮箱**: `zhangjinhua@aieducenter.com`
- **密码**: `Hcy@2026`
- **权限**: 管理员

## 数据库表结构

已创建以下 11 个表：

1. **users** - 用户表
2. **sessions** - 会话表
3. **messages** - 消息表
4. **artifacts** - 成果物表
5. **common_tools** - 内置工具表
6. **tool_categories** - 工具分类表
7. **works** - 教案作品表
8. **work_categories** - 教案分类表
9. **course_documents** - 课程文档表
10. **course_categories** - 课程分类表
11. **alembic_version** - 数据库版本记录

## 重新初始化数据库

如需重新初始化数据库（⚠️ 会清空所有数据）：

```bash
cd backend
python3 init_db.py
# 按提示输入 y 确认删除并重建
```

## 运行数据库迁移

如果模型有变更，需要创建并运行新迁移：

```bash
cd backend

# 创建新迁移
alembic revision --autogenerate -m "描述"

# 运行迁移
alembic upgrade head
```

## 测试数据库

测试数据库隔离在 `ai_teacher_platform_test`，不会影响开发数据：

```bash
cd backend
bash scripts/setup_test_db.sh
```

## 启动服务

数据库初始化完成后，启动后端服务：

```bash
cd backend
python -m src.main
```

服务将在 http://localhost:8000 启动

## 环境配置

`.env` 文件配置示例：

```env
# 数据库
DATABASE_URL=mysql+pymysql://root:truth@localhost:3306/hcy_studio?charset=utf8mb4

# JWT
JWT_SECRET_KEY=dev-secret-key-change-in-production

# AI 模型
CURRENT_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key-here
```

## 常见问题

### 忘记管理员密码

使用 Python 重置密码：

```python
import bcrypt
import pymysql

conn = pymysql.connect(host='localhost', user='root', password='truth', database='hcy_studio')
cursor = conn.cursor()

new_password = "your_new_password"
password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

cursor.execute('UPDATE users SET password_hash = %s WHERE username = %s',
               (password_hash, 'admin'))
conn.commit()
```

### 检查数据库连接

```python
import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='truth',
    database='hcy_studio'
)
print("连接成功")
```
