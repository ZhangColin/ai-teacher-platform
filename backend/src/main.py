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
    ToolListResponse, ToolListItem, CategoryGroup,
    ConversationListResponse, ConversationListItem,
    SessionDetailResponse, Session,
    UpdateSessionRequest, UpdateSessionResponse
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


@app.get("/api/v1/tools/{tool_id}/conversations", response_model=ConversationListResponse)
async def get_conversations(
    tool_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """获取当前用户在当前工具下的所有历史对话列表"""
    # 验证工具是否存在
    tool = tool_service.get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    
    # 获取会话列表
    sessions = session_service.get_sessions_by_user_and_tool(
        user_id=current_user.user_id,
        tool_id=tool_id
    )
    
    # 转换为 API 响应格式
    conversations = [
        ConversationListItem(
            session_id=session.session_id,
            title=session.title,
            updated_at=session.updated_at
        )
        for session in sessions
    ]
    
    return ConversationListResponse(conversations=conversations)


@app.get("/api/v1/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """获取指定会话的完整消息历史"""
    # 获取会话（验证是否属于当前用户）
    session = session_service.get_session_by_id(session_id, user_id=current_user.user_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found"
        )
    
    # 获取消息列表
    messages = session_service.get_messages_by_session(session_id, user_id=current_user.user_id)
    
    # 转换为 API 响应格式（设置 timestamp 字段）
    message_list = []
    for msg in messages:
        message_list.append(
            Message(
                message_id=msg.message_id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                timestamp=msg.timestamp or msg.created_at,
                artifacts=msg.artifacts
            )
        )
    
    return SessionDetailResponse(
        session_id=session.session_id,
        tool_id=session.tool_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=message_list
    )


@app.patch("/api/v1/sessions/{session_id}", response_model=UpdateSessionResponse)
async def update_session_title(
    session_id: str,
    request: UpdateSessionRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """更新指定会话的标题"""
    # 更新会话标题
    session = session_service.update_session_title(
        session_id=session_id,
        new_title=request.title,
        user_id=current_user.user_id
    )
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found"
        )
    
    return UpdateSessionResponse(
        session_id=session.session_id,
        title=session.title
    )


@app.delete("/api/v1/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """删除指定会话（级联删除消息和成果物）"""
    success = session_service.delete_session(session_id, user_id=current_user.user_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found"
        )
    
    return {"message": "Session deleted successfully"}


@app.post("/api/v1/agents/{agent_id}/sessions", response_model=SessionInitResponse)
async def create_agent_session(agent_id: str):
    """为指定的 Agent 创建新会话（已废弃，请使用 POST /api/v1/tools/{tool_id}/chat）"""
    # 获取 Agent
    agent = agent_service.get_agent_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    # 生成欢迎消息
    welcome_message = await ai_service.generate_welcome_message(agent.system_prompt)
    
    # 解析欢迎消息中的成果物
    artifacts = artifact_parser.parse_from_markdown(welcome_message)
    
    # 注意：此 API 已废弃，不再创建真实会话
    # 返回一个临时 session_id（仅用于兼容旧代码）
    import uuid
    temp_session_id = str(uuid.uuid4())
    
    return SessionInitResponse(
        session_id=temp_session_id,
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
async def get_me(current_user: UserInfo = Depends(get_current_user)):
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


@app.post("/api/v1/tools/{tool_id}/chat", response_model=ChatResponse)
async def chat(
    tool_id: str,
    request: ChatRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """向指定工具发送消息，获取 AI 回复。如果 session_id 不存在，自动创建新会话。"""
    # 验证工具是否存在
    tool = tool_service.get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    
    # 处理会话：如果 session_id 不存在，创建新会话
    session_id = request.session_id
    session = None
    
    if session_id:
        # 验证会话是否存在且属于当前用户
        session = session_service.get_session_by_id(session_id, user_id=current_user.user_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found"
            )
    else:
        # 创建新会话（基于第一条消息自动生成标题）
        session = session_service.create_session(
            user_id=current_user.user_id,
            tool_id=tool_id,
            first_message=request.message
        )
        session_id = session.session_id
    
    # 获取历史消息
    history_list = []
    if request.history:
        # 使用请求中提供的历史消息
        for msg in request.history:
            if msg.role not in ["user", "assistant"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的消息角色: {msg.role}，必须是 'user' 或 'assistant'"
                )
            history_list.append({
                "role": msg.role,
                "content": msg.content
            })
    else:
        # 从数据库读取历史消息
        messages = session_service.get_messages_by_session(session_id, user_id=current_user.user_id)
        for msg in messages:
            history_list.append({
                "role": msg.role,
                "content": msg.content
            })
    
    # 添加当前用户消息到历史
    history_list.append({
        "role": "user",
        "content": request.message
    })
    
    # 调用 AI 服务进行对话
    reply = await ai_service.chat(
        system_prompt=tool.system_prompt,
        history=history_list[:-1],  # 不包含当前消息
        user_message=request.message
    )
    
    # 保存用户消息到数据库
    session_service.add_message(
        session_id=session_id,
        role="user",
        content=request.message,
        user_id=current_user.user_id
    )
    
    # 保存 AI 回复到数据库
    session_service.add_message(
        session_id=session_id,
        role="assistant",
        content=reply,
        user_id=current_user.user_id
    )
    
    # 解析成果物
    artifacts = artifact_parser.parse_from_markdown(reply)
    
    return ChatResponse(
        session_id=session_id,
        reply=reply,
        artifacts=artifacts
    )

