# 快速开始 - 5 分钟部署指南

> 适用于已有 Python 和 Nginx 环境的服务器

## 前置条件

- ✅ 服务器上已安装 Python 3.9+
- ✅ 服务器上已运行 MySQL（Podman 容器或其他）
- ✅ 服务器上已运行 Nginx（Podman 容器或其他）
- ✅ 本地已安装 Node.js 18+ 和 pnpm

## 一、本地准备（3 分钟）

```bash
# 1. 进入项目目录
cd /Users/zhangcolin/workspace/ai-teacher-platform

# 2. 构建前端
cd frontend
pnpm install
pnpm run build
cd ..

# 3. 配置部署脚本（首次需要）
export SERVER_HOST=your-server-ip
export SERVER_USER=root
export SERVER_PORT=22
```

## 二、首次部署（5-10 分钟）

### 1. 上传文件到服务器

```bash
# 在本地执行
scp -r backend/ configs/ scripts/ .env.example root@server:/home/studio/
scp -r frontend/dist/ root@server:/home/studio/frontend-dist/
```

### 2. 在服务器上配置

```bash
# SSH 到服务器
ssh root@server

# 创建数据目录
mkdir -p /home/studio/data/static/common_tools/html
mkdir -p /home/studio/data/static/works/html
mkdir -p /home/studio/data/logs

# 创建 Python 虚拟环境
cd /home/studio/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 配置环境变量
cd /home/studio
cp .env.example .env
vim .env  # 填入实际配置（数据库、JWT 密钥、API 密钥等）

# 初始化数据库
cd /home/studio/backend
source venv/bin/activate
alembic upgrade head
python scripts/create_initial_user.py

# 创建 systemd 服务
sudo cp /home/studio/docs/deployment/studio-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable studio-backend
sudo systemctl start studio-backend

# 检查服务状态
sudo systemctl status studio-backend
```

### 3. 配置 Nginx

```bash
# 在服务器上执行

# 备份现有配置
cp /home/data/nginx/conf.d/default.conf \
   /home/data/nginx/conf.d/default.conf.backup

# 创建新配置（参考 docs/deployment/nginx-config-reference.md）
vim /home/data/nginx/conf.d/studio.conf
# 粘贴配置内容，保存

# 测试并重载 Nginx
podman exec nginx-container nginx -t
podman exec nginx-container nginx -s reload
```

### 4. 验证部署

```bash
# 在服务器上测试
curl http://localhost:8000/api/v1/navigation
curl http://localhost | head -20

# 浏览器访问
# http://studio.aieducenter.com
# 用户名: admin
# 密码: HcyAdmin@2026
```

## 三、后续更新（1 分钟）

### 方式1: 使用自动化脚本（推荐）

```bash
# 在本地执行
cd /Users/zhangcolin/workspace/ai-teacher-platform

# 配置服务器信息（首次）
export SERVER_HOST=your-server-ip
export SERVER_USER=root
export SERVER_PORT=22

# 运行部署脚本
./scripts/deploy.sh

# 选择部署模式：
# 1) 仅前端 - 适合前端代码更新
# 2) 仅后端 - 适合后端代码更新
# 3) 完整部署 - 前后端都更新
```

### 方式2: 手动更新

**前端更新**:
```bash
# 本地构建
cd frontend && pnpm run build

# 上传
scp -r dist/ root@server:/home/studio/frontend-dist/

# 无需重启，刷新浏览器即可
```

**后端更新**:
```bash
# 上传代码
scp -r backend/ root@server:/home/studio/

# SSH 到服务器
ssh root@server
cd /home/studio/backend
source venv/bin/activate
pip install -r requirements.txt  # 如果有新依赖
alembic upgrade head  # 如果有数据库变更
sudo systemctl restart studio-backend
```

## 常用命令

```bash
# 后端服务管理
sudo systemctl start studio-backend      # 启动
sudo systemctl stop studio-backend       # 停止
sudo systemctl restart studio-backend    # 重启
sudo systemctl status studio-backend     # 状态

# 查看日志
sudo journalctl -u studio-backend -f    # 实时日志
tail -f /home/studio/data/logs/backend.log

# 测试
curl http://localhost:8000/api/v1/navigation  # 测试 API
curl http://localhost  # 测试前端
```

## 故障排查

### 后端服务无法启动

```bash
# 查看日志
sudo journalctl -u studio-backend -n 50
tail -50 /home/studio/data/logs/backend-error.log

# 测试数据库连接
cd /home/studio/backend
source venv/bin/activate
python -c "
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv('/home/studio/.env')
engine = create_engine(os.getenv('DATABASE_URL'))
conn = engine.connect()
print('数据库连接成功')
"
```

### 前端无法访问

```bash
# 检查文件是否存在
ls -la /home/studio/frontend-dist/

# 检查 Nginx 配置
cat /home/data/nginx/conf.d/studio.conf

# 查看 Nginx 日志
podman exec nginx-container tail -50 /var/log/nginx/studio_error.log
```

## 详细文档

- 完整部署文档: [DEPLOYMENT.md](./DEPLOYMENT.md)
- Nginx 配置参考: [nginx-config-reference.md](./nginx-config-reference.md)
- Systemd 服务模板: [studio-backend.service](./studio-backend.service)

---

**文档版本**: v1.0  
**最后更新**: 2026-01-11

