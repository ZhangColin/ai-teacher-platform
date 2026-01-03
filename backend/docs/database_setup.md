# 数据库配置和初始化指南

## 1. 数据库配置位置

### 1.1 配置文件位置

数据库配置位于 `backend/src/database.py`，通过环境变量 `DATABASE_URL` 读取。

### 1.2 环境变量配置

**推荐方式**：在 `backend/` 目录下创建 `.env` 文件（不要提交到 Git）

**快速开始**：
```bash
cd backend
cp .env.example .env
# 然后编辑 .env 文件，修改为你的实际配置
```

**配置说明**：
- `.env.example` 是配置模板文件（已提交到版本控制）
- `.env` 是实际配置文件（已添加到 `.gitignore`，不会提交）
- 复制 `.env.example` 为 `.env` 后，修改其中的配置值

**配置项说明**：
```bash
# 数据库连接字符串
DATABASE_URL=mysql+pymysql://用户名:密码@主机:端口/数据库名?charset=utf8mb4

# JWT 密钥（用于生成和验证 Token）
JWT_SECRET_KEY=your-secret-key-change-in-production
```

**示例**：
```bash
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/ai_teacher_platform?charset=utf8mb4
JWT_SECRET_KEY=your-secret-key-change-in-production
```

**注意**：
- `.env` 文件应添加到 `.gitignore`，不要提交到版本控制
- `.env.example` 是模板文件，可以提交到版本控制
- 生产环境必须使用强随机字符串作为 `JWT_SECRET_KEY`
- 生成强随机密钥：`python -c "import secrets; print(secrets.token_urlsafe(32))"`

### 1.3 默认配置

如果未设置 `DATABASE_URL` 环境变量，系统会使用默认值：
```
mysql+pymysql://root:password@localhost:3306/ai_teacher_platform?charset=utf8mb4
```

## 2. 数据库初始化

### 2.1 使用 Alembic 进行数据库迁移

项目使用 **Alembic** 进行数据库版本管理和迁移。

#### 2.1.1 初始化 Alembic（已完成）

Alembic 已经初始化，配置文件位于：
- `backend/alembic.ini` - Alembic 主配置文件
- `backend/alembic/env.py` - Alembic 环境配置（已配置为使用项目的数据库配置）
- `backend/alembic/versions/` - 迁移文件目录

#### 2.1.2 创建数据库

首先，确保 MySQL 服务已启动，然后创建数据库：

```sql
CREATE DATABASE ai_teacher_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 2.1.3 配置环境变量

在 `backend/.env` 文件中配置数据库连接：

```bash
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/ai_teacher_platform?charset=utf8mb4
```

#### 2.1.4 运行数据库迁移

```bash
cd backend
source ai-teacher-platform-backend/bin/activate
alembic upgrade head
```

这会创建所有表结构（当前包括 `users` 表）。

#### 2.1.5 查看迁移历史

```bash
alembic history
```

#### 2.1.6 回滚迁移

如果需要回滚到上一个版本：

```bash
alembic downgrade -1
```

### 2.2 创建新的迁移

当数据模型发生变化时，创建新的迁移：

```bash
# 自动生成迁移（推荐）
alembic revision --autogenerate -m "描述信息"

# 手动创建迁移
alembic revision -m "描述信息"
```

**注意**：自动生成迁移需要数据库连接正常，如果数据库未配置，可以手动创建迁移文件。

### 2.3 验证数据库表

迁移完成后，可以验证表是否创建成功：

```sql
USE ai_teacher_platform;
SHOW TABLES;
DESCRIBE users;
```

## 3. 开发环境快速启动

### 3.1 首次设置

1. **创建 `.env` 文件**：
   ```bash
   cd backend
   cp .env.example .env  # 如果存在 .env.example
   # 或手动创建 .env 文件
   ```

2. **编辑 `.env` 文件**，设置正确的数据库连接信息

3. **创建数据库**：
   ```sql
   CREATE DATABASE ai_teacher_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

4. **运行迁移**：
   ```bash
   alembic upgrade head
   ```

### 3.2 日常开发

数据库迁移已配置，日常开发中：

- **修改数据模型**：在 `backend/src/db_models.py` 中修改模型
- **创建迁移**：运行 `alembic revision --autogenerate -m "描述"`
- **应用迁移**：运行 `alembic upgrade head`

## 4. 测试环境

测试使用 SQLite 内存数据库，无需额外配置。测试会自动创建和清理数据库。

## 5. 生产环境

生产环境部署时：

1. **设置环境变量**：通过系统环境变量或容器环境变量设置 `DATABASE_URL`
2. **运行迁移**：在应用启动前运行 `alembic upgrade head`
3. **备份数据库**：定期备份生产数据库

## 6. 常见问题

### 6.1 数据库连接失败

**错误**：`Access denied for user 'root'@'localhost'`

**解决**：
- 检查 MySQL 服务是否启动
- 检查用户名和密码是否正确
- 检查数据库是否存在
- 确认用户有访问权限

### 6.2 迁移失败

**错误**：表已存在

**解决**：
- 检查数据库是否已有表结构
- 如果需要重新开始，可以删除数据库后重新创建
- 或者手动调整迁移文件

### 6.3 环境变量未生效

**解决**：
- 确认 `.env` 文件在 `backend/` 目录下
- 确认 `.env` 文件格式正确（无多余空格）
- 重启应用或重新加载环境变量

---

## 7. 创建系统初始化用户

### 7.1 使用初始化脚本（推荐）

系统提供了独立的初始化脚本，可以直接创建系统初始化用户：

```bash
cd backend
source ai-teacher-platform-backend/bin/activate
python scripts/create_initial_user.py
```

**脚本功能**：
- 检查用户是否已存在（通过用户名、邮箱或手机号）
- 如果不存在，自动创建初始化用户
- 如果已存在，显示用户信息并跳过创建

**初始化用户信息**：
- 用户名：`colin`
- 密码：`Hcy@2026`
- 昵称：`文野`
- 邮箱：`zhangjinhua@aieducenter.com`
- 手机：`18001828301`

**登录方式**：
- 可以使用用户名 `colin` 登录
- 可以使用邮箱 `zhangjinhua@aieducenter.com` 登录
- 可以使用手机号 `18001828301` 登录

### 7.2 通过数据库迁移自动创建

执行数据库迁移时，会自动创建初始化用户（如果不存在）：

```bash
cd backend
source ai-teacher-platform-backend/bin/activate
alembic upgrade head
```

迁移脚本 `4a7fcb1183df_create_initial_admin_user.py` 会在迁移时自动创建初始化用户。

**注意**：两种方式都会检查用户是否已存在，不会重复创建。

