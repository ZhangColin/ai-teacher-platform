"""AI 教师平台后端主应用"""
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# 添加项目根目录到路径，以便访问配置目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.agent_service import AgentService
from src.services.tool_service import ToolService
from src.services.session_service import SessionService
from src.services.ai_service import AIService
from src.services.artifact_parser import ArtifactParser
from src.services.user_service import UserService
from src.services.auth_service import AuthService
from src.models import (
    AgentListResponse, AgentListItem, SessionInitResponse,
    ChatRequest, ChatResponse, Message,
    LoginRequest, LoginResponse, UserInfo, UserInfoResponse,
    CreateUserRequest, CreateUserResponse, UserListResponse, UserListItem,
    ToolListResponse, ToolListItem, CategoryGroup
)

app = FastAPI(title="AI Teacher Platform Backend")

# 初始化服务
agent_service = AgentService(config_dir=str(project_root / "configs" / "agents"))
tool_service = ToolService(config_dir=str(project_root / "configs" / "tools"))
session_service = SessionService()
ai_service = AIService()
artifact_parser = ArtifactParser()
user_service = UserService()
auth_service = AuthService()

# HTTP Bearer Token 安全方案
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInfo:
    """
    获取当前登录用户（依赖注入函数）
    
    Args:
        credentials: HTTP Bearer Token凭证
        
    Returns:
        UserInfo: 当前用户信息
        
    Raises:
        HTTPException: Token无效、过期或用户不存在
    """
    token = credentials.credentials
    
    # 验证Token并获取用户ID
    user_id = auth_service.get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 根据用户ID查询用户
    user = user_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 返回用户信息（不包含密码）
    return UserInfo(
        user_id=user.user_id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar
    )


@app.get("/api/v1/agents", response_model=AgentListResponse)
async def get_agents():
    """获取所有已配置的 Agent 列表（已废弃，请使用 GET /api/v1/tools）"""
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


@app.get("/api/v1/tools", response_model=ToolListResponse)
async def get_tools(current_user: UserInfo = Depends(get_current_user)):
    """获取所有已配置的工具列表，按分类组织"""
    # 加载所有工具（只返回 visible=true 的工具）
    tools = tool_service.load_all_tools()
    
    # 按 category 聚合
    category_groups = tool_service.group_by_category(tools)
    
    # 转换为 API 响应格式
    categories = []
    for group in category_groups:
        tool_items = [
            ToolListItem(
                tool_id=tool.tool_id,
                name=tool.name,
                description=tool.description,
                icon=tool.icon,
                category=tool.category,
                visible=tool.visible,
                type=tool.type,
                welcome_message=tool.welcome_message
            )
            for tool in group['tools']
        ]
        
        categories.append(
            CategoryGroup(
                name=group['name'],
                icon=group['icon'],
                tools=tool_items
            )
        )
    
    return ToolListResponse(categories=categories)


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


@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """用户登录（支持用户名、邮箱或手机号）"""
    import re
    
    # 判断账号类型：手机号 > 邮箱 > 用户名（优先级）
    phone_pattern = r'^1[3-9]\d{9}$'
    email_pattern = r'^[^@]+@[^@]+\.[^@]+$'
    
    user = None
    if re.match(phone_pattern, request.account):
        # 手机号登录（优先级最高）
        user = user_service.get_user_by_phone(request.account)
    elif re.match(email_pattern, request.account):
        # 邮箱登录
        user = user_service.get_user_by_email(request.account)
    else:
        # 用户名登录（默认）
        user = user_service.get_user_by_username(request.account)
    
    # 验证用户是否存在和密码是否正确
    if user is None or not user.verify_password(request.password):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    
    # 生成JWT Token
    token = auth_service.generate_token(user, remember_me=request.remember_me)
    
    # 计算Token有效期（秒）
    expires_in = 604800 if request.remember_me else 86400  # 7天或24小时
    
    # 构建用户信息（不包含密码）
    user_info = UserInfo(
        user_id=user.user_id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar
    )
    
    return LoginResponse(
        token=token,
        user=user_info,
        expires_in=expires_in
    )


@app.get("/api/v1/auth/me", response_model=UserInfoResponse)
async def get_current_user(current_user: UserInfo = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return UserInfoResponse(user=current_user)


@app.get("/api/v1/admin/users", response_model=UserListResponse)
async def get_user_list(
    page: int = 1,
    page_size: int = 20,
    current_user: UserInfo = Depends(get_current_user)
):
    """获取用户列表（临时管理功能）"""
    users, total = user_service.get_all_users(page=page, page_size=page_size)
    
    # 转换为API响应格式
    user_items = [
        UserListItem(
            user_id=user.user_id,
            username=user.username,
            nickname=user.nickname,
            email=user.email,
            phone=user.phone,
            avatar=user.avatar,
            created_at=user.created_at
        )
        for user in users
    ]
    
    return UserListResponse(
        users=user_items,
        total=total,
        page=page,
        page_size=page_size
    )


@app.post("/api/v1/admin/users", response_model=CreateUserResponse)
async def create_user(
    request: CreateUserRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """创建新用户（临时管理功能）"""
    try:
        user = user_service.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            phone=request.phone,
            avatar=request.avatar
        )
        
        # 转换为API响应格式
        user_info = UserInfo(
            user_id=user.user_id,
            username=user.username,
            nickname=user.nickname,
            email=user.email,
            phone=user.phone,
            avatar=user.avatar
        )
        
        return CreateUserResponse(user=user_info)
    except ValueError as e:
        # 邮箱或手机号已存在
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
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

