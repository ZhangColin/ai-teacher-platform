# -*- coding: utf-8 -*-
"""AI 教师平台后端主应用"""
import sys
import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

# 添加项目根目录到路径，以便访问配置目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入路由模块
from src.routers import (
    auth_router,
    users_router,
    tools_router,
    sessions_router,
    admin_tools_router,
    works_router,
    courses_router,
    common_router,
)

# 导入新的模块化路由（interfaces层）
from src.interfaces.routers.tools import list as tools_list_router
from src.interfaces.routers.tools import chat as tools_chat_router
from src.interfaces.routers.tools import conversations as tools_conversations_router

# 导入错误处理中间件
from src.interfaces.middleware.error_handler import error_handler

# 创建 FastAPI 应用
app = FastAPI(title="AI Teacher Platform Backend")

# ==================== 静态文件服务 ====================

# 挂载静态文件目录
# 优先使用环境变量指定的目录，否则使用默认目录
static_dir = Path(os.getenv("STATIC_DIR", str(project_root / "backend" / "static")))
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
else:
    logger.warning(f"静态文件目录不存在: {static_dir}")

# 确保static下的media目录存在（用于存储生成的音频、视频等）
media_dir = static_dir / "media"
media_dir.mkdir(parents=True, exist_ok=True)


# ==================== 中间件注册 ====================

# 注册统一错误处理中间件
app.middleware("http")(error_handler)


# ==================== 路由注册 ====================

# 新的工具路由（interfaces层）- 使用前缀
app.include_router(tools_list_router.router, prefix="/api/v1")
app.include_router(tools_chat_router.router, prefix="/api/v1")
app.include_router(tools_conversations_router.router, prefix="/api/v1")

# 认证相关路由
app.include_router(auth_router)

# 用户管理路由
app.include_router(users_router)

# AI 工具路由（旧路由）
# 已迁移到 interfaces 层的端点：
#   - GET /tools -> interfaces/routers/tools/list.py
#   - GET /toolsets/{toolset_id}/tools -> interfaces/routers/tools/list.py
#   - POST /tools/{tool_id}/chat -> interfaces/routers/tools/chat.py
#   - POST /tools/{tool_id}/chat/stream -> interfaces/routers/tools/chat.py
#   - GET /tools/{tool_id}/conversations -> interfaces/routers/tools/conversations.py
#   - DELETE /tools/{tool_id}/conversations/{conv_id} -> interfaces/routers/tools/conversations.py
# 未迁移的端点（仍需要旧 tools.py）：
#   - GET /common-tools - 通用工具列表（被前端 CommonToolsView 使用）
#   - POST /tools/{tool_id}/generate-media - 媒体生成
# TODO: 未来迁移剩余端点到新架构，然后完全删除 tools.py
app.include_router(tools_router)

# 会话管理路由
app.include_router(sessions_router)

# 管理员工具路由
app.include_router(admin_tools_router)

# 教案学案路由
app.include_router(works_router)

# 课程文档路由
app.include_router(courses_router)

# 通用功能路由
app.include_router(common_router)

# 设置任务存储引用（供 common_router 使用）
from src.routers.common import set_task_storage
from src.routers.tools import task_storage
set_task_storage(task_storage)


# ==================== 已废弃的 Agent API ====================
# 保留这些接口是为了向后兼容，实际功能已迁移到 Tool API

@app.get("/api/v1/agents")
async def get_agents():
    """获取所有已配置的 Agent 列表（已废弃，请使用 GET /api/v1/tools）"""
    from src.services.agent_service import AgentService
    from src.models import AgentListResponse, AgentListItem

    agent_service = AgentService(config_dir=str(project_root / "configs" / "agents"))
    agents = agent_service.load_all_agents()

    # 转换为 API 响应格式
    agent_items = [
        AgentListItem(
            agent_id=agent.agent_id,
            name=agent.name,
            description=agent.description,
            icon=None  # MVP阶段暂不支持icon
        )
        for agent in agents
    ]

    return AgentListResponse(agents=agent_items)


@app.post("/api/v1/agents/{agent_id}/sessions")
async def create_agent_session(agent_id: str):
    """为指定的 Agent 创建新会话（已废弃，请使用 POST /api/v1/tools/{tool_id}/chat）"""
    from src.services.agent_service import AgentService
    from src.services.ai_service import AIService
    from src.services.artifact_parser import ArtifactParser
    from src.models import SessionInitResponse
    import uuid

    agent_service = AgentService(config_dir=str(project_root / "configs" / "agents"))
    ai_service = AIService()
    artifact_parser = ArtifactParser()

    # 获取 Agent
    agent = agent_service.get_agent_by_id(agent_id)

    if not agent:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    # 生成欢迎消息
    welcome_message = await ai_service.generate_welcome_message(agent.system_prompt)

    # 解析欢迎消息中的成果物
    artifacts = artifact_parser.parse_from_markdown(welcome_message)

    # 注意：此 API 已废弃，不再创建真实会话
    # 返回一个临时 session_id（仅用于兼容旧代码）
    temp_session_id = str(uuid.uuid4())

    return SessionInitResponse(
        session_id=temp_session_id,
        welcome_message=welcome_message,
        ui_config=agent.ui_config,
        artifacts=artifacts
    )


# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "service": "ai-teacher-platform"}


# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    logger.info("AI Teacher Platform Backend 启动中...")
    logger.info(f"项目根目录: {project_root}")
    logger.info(f"静态文件目录: {static_dir}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作"""
    logger.info("AI Teacher Platform Backend 关闭中...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
