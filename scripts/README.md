# 部署脚本使用说明

本目录包含AI智能备课平台的部署脚本，用于打包和部署项目到生产服务器。

## 脚本说明

### build.sh - 构建打包脚本

自动构建前后端项目并打包到 `dist/` 目录。

**功能：**
- 清理旧的构建文件
- 构建前端（Vue3 + Vite）
- 打包后端（Python + FastAPI）
- 复制配置文件和必要文件
- 应用生产环境配置

**使用方法：**
```bash
./scripts/build.sh
```

**输出目录结构：**
```
dist/
├── frontend/          # 前端构建产物
├── backend/           # 后端源代码和配置
└── configs/           # YAML配置文件
```

### deploy.sh - 服务器部署脚本

自动将打包好的文件上传到生产服务器。

**使用前配置：**
1. 编辑 `scripts/deploy.sh`
2. 修改服务器配置变量：
   ```bash
   # 服务器连接配置
   SERVER_HOST="your-server-ip"              # 服务器IP
   SERVER_USER="root"                        # 登录用户
   SERVER_PASS="your-password"               # 登录密码

   # 服务器目录配置（可根据实际情况调整）
   SERVER_BASE_DIR="/home/ai-teacher-platform"     # 基础目录
   SERVER_FRONTEND_DIR="$SERVER_BASE_DIR/frontend" # 前端目录
   SERVER_BACKEND_DIR="$SERVER_BASE_DIR/backend"   # 后端目录
   SERVER_CONFIGS_DIR="$SERVER_BASE_DIR/configs"   # 配置目录
   # SERVER_UPLOADS_DIR 会自动设置为 $SERVER_BACKEND_DIR/uploads
   ```

3. **配置生产环境（重要！）**
   - 配置文件位置：`backend/.env.production`
   - 使用真实的数据库密码、API密钥等（不要使用占位符）
   - ✅ backend/ 下的 `.env`、`.env.production`、`.env.test` 都已加入 Git 版本控制
   - 首次配置建议：
     ```bash
     # 复制示例模板
     cp backend/.env.example backend/.env.production
     # 然后编辑，填入真实的生产环境配置
     vim backend/.env.production
     ```

**使用方法：**
```bash
./scripts/deploy.sh
```

**功能：**
- 自动执行 build.sh 构建项目
- 创建服务器目录
- 上传前端文件
- 上传后端文件
- 上传配置文件
- 自动修复前端文件权限（`chmod -R 755`）
- 自动重启后端服务（`systemctl restart studio-backend`）
- 显示后端服务状态

## 部署流程

1. **本地测试**
   ```bash
   # 确保代码能正常运行
   cd backend && python3 -m src.main
   cd frontend && npm run dev
   ```

2. **构建项目**
   ```bash
   ./scripts/build.sh
   ```

3. **配置生产环境**
   - 配置文件位置：`backend/.env.production`
   - 填入真实的数据库密码、API密钥等（非占位符）
   - 💡 配置说明：
     - `backend/.env.production` - 生产环境配置（Git管理）
     - `backend/.env.test` - 测试环境配置（Git管理）
     - `backend/.env` - 本地开发配置（Git管理）
     - 部署时会自动复制到 `dist/backend/.env`

4. **配置服务器信息**
   - 编辑 `scripts/deploy.sh`
   - 填写服务器IP、用户名、密码

5. **部署到服务器**
   ```bash
   ./scripts/deploy.sh
   ```

## 依赖要求

**本地环境：**
- Node.js 18+
- Python 3.10+
- rsync（用于文件同步）

**服务器环境：**
- Python 3.10+
- MySQL 8.0+
- sshpass（用于自动登录）

**安装sshpass：**
```bash
# macOS
brew install sshpass

# Ubuntu/Debian
sudo apt-get install sshpass

# CentOS/RHEL
sudo yum install sshpass
```

## 注意事项

1. **配置管理（重要）**
   - ✅ **配置文件位置**：`backend/.env.production`
     - 所有环境配置文件（`.env`、`.env.production`、`.env.test`）都使用 Git 版本控制
     - 每次运行 `build.sh` 时自动复制 `backend/.env.production` 到 `dist/backend/.env`
     - 部署时直接上传到服务器
     - 有配置变更时，直接修改 `backend/.env.production`，然后重新部署
   - ⚠️ **不要做**：
     - 不要在服务器上手动修改 `.env`（下次部署会被覆盖）
     - 不要将包含占位符的模板文件部署到生产环境

2. **安全性**
   - 生产环境的API密钥和密码要妥善保管
   - 建议使用SSH密钥而非密码登录
   - 定期更新数据库密码和API密钥

2. **数据库**
   - 首次部署前需要在服务器创建数据库
   - 运行数据库迁移：`alembic upgrade head`

3. **Nginx配置**
   - 前端静态文件建议使用Nginx托管
   - 后端API需要配置反向代理

4. **systemd 服务配置**
   - 部署脚本使用 `systemctl restart studio-backend` 重启服务
   - 需要确保服务器已配置 systemd 服务文件
   - 服务文件位置：`/etc/systemd/system/studio-backend.service`
   - 示例服务文件内容：
     ```ini
     [Unit]
     Description=AI Teacher Platform Backend
     After=network.target mysql.service

     [Service]
     Type=simple
     User=root
     WorkingDirectory=/home/studio/backend
     Environment="PATH=/usr/local/bin:/usr/bin:/bin"
     ExecStart=/usr/bin/python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000
     Restart=always
     RestartSec=10

     [Install]
     WantedBy=multi-user.target
     ```

5. **日志查看**
   - 使用 systemd journal 查看后端日志：`journalctl -u studio-backend -f`
   - 或查看应用日志：`tail -f /home/studio/backend/server.log`

## 常见问题

**Q: 构建失败怎么办？**
A: 检查本地依赖是否安装完整，确保 `npm run build` 和后端测试能通过。

**Q: 上传失败怎么办？**
A: 检查服务器连接、密码是否正确，确保服务器已安装sshpass。

**Q: 部署后无法访问？**
A: 检查服务器防火墙、后端服务是否启动、Nginx配置是否正确。

**Q: 如何回滚？**
A: 保留上一版本的dist备份，或使用Git回退后重新部署。

**Q: 如何更新生产环境配置？**
A:
1. 编辑 `backend/.env.production`（修改数据库密码、API密钥等）
2. 提交到 Git（可选，如果需要团队共享）
3. 重新运行 `./scripts/deploy.sh`
4. 配置会自动更新到服务器（无需手动修改服务器文件）

**Q: 环境配置文件有哪些？**
A:
- `backend/.env` - 本地开发环境配置
- `backend/.env.test` - 测试环境配置
- `backend/.env.production` - 生产环境配置（部署时使用）
- `backend/.env.example` - 配置模板和说明
- 所有文件都使用 Git 版本控制
