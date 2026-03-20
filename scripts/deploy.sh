#!/bin/bash
# AI智能备课平台 - 服务器部署脚本

set -e

# 服务器配置 - 请根据实际情况修改
SERVER_HOST="39.97.6.179"
SERVER_USER="root"
SERVER_PASS="Hcy20251007"

# 服务器目录配置
SERVER_BASE_DIR="/home/studio"              # 服务器基础目录
SERVER_FRONTEND_DIR="$SERVER_BASE_DIR/frontend-dist"   # 前端文件目录
SERVER_BACKEND_DIR="$SERVER_BASE_DIR/backend"     # 后端代码目录
SERVER_CONFIGS_DIR="$SERVER_BASE_DIR/configs"     # 配置文件目录
SERVER_UPLOADS_DIR="$SERVER_BACKEND_DIR/uploads"  # 上传文件目录

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"
FRONTEND_DIST="$DIST_DIR/frontend"
BACKEND_DIST="$DIST_DIR/backend"

echo "📤 开始部署文件到 $SERVER_HOST..."
echo "目标目录: $SERVER_BASE_DIR"
echo "  前端: $SERVER_FRONTEND_DIR"
echo "  后端: $SERVER_BACKEND_DIR"
echo "  配置: $SERVER_CONFIGS_DIR"

# 检查是否已配置服务器信息
if [ "$SERVER_HOST" = "your-server-ip" ]; then
    echo "❌ 错误: 请先配置服务器信息"
    echo "请编辑 scripts/deploy.sh 文件，修改以下变量："
    echo "  - SERVER_HOST: 服务器IP地址"
    echo "  - SERVER_USER: 服务器用户名"
    echo "  - SERVER_PASS: 服务器密码"
    echo "  - SERVER_BASE_DIR: 服务器基础目录"
    echo "  - SERVER_FRONTEND_DIR: 前端文件目录"
    echo "  - SERVER_BACKEND_DIR: 后端代码目录"
    echo "  - SERVER_CONFIGS_DIR: 配置文件目录"
    exit 1
fi

# 1. 先执行构建
echo ""
echo "📦 构建项目..."
"$SCRIPT_DIR/build.sh"

# 2. 创建服务器目录
echo ""
echo "📁 创建服务器目录..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST" "mkdir -p $SERVER_FRONTEND_DIR $SERVER_BACKEND_DIR $SERVER_UPLOADS_DIR $SERVER_CONFIGS_DIR"

# 3. 上传前端文件
echo ""
echo "📤 上传前端文件..."
sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no -r "$FRONTEND_DIST"/* "$SERVER_USER@$SERVER_HOST:$SERVER_FRONTEND_DIR/"

# 4. 上传后端文件
echo ""
echo "📤 上传后端文件..."
sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no -r "$BACKEND_DIST" "$SERVER_USER@$SERVER_HOST:$SERVER_BACKEND_DIR/"

# 5. 上传配置文件
echo ""
echo "📤 上传配置文件..."
sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no -r "$DIST_DIR/configs"/* "$SERVER_USER@$SERVER_HOST:$SERVER_CONFIGS_DIR/"

# 6. 修复前端文件权限
echo ""
echo "🔧 修复前端文件权限..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST" "chmod -R 755 $SERVER_FRONTEND_DIR"

# 7. 重启后端服务
echo ""
echo "🔄 重启后端服务 (systemctl)..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST" "systemctl restart studio-backend"

# 8. 检查服务状态
echo ""
echo "📊 检查服务状态..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST" "systemctl status studio-backend --no-pager -l" | head -n 10

echo ""
echo "✅ 部署完成！"
echo ""
echo "已完成的操作："
echo "  ✓ 构建前后端项目"
echo "  ✓ 上传前端文件到 $SERVER_FRONTEND_DIR"
echo "  ✓ 上传后端文件到 $SERVER_BACKEND_DIR"
echo "  ✓ 上传配置文件到 $SERVER_CONFIGS_DIR"
echo "  ✓ 修复前端文件权限 (chmod -R 755)"
echo "  ✓ 重启后端服务 (systemctl restart studio-backend)"
echo ""
echo "访问地址："
echo "  前端: http://$SERVER_HOST (或配置的Nginx端口)"
echo "  后端: http://$SERVER_HOST:8000"
echo ""
echo "服务器目录："
echo "  前端: $SERVER_FRONTEND_DIR"
echo "  后端: $SERVER_BACKEND_DIR"
echo "  配置: $SERVER_CONFIGS_DIR"
echo ""
echo "查看后端日志："
echo "  ssh $SERVER_USER@$SERVER_HOST"
echo "  journalctl -u studio-backend -f"
echo ""
echo "查看后端服务状态："
echo "  systemctl status studio-backend"
