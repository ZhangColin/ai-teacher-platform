"""AI 教师平台后端主应用"""
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException

# 添加项目根目录到路径，以便访问配置目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.agent_service import AgentService
from src.services.session_service import SessionService
from src.services.ai_service import AIService
from src.services.artifact_parser import ArtifactParser
from src.models import (
    AgentListResponse, AgentListItem, SessionInitResponse,
    ChatRequest, ChatResponse, Message
)

app = FastAPI(title="AI Teacher Platform Backend")

# 初始化服务
agent_service = AgentService(config_dir=str(project_root / "configs" / "agents"))
session_service = SessionService()
ai_service = AIService()
artifact_parser = ArtifactParser()


@app.get("/api/v1/agents", response_model=AgentListResponse)
async def get_agents():
    """获取所有已配置的 Agent 列表"""
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


@app.post("/api/v1/agents/{agent_id}/sessions", response_model=SessionInitResponse)
async def create_session(agent_id: str):
    """为指定的 Agent 创建新会话"""
    # 获取 Agent
    agent = agent_service.get_agent_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    # 创建会话
    session_id = session_service.create_session(agent)
    
    # 生成欢迎消息
    welcome_message = await ai_service.generate_welcome_message(agent.system_prompt)
    
    # 解析欢迎消息中的成果物
    artifacts = artifact_parser.parse_from_markdown(welcome_message)
    
    return SessionInitResponse(
        session_id=session_id,
        welcome_message=welcome_message,
        ui_config=agent.ui_config,
        artifacts=artifacts
    )


@app.post("/api/v1/sessions/{session_id}/chat", response_model=ChatResponse)
async def chat(session_id: str, request: ChatRequest):
    """发送消息并获取 AI 回复（包含成果物）"""
    # 验证会话是否存在
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    
    # 获取 Agent 信息
    agent_id = session["agent_id"]
    agent = agent_service.get_agent_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    # 转换历史消息格式（从 Message 对象转换为字典）
    history_list = []
    if request.history:
        for msg in request.history:
            # 验证 role 的有效值
            if msg.role not in ["user", "assistant"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"无效的消息角色: {msg.role}，必须是 'user' 或 'assistant'"
                )
            history_list.append({
                "role": msg.role,
                "content": msg.content
            })
    
    # 调用 AI 服务进行对话
    reply = await ai_service.chat(
        system_prompt=agent.system_prompt,
        history=history_list,
        user_message=request.message
    )
    
    # 解析成果物
    artifacts = artifact_parser.parse_from_markdown(reply)
    
    return ChatResponse(
        reply=reply,
        artifacts=artifacts
    )

