# AI 教育平台 - 完整部署文档

> **部署目录**: `/home/studio`  
> **二级域名**: `studio.aieducenter.com`  
> **部署方式**: 传统部署（Python 虚拟环境 + Nginx 静态文件）  
> **更新命令**: `./scripts/deploy.sh`

---

## 📋 目录

- [部署概述](#部署概述)
- [第一部分：本地准备](#第一部分本地准备)
- [第二部分：服务器环境准备](#第二部分服务器环境准备)
- [第三部分：后端部署](#第三部分后端部署)
- [第四部分：前端部署](#第四部分前端部署)
- [第五部分：Nginx 配置](#第五部分nginx-配置)
- [第六部分：服务管理](#第六部分服务管理)
- [第七部分：验证部署](#第七部分验证部署)
- [第八部分：代码更新](#第八部分代码更新)
- [第九部分：常见问题](#第九部分常见问题)

---

## 部署概述

### 部署架构

```
┌─────────────────────────────────────────────────────┐
│                   服务器布局                          │
├─────────────────────────────────────────────────────┤
│                                                       │
│  Nginx (Podman 容器)  ←─ 已存在，添加新配置          │
│    ├─ / → 前端静态文件 (/home/studio/frontend-dist/)│
│    ├─ /api → 后端服务 (127.0.0.1:8000)              │
│    └─ /static → 后端静态文件                         │
│                                                       │
│  MySQL (Podman 容器)  ←─ 已存在，直接使用            │
│                                                       │
│  后端服务 (Python 虚拟环境)  ←─ 新部署               │
│    监听: 127.0.0.1:8000                              │
│    进程管理: systemd                                  │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### 核心原则

1. **本地优先**: 能在本地做的（如前端打包）就本地做
2. **服务器简单**: 服务器上只做必要的操作
3. **不影响现有服务**: 不修改现有 Nginx、MySQL 配置
4. **传统部署**: 不使用新容器，避免复杂性

---

## 第一部分：本地准备

### 1.1 确认项目结构

```bash
# 在本地项目根目录
cd /Users/zhangcolin/workspace/ai-teacher-platform

# 查看项目结构
ls -la

# 应该看到：
# backend/          # 后端代码
# frontend/         # 前端代码
# configs/          # 配置文件（工具、导航等）
# scripts/          # 部署脚本
```

### 1.2 构建前端（本地）

**重要**: 前端在本地打包好，直接上传到服务器。

```bash
# 进入前端目录
cd frontend

# 检查 Node.js 版本（需要 18+）
node --version

# 检查 pnpm（如果没有，先安装：npm install -g pnpm）
pnpm --version

# 安装依赖
pnpm install

# 构建生产版本
pnpm run build

# 检查构建结果
ls -la dist/

# 应该看到：
# dist/index.html       # 入口文件
# dist/assets/          # JS、CSS 等静态资源
```

**构建失败？**
- 检查 Node.js 版本是否 >= 18
- 检查是否有编译错误，先在本地修复
- 查看 `frontend/package.json` 的 `build` 脚本

### 1.3 准备上传清单

**需要上传的目录和文件**：

```
✅ backend/              # 后端代码（整个目录）
✅ frontend/dist/        # 前端打包后的文件（本地构建好的）
✅ configs/              # 配置文件（工具、导航等）
✅ scripts/              # 部署脚本
✅ .env.example          # 环境变量模板
```

**不需要上传**：
- ❌ `frontend/src/` - 不需要，已打包到 `dist/`
- ❌ `frontend/node_modules/` - 不需要
- ❌ `backend/__pycache__/` - Python 缓存，服务器会重新生成
- ❌ `backend/ai-teacher-platform-backend/` - 虚拟环境，服务器上重新创建

---

## 第二部分：服务器环境准备

### 2.1 连接到服务器

```bash
# 在本地执行
ssh -p <端口> <用户名>@<服务器IP>

# 示例（替换为你的实际信息）：
# ssh -p 22 root@your-server-ip
```

### 2.2 检查服务器环境

```bash
# 进入服务器后执行

# 1. 检查 Python 版本（需要 3.9+）
python3 --version

# 如果版本低于 3.9，需要先安装/升级 Python
# CentOS/RHEL: sudo yum install python39
# Ubuntu/Debian: sudo apt install python3.9

# 2. 检查 pip
python3 -m pip --version

# 3. 检查 pandoc（Word/PDF 转换需要）
pandoc --version

# 如果没有 pandoc：
# CentOS/RHEL: sudo yum install pandoc
# Ubuntu/Debian: sudo apt install pandoc

# 4. 检查现有 MySQL 容器
podman ps | grep mysql

# 记录以下信息：
# - 容器名称（如：mysql-container）
# - 监听端口（通常是 3306）

# 5. 检查现有 Nginx 容器
podman ps | grep nginx

# 记录：
# - 容器名称（如：nginx-container）
```

### 2.3 创建部署目录

```bash
# 在服务器上执行

# 创建项目目录
mkdir -p /home/studio

# 创建数据目录（用于存放用户上传的文件、日志等）
mkdir -p /home/studio/data/static/common_tools/html
mkdir -p /home/studio/data/static/works/html
mkdir -p /home/studio/data/logs

# 确认目录创建成功
ls -la /home/studio/
```

### 2.4 准备 MySQL 数据库

```bash
# 在服务器上执行

# 连接到 MySQL 容器（需要知道 root 密码）
podman exec -it <mysql-container-name> mysql -u root -p

# 在 MySQL 中执行：
CREATE DATABASE studio CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 确认数据库创建成功
SHOW DATABASES;

# 退出 MySQL
EXIT;
```

**重要信息记录**：
- MySQL 容器名称: `________________`
- MySQL root 密码: `________________`
- MySQL 端口: `3306`（通常）

---

## 第三部分：后端部署

### 3.1 上传后端代码到服务器

**在本地执行**：

```bash
# 回到项目根目录
cd /Users/zhangcolin/workspace/ai-teacher-platform

# 上传后端代码
scp -r -P <端口> backend/ <用户名>@<服务器IP>:/home/studio/

# 上传配置文件
scp -r -P <端口> configs/ <用户名>@<服务器IP>:/home/studio/

# 上传脚本
scp -r -P <端口> scripts/ <用户名>@<服务器IP>:/home/studio/

# 上传环境变量模板
scp -P <端口> .env.example <用户名>@<服务器IP>:/home/studio/
```

### 3.2 在服务器上创建 Python 虚拟环境

**在服务器上执行**：

```bash
# 进入后端目录
cd /home/studio/backend

# 创建虚拟环境（名为 venv）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 你会看到命令行前面多了 (venv) 标识

# 升级 pip（重要！）
pip install --upgrade pip

# 安装项目依赖（这一步会花费几分钟）
pip install -r requirements.txt

# 等待安装完成...
# 应该看到类似：Successfully installed fastapi-xxx sqlalchemy-xxx ...

# 测试安装是否成功
python -c "import fastapi; print('FastAPI 安装成功')"
python -c "import sqlalchemy; print('SQLAlchemy 安装成功')"
```

**如果安装失败**：
- 检查 Python 版本是否 >= 3.9
- 检查是否有系统依赖缺失（如 `gcc`、`mysql-devel`）
- CentOS/RHEL: `sudo yum install gcc python3-devel mysql-devel`
- Ubuntu/Debian: `sudo apt install gcc python3-dev libmysqlclient-dev`

### 3.3 配置环境变量

```bash
# 在服务器上执行
cd /home/studio

# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
# 或使用 nano: nano .env
```

**填入以下配置**：

```bash
# ============================================
# 数据库配置
# ============================================

# 方式1: 使用容器名称（推荐，如果在同一 Podman 网络）
DATABASE_URL=mysql+pymysql://root:<MySQL密码>@<MySQL容器名>:3306/studio?charset=utf8mb4

# 方式2: 使用 localhost（如果 MySQL 端口映射到主机）
DATABASE_URL=mysql+pymysql://root:<MySQL密码>@localhost:3306/studio?charset=utf8mb4

# 示例（替换 <> 中的内容）：
# DATABASE_URL=mysql+pymysql://root:your_password@mysql-container:3306/studio?charset=utf8mb4

# ============================================
# JWT 密钥（必须修改为随机值）
# ============================================
JWT_SECRET_KEY=<生成的随机密钥>

# ============================================
# AI 服务配置
# ============================================
CURRENT_PROVIDER=kimi
KIMI_API_KEY=sk-your-actual-kimi-api-key
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=moonshot-v1-8k

# DeepSeek（可选）
DEEPSEEK_API_KEY=sk-your-actual-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

AI_REQUEST_TIMEOUT=120

# ============================================
# 静态文件目录
# ============================================
STATIC_DIR=/home/studio/data/static
```

**生成 JWT 密钥**：

```bash
# 在服务器上执行
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 复制输出的密钥，填入 .env 文件的 JWT_SECRET_KEY
```

**保存文件**：
- vim: 按 `Esc`，输入 `:wq`，按 `Enter`
- nano: 按 `Ctrl+O` 保存，`Ctrl+X` 退出

### 3.4 初始化数据库

```bash
# 在服务器上执行
cd /home/studio/backend

# 激活虚拟环境（如果还没激活）
source venv/bin/activate

# 运行数据库迁移（创建表结构）
alembic upgrade head

# 应该看到类似输出：
# INFO  [alembic.runtime.migration] Running upgrade -> xxx, create_users_table
# INFO  [alembic.runtime.migration] Running upgrade xxx -> yyy, create_sessions_table
# ...

# 创建初始管理员用户
python scripts/create_initial_user.py

# 应该看到：
# 管理员用户创建成功
# 用户名: admin
# 密码: HcyAdmin@2026
```

**如果数据库迁移失败**：
- 检查 `.env` 中的 `DATABASE_URL` 是否正确
- 测试数据库连接：
```bash
python -c "
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv('/home/studio/.env')
try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    conn = engine.connect()
    print('✅ 数据库连接成功')
    conn.close()
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
"
```

### 3.5 测试后端服务

```bash
# 在服务器上执行
cd /home/studio/backend

# 激活虚拟环境
source venv/bin/activate

# 手动启动后端（测试用）
uvicorn src.main:app --host 127.0.0.1 --port 8000

# 应该看到：
# INFO:     Started server process [xxxxx]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://127.0.0.1:8000

# 保持这个终端运行，打开另一个终端测试
```

**在另一个终端测试**：

```bash
# 连接到服务器（新终端）
ssh -p <端口> <用户名>@<服务器IP>

# 测试 API
curl http://localhost:8000/api/v1/navigation

# 应该返回 JSON 数据（导航菜单）

# 测试登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"account": "admin", "password": "HcyAdmin@2026"}'

# 应该返回包含 token 的 JSON

# 如果测试成功，回到第一个终端，按 Ctrl+C 停止服务
```

---

## 第四部分：前端部署

### 4.1 上传前端打包文件

**在本地执行**：

```bash
# 回到项目根目录
cd /Users/zhangcolin/workspace/ai-teacher-platform

# 上传前端打包文件到服务器
scp -r -P <端口> frontend/dist/ <用户名>@<服务器IP>:/home/studio/frontend-dist/

# 等待上传完成...
```

### 4.2 验证前端文件

**在服务器上执行**：

```bash
# 检查前端文件
ls -la /home/studio/frontend-dist/

# 应该看到：
# index.html           # 入口文件
# assets/              # 静态资源目录
#   - index-xxx.js     # 主 JS 文件
#   - index-xxx.css    # 主 CSS 文件
#   - ...

# 检查文件权限（应该可读）
chmod -R 755 /home/studio/frontend-dist/
```

---

## 第五部分：Nginx 配置

### 5.1 重要提醒

⚠️ **服务器上已有其他服务在运行！**

- Nginx 配置位置: `/home/data/nginx/conf.d/`
- **务必先备份现有配置**
- **只添加新配置，不修改现有配置**

### 5.2 备份现有配置

```bash
# 在服务器上执行

# 备份现有配置（带时间戳）
cp /home/data/nginx/conf.d/default.conf \
   /home/data/nginx/conf.d/default.conf.backup.$(date +%Y%m%d_%H%M%S)

# 确认备份成功
ls -la /home/data/nginx/conf.d/ | grep backup
```

### 5.3 添加项目配置

**方式1: 创建独立配置文件（推荐）**

```bash
# 创建新配置文件
vim /home/data/nginx/conf.d/studio.conf
```

**方式2: 在现有文件末尾添加**

```bash
# 编辑现有配置
vim /home/data/nginx/conf.d/default.conf

# 滚动到文件末尾，添加新配置
```

**配置内容**：

```nginx
# ============================================
# AI 教育平台 - studio.aieducenter.com
# ============================================
server {
    listen 80;
    server_name studio.aieducenter.com;

    # 前端静态文件
    location / {
        root /home/studio/frontend-dist;
        index index.html;
        try_files $uri $uri/ /index.html;  # SPA 路由支持
    }

    # 后端 API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 流式输出支持（AI 对话需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
        
        # 超时设置（AI 请求可能较长）
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # 静态文件（用户上传的 HTML 工具、作品）
    location /static {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # 日志
    access_log /var/log/nginx/studio_access.log;
    error_log /var/log/nginx/studio_error.log;
}
```

**保存文件**：
- vim: 按 `Esc`，输入 `:wq`，按 `Enter`
- nano: 按 `Ctrl+O` 保存，`Ctrl+X` 退出

### 5.4 测试并重载 Nginx

```bash
# 在服务器上执行

# 测试 Nginx 配置
podman exec <nginx-container-name> nginx -t

# 应该看到：
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# 测试通过后，重载 Nginx
podman exec <nginx-container-name> nginx -s reload

# 或重启 Nginx 容器
# podman restart <nginx-container-name>
```

**如果测试失败**：
- 检查语法错误（如缺少分号、括号不匹配）
- 检查是否有重复的 `server_name`
- 检查文件路径是否正确

---

## 第六部分：服务管理

### 6.1 创建 systemd 服务（推荐）

**为什么使用 systemd？**
- ✅ 系统级管理，开机自启
- ✅ 自动重启（如果进程崩溃）
- ✅ 日志管理（journalctl）
- ✅ 标准化服务管理

**创建服务文件**：

```bash
# 在服务器上执行
sudo vim /etc/systemd/system/studio-backend.service
```

**服务配置内容**：

```ini
[Unit]
Description=AI Teacher Platform Backend Service
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/studio/backend
Environment="PATH=/home/studio/backend/venv/bin"
EnvironmentFile=/home/studio/.env
ExecStart=/home/studio/backend/venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

# 日志
StandardOutput=append:/home/studio/data/logs/backend.log
StandardError=append:/home/studio/data/logs/backend-error.log

[Install]
WantedBy=multi-user.target
```

**保存并启用服务**：

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start studio-backend

# 检查服务状态
sudo systemctl status studio-backend

# 应该看到：
# ● studio-backend.service - AI Teacher Platform Backend Service
#    Loaded: loaded (/etc/systemd/system/studio-backend.service; disabled)
#    Active: active (running) since ...
#    Main PID: xxxxx

# 设置开机自启
sudo systemctl enable studio-backend

# 测试服务是否正常
curl http://localhost:8000/api/v1/navigation
```

### 6.2 常用服务管理命令

```bash
# 启动服务
sudo systemctl start studio-backend

# 停止服务
sudo systemctl stop studio-backend

# 重启服务
sudo systemctl restart studio-backend

# 查看服务状态
sudo systemctl status studio-backend

# 查看服务日志
sudo journalctl -u studio-backend -f

# 或查看日志文件
tail -f /home/studio/data/logs/backend.log
tail -f /home/studio/data/logs/backend-error.log
```

---

## 第七部分：验证部署

### 7.1 检查服务状态

```bash
# 在服务器上执行

# 1. 检查后端服务
sudo systemctl status studio-backend

# 2. 测试后端 API
curl http://localhost:8000/api/v1/navigation

# 3. 测试前端（本地）
curl http://localhost | head -20

# 应该看到 HTML 内容

# 4. 检查 Nginx 容器
podman ps | grep nginx

# 5. 检查 MySQL 容器
podman ps | grep mysql
```

### 7.2 浏览器访问

1. **配置域名解析**（如果还没配置）：
   - 在 DNS 中添加 A 记录：`studio.aieducenter.com` → 服务器 IP

2. **访问网站**：
   - 打开浏览器：`http://studio.aieducenter.com`

3. **登录测试**：
   - 用户名：`admin`
   - 密码：`HcyAdmin@2026`

4. **功能测试**：
   - ✅ 导航菜单显示正常
   - ✅ AI 对话功能正常
   - ✅ 工具创建功能正常
   - ✅ 作品管理功能正常

### 7.3 检查数据持久化

```bash
# 检查数据目录
ls -la /home/studio/data/

# 应该看到：
# static/  # 用户上传的文件
# logs/    # 日志文件

# 检查日志文件
tail -20 /home/studio/data/logs/backend.log
```

---

## 第八部分：代码更新

### 8.1 后端更新

**在本地**：

```bash
# 1. 拉取最新代码
cd /Users/zhangcolin/workspace/ai-teacher-platform
git pull

# 2. 上传后端代码到服务器
scp -r -P <端口> backend/ <用户名>@<服务器IP>:/home/studio/

# 3. 上传配置文件（如果有更新）
scp -r -P <端口> configs/ <用户名>@<服务器IP>:/home/studio/
```

**在服务器上**：

```bash
# 1. 连接到服务器
ssh -p <端口> <用户名>@<服务器IP>

# 2. 进入后端目录
cd /home/studio/backend

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 更新依赖（如果 requirements.txt 有变化）
pip install -r requirements.txt

# 5. 运行数据库迁移（如果有新的迁移）
alembic upgrade head

# 6. 重启服务
sudo systemctl restart studio-backend

# 7. 检查服务状态
sudo systemctl status studio-backend

# 8. 查看日志（确认启动正常）
tail -f /home/studio/data/logs/backend.log
```

### 8.2 前端更新

**在本地**：

```bash
# 1. 拉取最新代码
cd /Users/zhangcolin/workspace/ai-teacher-platform
git pull

# 2. 重新构建前端
cd frontend
pnpm install  # 如果有新依赖
pnpm run build

# 3. 上传到服务器（会覆盖旧文件）
scp -r -P <端口> dist/ <用户名>@<服务器IP>:/home/studio/frontend-dist/
```

**在服务器上**：

```bash
# 无需重启 Nginx，直接访问即可看到更新
# 如果浏览器有缓存，按 Ctrl+F5 强制刷新
```

### 8.3 使用部署脚本（可选）

我们提供了简化的部署脚本，可以自动完成上传和重启。

**在本地使用脚本**：

```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform
./scripts/deploy.sh
```

脚本会自动：
1. 构建前端
2. 上传前后端代码到服务器
3. 重启后端服务

---

## 第九部分：常见问题

### 9.1 后端服务无法启动

**症状**: `systemctl status studio-backend` 显示 `failed` 或 `inactive`

**排查步骤**：

```bash
# 查看服务日志
sudo journalctl -u studio-backend -n 50

# 或查看日志文件
tail -50 /home/studio/data/logs/backend-error.log

# 常见原因：
# 1. 数据库连接失败 - 检查 .env 中的 DATABASE_URL
# 2. 端口被占用 - 检查 8000 端口: netstat -tulpn | grep 8000
# 3. 虚拟环境问题 - 检查虚拟环境路径
# 4. 依赖缺失 - 重新安装: pip install -r requirements.txt
```

### 9.2 数据库连接失败

**症状**: 日志显示 `Can't connect to MySQL server`

**排查步骤**：

```bash
# 1. 检查 MySQL 容器是否运行
podman ps | grep mysql

# 2. 测试数据库连接
cd /home/studio/backend
source venv/bin/activate

python -c "
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv('/home/studio/.env')
try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    conn = engine.connect()
    print('✅ 数据库连接成功')
    conn.close()
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
"

# 3. 检查 .env 配置
cat /home/studio/.env | grep DATABASE_URL

# 常见问题：
# - 容器名称错误
# - 密码错误
# - 数据库不存在（需要先创建）
# - 网络不通（ping 测试）
```

### 9.3 前端无法访问

**症状**: 浏览器访问 `studio.aieducenter.com` 显示 404 或无法访问

**排查步骤**：

```bash
# 1. 检查前端文件是否存在
ls -la /home/studio/frontend-dist/

# 2. 测试 Nginx 是否正常
podman ps | grep nginx

# 3. 检查 Nginx 配置
cat /home/data/nginx/conf.d/studio.conf

# 4. 测试本地访问
curl http://localhost | head -20

# 5. 检查 Nginx 日志
podman exec <nginx-container-name> tail -50 /var/log/nginx/studio_error.log

# 常见问题：
# - 前端文件路径错误
# - Nginx 配置错误
# - 域名解析问题
```

### 9.4 API 请求 502 错误

**症状**: 前端能访问，但 API 请求返回 502

**排查步骤**：

```bash
# 1. 检查后端服务是否运行
sudo systemctl status studio-backend

# 2. 测试后端 API
curl http://localhost:8000/api/v1/navigation

# 3. 检查 Nginx 配置中的代理设置
cat /home/data/nginx/conf.d/studio.conf | grep -A 10 "location /api"

# 4. 查看 Nginx 日志
podman exec <nginx-container-name> tail -50 /var/log/nginx/studio_error.log

# 常见问题：
# - 后端服务未启动
# - 端口配置错误（应该是 127.0.0.1:8000）
# - 超时设置过短
```

### 9.5 查看所有日志

```bash
# 后端服务日志（systemd）
sudo journalctl -u studio-backend -f

# 后端应用日志
tail -f /home/studio/data/logs/backend.log
tail -f /home/studio/data/logs/backend-error.log

# Nginx 日志
podman exec <nginx-container-name> tail -f /var/log/nginx/studio_access.log
podman exec <nginx-container-name> tail -f /var/log/nginx/studio_error.log
```

---

## 附录

### A. 常用命令速查

```bash
# 后端服务管理
sudo systemctl start studio-backend      # 启动
sudo systemctl stop studio-backend       # 停止
sudo systemctl restart studio-backend    # 重启
sudo systemctl status studio-backend     # 状态

# 查看日志
sudo journalctl -u studio-backend -f     # 实时日志
tail -f /home/studio/data/logs/backend.log

# 测试服务
curl http://localhost:8000/api/v1/navigation

# Nginx 操作
podman ps | grep nginx                   # 查看容器
podman exec <nginx-name> nginx -t        # 测试配置
podman exec <nginx-name> nginx -s reload # 重载配置

# 进入虚拟环境
cd /home/studio/backend
source venv/bin/activate
```

### B. 目录说明

| 目录 | 说明 | 持久化 |
|:---|:---|:---|
| `/home/studio/backend/` | 后端代码 | ❌ 更新会覆盖 |
| `/home/studio/frontend-dist/` | 前端打包文件 | ❌ 更新会覆盖 |
| `/home/studio/configs/` | 配置文件 | ❌ 更新会覆盖 |
| `/home/studio/data/static/` | 用户上传文件 | ✅ **持久化** |
| `/home/studio/data/logs/` | 日志文件 | ✅ **持久化** |
| `/home/studio/.env` | 环境变量 | ✅ **持久化** |

### C. 默认管理员账号

- **用户名**: `admin`
- **密码**: `HcyAdmin@2026`
- **邮箱**: `admin@aieducenter.com`
- **角色**: 管理员

### D. 环境变量说明

| 变量 | 说明 | 必填 | 示例 |
|:---|:---|:---|:---|
| `DATABASE_URL` | 数据库连接 | ✅ | `mysql+pymysql://root:pass@mysql:3306/studio?charset=utf8mb4` |
| `JWT_SECRET_KEY` | JWT 密钥 | ✅ | 使用 `secrets.token_urlsafe(32)` 生成 |
| `CURRENT_PROVIDER` | AI 服务商 | ✅ | `kimi` 或 `deepseek` |
| `KIMI_API_KEY` | Kimi API 密钥 | ✅ | `sk-xxx...` |
| `KIMI_BASE_URL` | Kimi API 地址 | ✅ | `https://api.moonshot.cn/v1` |
| `KIMI_MODEL` | Kimi 模型 | ✅ | `moonshot-v1-8k` |
| `STATIC_DIR` | 静态文件目录 | ✅ | `/home/studio/data/static` |

### E. 端口说明

| 端口 | 服务 | 监听地址 | 说明 |
|:---|:---|:---|:---|
| 80 | Nginx | 0.0.0.0:80 | 对外访问 |
| 8000 | 后端 API | 127.0.0.1:8000 | 仅本地，通过 Nginx 代理 |
| 3306 | MySQL | - | Podman 容器内部 |

---

**文档版本**: v5.0  
**最后更新**: 2026-01-11  
**适用场景**: 传统部署方式（Python 虚拟环境 + Nginx）
