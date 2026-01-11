#!/bin/bash
# AI 教育平台 - 简化部署脚本
# 功能: 本地构建 + 上传到服务器 + 重启服务

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置（根据实际情况修改）
SERVER_USER="${SERVER_USER:-root}"
SERVER_HOST="${SERVER_HOST:-your-server-ip}"
SERVER_PORT="${SERVER_PORT:-22}"
DEPLOY_DIR="/home/studio"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AI 教育平台部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查是否在项目根目录
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}错误: 请在项目根目录执行此脚本${NC}"
    echo -e "${YELLOW}当前目录: $(pwd)${NC}"
    exit 1
fi

# 检查服务器配置
if [ "$SERVER_HOST" == "your-server-ip" ]; then
    echo -e "${RED}错误: 请先配置服务器信息${NC}"
    echo -e "${YELLOW}编辑脚本或设置环境变量:${NC}"
    echo -e "${BLUE}  export SERVER_HOST=your-server-ip${NC}"
    echo -e "${BLUE}  export SERVER_USER=root${NC}"
    echo -e "${BLUE}  export SERVER_PORT=22${NC}"
    exit 1
fi

echo -e "${GREEN}目标服务器: ${SERVER_USER}@${SERVER_HOST}:${SERVER_PORT}${NC}"
echo ""

# 询问部署模式
echo -e "${YELLOW}选择部署模式:${NC}"
echo -e "  1) 仅前端（推荐，适合前端更新）"
echo -e "  2) 仅后端（适合后端代码更新）"
echo -e "  3) 完整部署（前端 + 后端）"
echo -e "  4) 仅上传，不重启（调试用）"
echo ""
read -p "请选择 [1-4]: " choice

case $choice in
    1)
        DEPLOY_MODE="frontend"
        ;;
    2)
        DEPLOY_MODE="backend"
        ;;
    3)
        DEPLOY_MODE="full"
        ;;
    4)
        DEPLOY_MODE="upload-only"
        ;;
    *)
        echo -e "${RED}无效选择${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}部署模式: ${DEPLOY_MODE}${NC}"
echo ""

# ============================================
# 前端构建和上传
# ============================================
if [ "$DEPLOY_MODE" == "frontend" ] || [ "$DEPLOY_MODE" == "full" ] || [ "$DEPLOY_MODE" == "upload-only" ]; then
    echo -e "${GREEN}[1/3] 构建前端...${NC}"
    cd frontend
    
    # 检查 pnpm
    if ! command -v pnpm &> /dev/null; then
        echo -e "${RED}错误: pnpm 未安装${NC}"
        echo -e "${YELLOW}安装命令: npm install -g pnpm${NC}"
        exit 1
    fi
    
    # 安装依赖（如果需要）
    echo -e "${YELLOW}安装依赖...${NC}"
    pnpm install
    
    # 构建
    echo -e "${YELLOW}构建生产版本...${NC}"
    pnpm run build
    
    # 检查构建结果
    if [ ! -f "dist/index.html" ]; then
        echo -e "${RED}错误: 前端构建失败${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 前端构建完成${NC}"
    cd ..
    
    echo -e "${GREEN}[2/3] 上传前端文件...${NC}"
    # 删除服务器上的旧文件
    ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} "rm -rf ${DEPLOY_DIR}/frontend-dist/*"
    
    # 上传新文件
    scp -r -P ${SERVER_PORT} frontend/dist/* ${SERVER_USER}@${SERVER_HOST}:${DEPLOY_DIR}/frontend-dist/
    
    echo -e "${GREEN}✓ 前端上传完成${NC}"
    echo -e "${YELLOW}提示: 前端更新无需重启服务，可能需要清除浏览器缓存（Ctrl+F5）${NC}"
fi

# ============================================
# 后端上传和重启
# ============================================
if [ "$DEPLOY_MODE" == "backend" ] || [ "$DEPLOY_MODE" == "full" ] || [ "$DEPLOY_MODE" == "upload-only" ]; then
    echo -e "${GREEN}[2/3] 上传后端文件...${NC}"
    
    # 上传后端代码
    scp -r -P ${SERVER_PORT} backend/ ${SERVER_USER}@${SERVER_HOST}:${DEPLOY_DIR}/
    
    # 上传配置文件
    scp -r -P ${SERVER_PORT} configs/ ${SERVER_USER}@${SERVER_HOST}:${DEPLOY_DIR}/
    
    echo -e "${GREEN}✓ 后端上传完成${NC}"
    
    if [ "$DEPLOY_MODE" != "upload-only" ]; then
        echo -e "${GREEN}[3/3] 重启后端服务...${NC}"
        
        # 在服务器上执行
        ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} << 'EOF'
            cd /home/studio/backend
            source venv/bin/activate
            
            # 更新依赖（如果 requirements.txt 有变化）
            echo "检查依赖更新..."
            pip install -r requirements.txt
            
            # 运行数据库迁移（如果有新的迁移）
            echo "运行数据库迁移..."
            alembic upgrade head
            
            # 重启服务
            echo "重启后端服务..."
            sudo systemctl restart studio-backend
            
            # 等待服务启动
            sleep 3
            
            # 检查服务状态
            sudo systemctl status studio-backend --no-pager -l
EOF
        
        echo -e "${GREEN}✓ 后端服务重启完成${NC}"
    fi
fi

# ============================================
# 验证部署
# ============================================
if [ "$DEPLOY_MODE" != "upload-only" ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}验证部署${NC}"
    echo -e "${GREEN}========================================${NC}"
    
    # 测试后端 API
    if [ "$DEPLOY_MODE" == "backend" ] || [ "$DEPLOY_MODE" == "full" ]; then
        echo -e "${YELLOW}测试后端 API...${NC}"
        if ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} "curl -f http://localhost:8000/api/v1/navigation > /dev/null 2>&1"; then
            echo -e "${GREEN}✓ 后端 API 正常${NC}"
        else
            echo -e "${RED}✗ 后端 API 异常${NC}"
            echo -e "${YELLOW}查看日志: ssh 到服务器后执行${NC}"
            echo -e "${BLUE}  sudo journalctl -u studio-backend -n 50${NC}"
        fi
    fi
    
    # 测试前端
    if [ "$DEPLOY_MODE" == "frontend" ] || [ "$DEPLOY_MODE" == "full" ]; then
        echo -e "${YELLOW}测试前端...${NC}"
        if ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} "test -f ${DEPLOY_DIR}/frontend-dist/index.html"; then
            echo -e "${GREEN}✓ 前端文件存在${NC}"
        else
            echo -e "${RED}✗ 前端文件不存在${NC}"
        fi
    fi
fi

# 完成
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "访问地址: ${GREEN}http://studio.aieducenter.com${NC}"
echo ""
echo -e "常用命令（在服务器上执行）:"
echo -e "  - 查看后端状态: ${BLUE}sudo systemctl status studio-backend${NC}"
echo -e "  - 查看后端日志: ${BLUE}sudo journalctl -u studio-backend -f${NC}"
echo -e "  - 重启后端: ${BLUE}sudo systemctl restart studio-backend${NC}"
echo ""
