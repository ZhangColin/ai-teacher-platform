"""AI 教师平台后端主应用"""
import sys
import json
import logging
import uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
import os
import shutil

logger = logging.getLogger(__name__)

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
from src.services.conversion_service import ConversionService
from src.services.common_tool_service import CommonToolService
from src.services.work_service import WorkService
from src.services.course_service import CourseService
from src.services.title_generator import TitleGenerator
from src.config_loader import ConfigLoader
from src.models import (
    AgentListResponse, AgentListItem, SessionInitResponse,
    ChatRequest, ChatResponse, Message,
    LoginRequest, LoginResponse, UserInfo, UserInfoResponse,
    CreateUserRequest, CreateUserResponse, UserListResponse, UserListItem,
    UpdateUserRequest, UpdateUserResponse,
    ResetPasswordRequest, ResetPasswordResponse,
    ToolListResponse, ToolListItem, CategoryGroup,
    ConversationListResponse, ConversationListItem,
    SessionDetailResponse, Session,
    UpdateSessionRequest, UpdateSessionResponse,
    MarkdownToWordRequest,
    NavigationModule, NavigationResponse,
    CommonToolCategoryResponse, CommonToolDetail,
    WorkCategoryResponse, WorkDetail,
    AdminCommonToolListResponse, AdminCommonToolListItem,
    CreateBuiltInToolRequest, CreateToolResponse,
    UpdateToolRequest, UpdateToolResponse,
    MoveToolResponse, ToggleVisibilityResponse,
    AdminToolCategoryListResponse, AdminToolCategoryListItem,
    CreateToolCategoryRequest, CreateToolCategoryResponse,
    UpdateToolCategoryRequest, UpdateToolCategoryResponse,
    MoveCategoryResponse,
    AdminWorkListResponse, AdminWorkListItem,
    CreateWorkResponse, UpdateWorkRequest, UpdateWorkResponse,
    MoveWorkResponse, ToggleWorkVisibilityResponse,
    AdminWorkCategoryListResponse, AdminWorkCategoryListItem,
    CreateWorkCategoryRequest, CreateWorkCategoryResponse,
    UpdateWorkCategoryRequest, UpdateWorkCategoryResponse,
    MoveWorkCategoryResponse,
    CourseCategoryTreeResponse, CourseDocumentListResponse, CourseDocumentDetail,
    AdminCourseCategoryListResponse, AdminCourseCategoryListItem,
    CreateCourseCategoryRequest, UpdateCourseCategoryRequest,
    AdminCourseDocumentListResponse, AdminCourseDocumentListItem,
    UpdateCourseDocumentRequest
)

app = FastAPI(title="AI Teacher Platform Backend")

# 挂载静态文件目录
# 优先使用环境变量指定的目录，否则使用默认目录
static_dir = Path(os.getenv("STATIC_DIR", str(project_root / "backend" / "static")))
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
else:
    logger.warning(f"静态文件目录不存在: {static_dir}")

# 初始化服务
config_loader = ConfigLoader(config_root=str(project_root / "configs"))
agent_service = AgentService(config_dir=str(project_root / "configs" / "agents"))
tool_service = ToolService(
    config_dir=str(project_root / "configs" / "tools"),
    config_loader=config_loader
)
session_service = SessionService()
ai_service = AIService()
artifact_parser = ArtifactParser()
user_service = UserService()
auth_service = AuthService()
conversion_service = ConversionService()
common_tool_service = CommonToolService()
work_service = WorkService()
course_service = CourseService()
title_generator = TitleGenerator()

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
        avatar=user.avatar,
        is_admin=user.is_admin
    )


async def require_admin(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """
    管理员权限验证（依赖注入函数）
    
    Args:
        current_user: 当前登录用户
        
    Returns:
        UserInfo: 当前用户信息（已验证为管理员）
        
    Raises:
        HTTPException: 用户不是管理员
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    return current_user


@app.get("/api/v1/navigation", response_model=NavigationResponse)
async def get_navigation():
    """获取顶部导航模块配置（公开接口，无需认证）"""
    modules = config_loader.load_navigation()
    return NavigationResponse(modules=modules)


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
                welcome_message=tool.welcome_message,
                toolset_id=tool.toolset_id
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


@app.get("/api/v1/toolsets/{toolset_id}/tools", response_model=ToolListResponse)
async def get_toolset_tools(
    toolset_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """获取指定工具集的工具列表，按分类组织"""
    # 加载指定工具集的工具（只返回 visible=true 的工具）
    tools = tool_service.load_tools_by_toolset(toolset_id)
    
    # 按 category 聚合
    category_groups = tool_service.group_by_category(tools, toolset_id=toolset_id)
    
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
                welcome_message=tool.welcome_message,
                toolset_id=tool.toolset_id
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
    logger.info(f"获取会话消息 - 会话ID: {session_id}, 消息数量: {len(messages)}")
    for i, msg in enumerate(messages):
        logger.info(f"  消息 {i+1} - 角色: {msg.role}, 时间: {msg.created_at}, 内容前20字: {msg.content[:20]}")
    
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
        avatar=user.avatar,
        is_admin=user.is_admin
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
    is_admin: Optional[bool] = None,
    current_user: UserInfo = Depends(require_admin)
):
    """获取用户列表（管理员功能）- 支持分页和筛选"""
    # 限制每页最大数量
    if page_size > 100:
        page_size = 100
    
    users, total = user_service.get_all_users(
        page=page, 
        page_size=page_size,
        is_admin=is_admin
    )
    
    # 转换为API响应格式
    user_items = [
        UserListItem(
            user_id=user.user_id,
            username=user.username,
            nickname=user.nickname,
            email=user.email,
            phone=user.phone,
            avatar=user.avatar,
            is_admin=user.is_admin,
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


@app.post("/api/v1/admin/users", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """创建新用户（管理员功能）"""
    try:
        user = user_service.create_user(
            username=request.username,
            nickname=request.nickname,
            email=request.email,
            password=request.password,
            phone=request.phone,
            avatar=request.avatar,
            is_admin=request.is_admin
        )
        
        # 转换为API响应格式
        user_item = UserListItem(
            user_id=user.user_id,
            username=user.username,
            nickname=user.nickname,
            email=user.email,
            phone=user.phone,
            avatar=user.avatar,
            is_admin=user.is_admin,
            created_at=user.created_at
        )
        
        return CreateUserResponse(user=user_item)
    except ValueError as e:
        # 用户名、邮箱或手机号已存在
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@app.put("/api/v1/admin/users/{user_id}", response_model=UpdateUserResponse)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """更新用户信息（管理员功能）"""
    try:
        user = user_service.update_user(
            user_id=user_id,
            username=request.username,
            nickname=request.nickname,
            email=request.email,
            phone=request.phone,
            is_admin=request.is_admin
        )
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 转换为API响应格式
        user_item = UserListItem(
            user_id=user.user_id,
            username=user.username,
            nickname=user.nickname,
            email=user.email,
            phone=user.phone,
            avatar=user.avatar,
            is_admin=user.is_admin,
            created_at=user.created_at
        )
        
        return UpdateUserResponse(user=user_item)
    except ValueError as e:
        # 业务规则错误（如取消最后一个管理员、用户名/邮箱/手机号冲突）
        if "最后一个管理员" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )


@app.delete("/api/v1/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """删除用户（管理员功能）"""
    try:
        success = user_service.delete_user(user_id, current_user_id=current_user.user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return None  # 204 No Content
    except ValueError as e:
        # 业务规则错误（如删除自己、删除最后一个管理员）
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/admin/users/{user_id}/reset-password", response_model=ResetPasswordResponse)
async def reset_user_password(
    user_id: str,
    request: ResetPasswordRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """重置用户密码（管理员功能）"""
    try:
        success = user_service.reset_password(user_id, request.new_password)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return ResetPasswordResponse(
            message="密码已重置",
            new_password=request.new_password
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== 后台管理 - 常用工具管理接口 ====================

@app.get("/api/v1/admin/common-tools", response_model=AdminCommonToolListResponse)
async def get_admin_tools(
    page: int = 1,
    page_size: int = 20,
    category_id: Optional[str] = None,
    type: Optional[str] = None,
    visible: Optional[bool] = None,
    current_user: UserInfo = Depends(require_admin)
):
    """获取工具列表（管理后台）"""
    try:
        return common_tool_service.get_all_tools_admin(
            page=page,
            page_size=page_size,
            category_id=category_id,
            tool_type=type,
            visible=visible
        )
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/admin/common-tools/built-in", response_model=CreateToolResponse, status_code=status.HTTP_201_CREATED)
async def create_built_in_tool(
    request: CreateBuiltInToolRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """创建内置工具（管理后台）"""
    try:
        tool = common_tool_service.create_built_in_tool(request)
        return CreateToolResponse(tool=tool)
    except ValueError as e:
        if "分类不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/admin/common-tools/html", response_model=CreateToolResponse, status_code=status.HTTP_201_CREATED)
async def create_html_tool(
    name: str = Form(...),
    description: str = Form(...),
    category_id: str = Form(...),
    icon: Optional[str] = Form(None),
    order: int = Form(0),
    visible: bool = Form(True),
    html_file: UploadFile = File(...),
    current_user: UserInfo = Depends(require_admin)
):
    """上传HTML工具（管理后台）"""
    try:
        # 验证文件类型
        if not html_file.filename.endswith('.html'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持.html文件"
            )
        
        # 验证文件大小（5MB）
        content = await html_file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小超过5MB限制"
            )
        
        # 生成工具ID（使用UUID前8位确保唯一性且简短）
        import uuid
        tool_id = str(uuid.uuid4())[:8]
        
        # 创建存储目录
        tool_dir = Path(__file__).parent.parent / "static" / "common_tools" / "html" / tool_id
        tool_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        file_path = tool_dir / "index.html"
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 数据库存储相对路径
        html_path = f"common_tools/html/{tool_id}/index.html"
        
        # 创建工具记录
        tool = common_tool_service.create_html_tool(
            name=name,
            description=description,
            category_id=category_id,
            html_path=html_path,
            icon=icon,
            order=order,
            visible=visible
        )
        
        return CreateToolResponse(tool=tool)
        
    except ValueError as e:
        if "分类不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.put("/api/v1/admin/common-tools/{tool_id}", response_model=UpdateToolResponse)
async def update_tool(
    tool_id: str,
    request: UpdateToolRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """更新工具信息（管理后台）"""
    try:
        tool = common_tool_service.update_tool(tool_id, request)
        return UpdateToolResponse(tool=tool)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.delete("/api/v1/admin/common-tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """删除工具（管理后台）"""
    try:
        html_path = common_tool_service.delete_tool(tool_id)
        
        # 如果是HTML工具，删除文件
        if html_path:
            file_path = Path(__file__).parent.parent / "static" / html_path
            if file_path.exists():
                # 删除整个工具目录
                tool_dir = file_path.parent
                shutil.rmtree(tool_dir, ignore_errors=True)
        
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.post("/api/v1/admin/common-tools/{tool_id}/move-up", response_model=MoveToolResponse)
async def move_tool_up(
    tool_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """上移工具（管理后台）"""
    try:
        tool = common_tool_service.move_tool_up(tool_id)
        return MoveToolResponse(message="工具已上移", tool=tool)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/admin/common-tools/{tool_id}/move-down", response_model=MoveToolResponse)
async def move_tool_down(
    tool_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """下移工具（管理后台）"""
    try:
        tool = common_tool_service.move_tool_down(tool_id)
        return MoveToolResponse(message="工具已下移", tool=tool)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/admin/common-tools/{tool_id}/toggle-visibility", response_model=ToggleVisibilityResponse)
async def toggle_tool_visibility(
    tool_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """切换工具可见性（管理后台）"""
    try:
        tool, message = common_tool_service.toggle_tool_visibility(tool_id)
        return ToggleVisibilityResponse(message=message, tool=tool)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== 后台管理 - 工具分类管理接口 ====================

@app.get("/api/v1/admin/tool-categories", response_model=AdminToolCategoryListResponse)
async def get_admin_tool_categories(
    current_user: UserInfo = Depends(require_admin)
):
    """获取工具分类列表（管理后台）"""
    try:
        return common_tool_service.get_all_categories_admin()
    except Exception as e:
        logger.error(f"获取工具分类列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/admin/tool-categories", response_model=CreateToolCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_tool_category(
    request: CreateToolCategoryRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """创建工具分类（管理后台）"""
    try:
        category = common_tool_service.create_category(request)
        return CreateToolCategoryResponse(category=category)
    except ValueError as e:
        if "已存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.put("/api/v1/admin/tool-categories/{category_id}", response_model=UpdateToolCategoryResponse)
async def update_tool_category(
    category_id: str,
    request: UpdateToolCategoryRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """更新工具分类（管理后台）"""
    try:
        category = common_tool_service.update_category(category_id, request)
        return UpdateToolCategoryResponse(category=category)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        if "已被使用" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.delete("/api/v1/admin/tool-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool_category(
    category_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """删除工具分类（管理后台）"""
    try:
        common_tool_service.delete_category(category_id)
        return None
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        if "还有" in str(e) and "工具" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/admin/tool-categories/{category_id}/move-up", response_model=MoveCategoryResponse)
async def move_category_up(
    category_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """上移分类（管理后台）"""
    try:
        category = common_tool_service.move_category_up(category_id)
        return MoveCategoryResponse(message="分类已上移", category=category)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/admin/tool-categories/{category_id}/move-down", response_model=MoveCategoryResponse)
async def move_category_down(
    category_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """下移分类（管理后台）"""
    try:
        category = common_tool_service.move_category_down(category_id)
        return MoveCategoryResponse(message="分类已下移", category=category)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== 后台管理 - 作品管理接口 ====================

@app.get("/api/v1/admin/works", response_model=AdminWorkListResponse)
async def get_admin_works(
    page: int = 1,
    page_size: int = 20,
    category_id: Optional[str] = None,
    visible: Optional[bool] = None,
    current_user: UserInfo = Depends(require_admin)
):
    """获取作品列表（管理后台）"""
    try:
        return work_service.get_all_works_admin(
            page=page,
            page_size=page_size,
            category_id=category_id,
            visible=visible
        )
    except Exception as e:
        logger.error(f"获取作品列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/admin/works", response_model=CreateWorkResponse, status_code=status.HTTP_201_CREATED)
async def create_work(
    name: str = Form(...),
    description: str = Form(...),
    category_id: str = Form(...),
    icon: Optional[str] = Form(None),
    order: int = Form(0),
    visible: bool = Form(True),
    html_file: UploadFile = File(...),
    current_user: UserInfo = Depends(require_admin)
):
    """上传作品（管理后台）"""
    try:
        # 验证文件类型
        if not html_file.filename.endswith('.html'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持.html文件"
            )
        
        # 验证文件大小（10MB）
        content = await html_file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小超过10MB限制"
            )
        
        # 生成作品ID
        work_id = str(uuid.uuid4())[:8]
        
        # 创建存储目录
        work_dir = Path(__file__).parent.parent / "static" / "works" / "html" / work_id
        work_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        file_path = work_dir / "index.html"
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 数据库存储相对路径
        html_path = f"works/html/{work_id}/index.html"
        
        # 创建作品记录
        work = work_service.create_work(
            name=name,
            description=description,
            category_id=category_id,
            html_path=html_path,
            icon=icon,
            order=order,
            visible=visible
        )
        
        return CreateWorkResponse(work=work)
        
    except ValueError as e:
        if "分类不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.put("/api/v1/admin/works/{work_id}", response_model=UpdateWorkResponse)
async def update_work(
    work_id: str,
    request: UpdateWorkRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """更新作品信息（管理后台）"""
    try:
        work = work_service.update_work(work_id, request)
        return UpdateWorkResponse(work=work)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.delete("/api/v1/admin/works/{work_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work(
    work_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """删除作品（管理后台）"""
    try:
        html_path = work_service.delete_work(work_id)
        
        # 删除文件
        if html_path:
            file_path = Path(__file__).parent.parent / "static" / html_path
            if file_path.exists():
                work_dir = file_path.parent
                shutil.rmtree(work_dir, ignore_errors=True)
        
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.post("/api/v1/admin/works/{work_id}/move-up", response_model=MoveWorkResponse)
async def move_work_up(
    work_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """上移作品（管理后台）"""
    try:
        work = work_service.move_work_up(work_id)
        return MoveWorkResponse(message="作品已上移", work=work)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/admin/works/{work_id}/move-down", response_model=MoveWorkResponse)
async def move_work_down(
    work_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """下移作品（管理后台）"""
    try:
        work = work_service.move_work_down(work_id)
        return MoveWorkResponse(message="作品已下移", work=work)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/admin/works/{work_id}/toggle-visibility", response_model=ToggleWorkVisibilityResponse)
async def toggle_work_visibility(
    work_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """切换作品可见性（管理后台）"""
    try:
        work, message = work_service.toggle_work_visibility(work_id)
        return ToggleWorkVisibilityResponse(message=message, work=work)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== 后台管理 - 作品分类管理接口 ====================

@app.get("/api/v1/admin/work-categories", response_model=AdminWorkCategoryListResponse)
async def get_admin_work_categories(
    current_user: UserInfo = Depends(require_admin)
):
    """获取作品分类列表（管理后台）"""
    try:
        return work_service.get_all_categories_admin()
    except Exception as e:
        logger.error(f"获取作品分类列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/admin/work-categories", response_model=CreateWorkCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_work_category(
    request: CreateWorkCategoryRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """创建作品分类（管理后台）"""
    try:
        category = work_service.create_category(request)
        return CreateWorkCategoryResponse(category=category)
    except ValueError as e:
        if "已存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.put("/api/v1/admin/work-categories/{category_id}", response_model=UpdateWorkCategoryResponse)
async def update_work_category(
    category_id: str,
    request: UpdateWorkCategoryRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """更新作品分类（管理后台）"""
    try:
        category = work_service.update_category(category_id, request)
        return UpdateWorkCategoryResponse(category=category)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        if "已被使用" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.delete("/api/v1/admin/work-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_category(
    category_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """删除作品分类（管理后台）"""
    try:
        work_service.delete_category(category_id)
        return None
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        if "还有" in str(e) and "作品" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/admin/work-categories/{category_id}/move-up", response_model=MoveWorkCategoryResponse)
async def move_work_category_up(
    category_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """上移作品分类（管理后台）"""
    try:
        category = work_service.move_category_up(category_id)
        return MoveWorkCategoryResponse(message="分类已上移", category=category)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/admin/work-categories/{category_id}/move-down", response_model=MoveWorkCategoryResponse)
async def move_work_category_down(
    category_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """下移作品分类（管理后台）"""
    try:
        category = work_service.move_category_down(category_id)
        return MoveWorkCategoryResponse(message="分类已下移", category=category)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== 后台管理 - 课程目录管理接口 ====================

@app.get("/api/v1/admin/course-categories", response_model=AdminCourseCategoryListResponse)
async def get_admin_course_categories(
    current_user: UserInfo = Depends(require_admin)
):
    """获取课程目录列表（管理后台）"""
    try:
        return course_service.get_admin_categories()
    except Exception as e:
        logger.error(f"获取课程目录列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/admin/course-categories", status_code=status.HTTP_201_CREATED)
async def create_course_category(
    request: CreateCourseCategoryRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """创建课程目录（管理后台）"""
    try:
        category = course_service.create_category(request)
        return {"message": "目录创建成功", "category": category}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建课程目录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.put("/api/v1/admin/course-categories/{category_id}")
async def update_course_category(
    category_id: str,
    request: UpdateCourseCategoryRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """更新课程目录（管理后台）"""
    try:
        category = course_service.update_category(category_id, request)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目录不存在"
            )
        return {"message": "目录更新成功", "category": category}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新课程目录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.delete("/api/v1/admin/course-categories/{category_id}")
async def delete_course_category(
    category_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """删除课程目录（管理后台）"""
    try:
        success, error_msg = course_service.delete_category(category_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        return {"message": "目录删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除课程目录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/admin/course-categories/{category_id}/move-up")
async def move_course_category_up(
    category_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """上移课程目录（管理后台）"""
    try:
        success, error_msg = course_service.move_category_up(category_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        return {"message": "目录已上移"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上移课程目录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/admin/course-categories/{category_id}/move-down")
async def move_course_category_down(
    category_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """下移课程目录（管理后台）"""
    try:
        success, error_msg = course_service.move_category_down(category_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        return {"message": "目录已下移"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下移课程目录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== 后台管理 - 课程文档管理接口 ====================

@app.get("/api/v1/admin/course-documents", response_model=AdminCourseDocumentListResponse)
async def get_admin_course_documents(
    page: int = 1,
    page_size: int = 20,
    category_id: Optional[str] = None,
    current_user: UserInfo = Depends(require_admin)
):
    """获取课程文档列表（管理后台）"""
    try:
        return course_service.get_admin_documents(
            page=page,
            page_size=page_size,
            category_id=category_id
        )
    except Exception as e:
        logger.error(f"获取课程文档列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/admin/course-documents", status_code=status.HTTP_201_CREATED)
async def create_course_document(
    title: str = Form(...),
    summary: str = Form(...),
    category_id: str = Form(...),
    order: int = Form(0),
    markdown_file: UploadFile = File(...),
    current_user: UserInfo = Depends(require_admin)
):
    """创建课程文档（管理后台）"""
    try:
        # 验证文件类型
        if not markdown_file.filename.endswith(('.md', '.markdown')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持.md或.markdown文件"
            )
        
        # 验证文件大小（5MB）
        content = await markdown_file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小超过5MB限制"
            )
        
        # 解码Markdown内容
        markdown_content = content.decode('utf-8')
        
        # 创建文档
        document = course_service.create_document(
            title=title,
            summary=summary,
            category_id=category_id,
            markdown_content=markdown_content,
            order=order
        )
        
        return {"message": "文档创建成功", "document": document}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建课程文档失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.put("/api/v1/admin/course-documents/{doc_id}")
async def update_course_document(
    doc_id: str,
    request: UpdateCourseDocumentRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """更新课程文档（管理后台）"""
    try:
        document = course_service.update_document(doc_id, request)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        return {"message": "文档更新成功", "document": document}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新课程文档失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.delete("/api/v1/admin/course-documents/{doc_id}")
async def delete_course_document(
    doc_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """删除课程文档（管理后台）"""
    try:
        success, error_msg = course_service.delete_document(doc_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        return {"message": "文档删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除课程文档失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/admin/course-documents/{doc_id}/move-up")
async def move_course_document_up(
    doc_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """上移课程文档（管理后台）"""
    try:
        success, error_msg = course_service.move_document_up(doc_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        return {"message": "文档已上移"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上移课程文档失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/admin/course-documents/{doc_id}/move-down")
async def move_course_document_down(
    doc_id: str,
    current_user: UserInfo = Depends(require_admin)
):
    """下移课程文档（管理后台）"""
    try:
        success, error_msg = course_service.move_document_down(doc_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        return {"message": "文档已下移"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下移课程文档失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/tools/{tool_id}/chat", response_model=ChatResponse)
async def chat(
    tool_id: str,
    request: ChatRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """向指定工具发送消息，获取 AI 回复。如果 session_id 不存在，自动创建新会话。"""
    logger.info(f"🚀 chat() 函数被调用 - tool_id: {tool_id}, user: {current_user.username}, session_id: {request.session_id}")
    
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
    
    # 记录最终返回的完整内容（用于排查HTML问题）
    logger.info("=" * 80)
    logger.info("最终返回给前端的完整内容:")
    logger.info(f"内容总长度: {len(reply)} 字符")
    if '<html' in reply.lower() or '<!doctype' in reply.lower():
        logger.info("包含HTML内容")
        logger.info(f"完整HTML内容（前2000字符）:\n{reply[:2000]}")
        logger.info(f"完整HTML内容（后2000字符）:\n{reply[-2000:]}")
        # 检查HTML结构完整性
        html_tags = ['<!doctype', '<html', '</html>', '<head', '</head>', '<body', '</body>']
        for tag in html_tags:
            count = reply.lower().count(tag)
            if count > 0:
                logger.info(f"  {tag}: {count} 个")
    logger.info("=" * 80)
    
    # 保存用户消息到数据库（显式控制时间戳，确保消息顺序）
    from datetime import datetime, timedelta
    user_message_time = datetime.now()
    logger.info(f"保存用户消息 - 时间戳: {user_message_time}, 会话ID: {session_id}")
    session_service.add_message(
        session_id=session_id,
        role="user",
        content=request.message,
        user_id=current_user.user_id,
        created_at=user_message_time
    )
    
    # 保存 AI 回复到数据库（确保晚于用户消息 1 秒，避免精度问题）
    ai_message_time = user_message_time + timedelta(seconds=1)
    logger.info(f"保存 AI 消息 - 时间戳: {ai_message_time}, 会话ID: {session_id}")
    session_service.add_message(
        session_id=session_id,
        role="assistant",
        content=reply,
        user_id=current_user.user_id,
        created_at=ai_message_time
    )
    
    # 检查是否是第一轮对话，如果是则生成标题
    messages = session_service.get_messages_by_session(session_id, user_id=current_user.user_id)
    logger.info(f"会话消息数量检查 - 会话ID: {session_id}, 消息数: {len(messages)}")
    
    if len(messages) == 2:  # 第一轮对话：1条用户消息 + 1条AI回复
        try:
            logger.info(f"检测到第一轮对话，开始生成会话标题 - 用户消息: {request.message[:50]}")
            # 生成标题
            title = await title_generator.generate_title(request.message, reply)
            # 更新会话标题
            session_service.update_session_title(session_id, title, user_id=current_user.user_id)
            logger.info(f"会话标题已生成并更新：{title}")
        except Exception as e:
            logger.error(f"生成会话标题失败，使用降级方案: {e}", exc_info=True)
            # 降级方案：使用简单截取
            try:
                fallback_title = title_generator._fallback_title(request.message)
                session_service.update_session_title(session_id, fallback_title, user_id=current_user.user_id)
                logger.info(f"使用降级方案生成标题：{fallback_title}")
            except Exception as e2:
                logger.error(f"降级方案也失败了: {e2}", exc_info=True)
    else:
        logger.info(f"非第一轮对话，跳过标题生成")
    
    # 解析成果物
    artifacts = artifact_parser.parse_from_markdown(reply)
    logger.info(f"解析成果物完成，成果物数量: {len(artifacts)}")
    for i, artifact in enumerate(artifacts):
        logger.info(f"  成果物 {i+1}: type={artifact.type}, language={artifact.language}, content长度={len(artifact.content)}")
        if artifact.type == 'html':
            logger.info(f"    HTML内容预览（前500字符）:\n{artifact.content[:500]}")
            logger.info(f"    HTML内容预览（后500字符）:\n{artifact.content[-500:]}")
            # 检查HTML是否完整
            if '</html>' not in artifact.content.lower():
                logger.warning(f"    ⚠️ HTML成果物缺少 </html> 闭合标签！")
            if '<body' in artifact.content.lower() and '</body>' not in artifact.content.lower():
                logger.warning(f"    ⚠️ HTML成果物缺少 </body> 闭合标签！")
    
    return ChatResponse(
        session_id=session_id,
        reply=reply,
        artifacts=artifacts
    )


@app.post("/api/v1/tools/{tool_id}/chat/stream")
async def chat_stream(
    tool_id: str,
    request: ChatRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """向指定工具发送消息，获取 AI 流式回复。如果 session_id 不存在，自动创建新会话。"""
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
    
    # 保存用户消息到数据库（显式控制时间戳，确保消息顺序）
    from datetime import datetime, timedelta
    user_message_time = datetime.now()
    logger.info(f"保存用户消息 - 时间戳: {user_message_time}, 会话ID: {session_id}")
    session_service.add_message(
        session_id=session_id,
        role="user",
        content=request.message,
        user_id=current_user.user_id,
        created_at=user_message_time
    )
    
    # 流式生成回复
    async def generate_stream():
        full_reply = ""
        chunk_count = 0
        try:
            # 先发送 session_id
            yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"
            
            # 流式接收 AI 回复
            async for chunk in ai_service.chat_stream(
                system_prompt=tool.system_prompt,
                history=history_list,
                user_message=request.message
            ):
                if chunk:
                    chunk_count += 1
                    full_reply += chunk
                    # 发送内容块
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
            
            logger.info(f"流式输出完成 - 总chunk数: {chunk_count}, 总内容长度: {len(full_reply)} 字符")
            if 'html' in full_reply.lower() or '<html' in full_reply.lower():
                logger.info(f"HTML内容检测 - 包含<html>标签: {'<html' in full_reply.lower()}, 包含</html>标签: {'</html>' in full_reply.lower()}")
                logger.debug(f"HTML内容预览（前500字符）: {full_reply[:500]}")
                logger.debug(f"HTML内容预览（后500字符）: {full_reply[-500:]}")
            
            # 保存完整回复到数据库（确保晚于用户消息 1 秒，避免精度问题）
            ai_message_time = user_message_time + timedelta(seconds=1)
            logger.info(f"保存 AI 消息 - 时间戳: {ai_message_time}, 会话ID: {session_id}")
            session_service.add_message(
                session_id=session_id,
                role="assistant",
                content=full_reply,
                user_id=current_user.user_id,
                created_at=ai_message_time
            )
            
            # 检查是否是第一轮对话，如果是则生成标题
            messages = session_service.get_messages_by_session(session_id, user_id=current_user.user_id)
            logger.info(f"会话消息数量检查 - 会话ID: {session_id}, 消息数: {len(messages)}")
            
            if len(messages) == 2:  # 第一轮对话：1条用户消息 + 1条AI回复
                try:
                    logger.info(f"检测到第一轮对话，开始生成会话标题 - 用户消息: {request.message[:50]}")
                    # 生成标题
                    title = await title_generator.generate_title(request.message, full_reply)
                    # 更新会话标题
                    session_service.update_session_title(session_id, title, user_id=current_user.user_id)
                    logger.info(f"会话标题已生成并更新：{title}")
                    # 发送标题生成完成事件
                    yield f"data: {json.dumps({'type': 'title_generated', 'title': title})}\n\n"
                except Exception as e:
                    logger.error(f"生成会话标题失败，使用降级方案: {e}", exc_info=True)
                    # 降级方案：使用简单截取
                    try:
                        fallback_title = title_generator._fallback_title(request.message)
                        session_service.update_session_title(session_id, fallback_title, user_id=current_user.user_id)
                        logger.info(f"使用降级方案生成标题：{fallback_title}")
                        # 发送降级标题事件
                        yield f"data: {json.dumps({'type': 'title_generated', 'title': fallback_title})}\n\n"
                    except Exception as e2:
                        logger.error(f"降级方案也失败了: {e2}", exc_info=True)
            else:
                logger.info(f"非第一轮对话，跳过标题生成")
            
            # 解析成果物
            artifacts = artifact_parser.parse_from_markdown(full_reply)
            logger.info(f"解析成果物完成 - 成果物数量: {len(artifacts)}")
            
            # 发送完成信号和成果物（转换为字典格式以便序列化）
            artifacts_dict = [
                {
                    'type': a.type,
                    'content': a.content,
                    'language': a.language,
                    'timestamp': a.timestamp.isoformat() if a.timestamp else None
                }
                for a in artifacts
            ]
            yield f"data: {json.dumps({'type': 'done', 'artifacts': artifacts_dict})}\n\n"
            
        except Exception as e:
            logger.error(f"流式对话异常: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )


@app.post("/api/v1/convert/markdown-to-word")
async def convert_markdown_to_word(
    request: MarkdownToWordRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    将 Markdown 内容转换为 Word 文档并下载
    
    - **content**: Markdown 内容（必填）
    - **filename**: 文件名（可选，不含扩展名）
    
    Returns:
        Word 文档文件（application/vnd.openxmlformats-officedocument.wordprocessingml.document）
    """
    try:
        # 调用转换服务
        word_content, filename = conversion_service.markdown_to_word(
            markdown_content=request.content,
            filename=request.filename
        )
        
        # 返回 Word 文件
        from fastapi.responses import Response
        return Response(
            content=word_content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        # pandoc 不可用或转换失败
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"文档转换服务暂时不可用: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Markdown 转 Word 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文档转换失败，请稍后重试"
        )


# ==================== 常用工具模块 API ====================

@app.get("/api/v1/common-tools/categories", response_model=CommonToolCategoryResponse)
async def get_common_tool_categories(current_user: UserInfo = Depends(get_current_user)):
    """
    获取所有工具分类及其下的工具列表
    
    Returns:
        CommonToolCategoryResponse: 分类列表，每个分类包含该分类下的工具列表
        
    Notes:
        - 只返回 visible=True 的工具
        - 分类按 order 字段升序排列
        - 每个分类下的工具按 order 字段升序排列
        - 如果某个分类下没有可见工具，则不返回该分类
    """
    try:
        result = common_tool_service.get_categories_with_tools()
        return result
    except Exception as e:
        logger.error(f"获取工具分类列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取工具分类列表失败"
        )


@app.get("/api/v1/common-tools/tools/{tool_id}", response_model=CommonToolDetail)
async def get_common_tool_detail(
    tool_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取指定工具的详细信息
    
    Args:
        tool_id: 工具ID
        
    Returns:
        CommonToolDetail: 工具详情（包括分类信息、HTML访问URL等）
        
    Raises:
        HTTPException: 工具不存在或不可见时返回404
        
    Notes:
        - 只能查询 visible=True 的工具
        - HTML工具的 html_path 会被转换为完整的访问URL
    """
    try:
        result = common_tool_service.get_tool_detail(tool_id)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工具不存在或已下线"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取工具详情失败"
        )


# ==================== 作品展示模块 API ====================

@app.get("/api/v1/works/categories", response_model=WorkCategoryResponse)
async def get_work_categories(current_user: UserInfo = Depends(get_current_user)):
    """
    获取所有作品分类及其下的作品列表
    
    Returns:
        WorkCategoryResponse: 分类列表，每个分类包含该分类下的作品列表
        
    Notes:
        - 只返回 visible=True 的作品
        - 分类按 order 字段升序排列
        - 每个分类下的作品按 order 字段升序排列
        - 如果某个分类下没有可见作品，则不返回该分类
    """
    try:
        result = work_service.get_categories_with_works()
        return result
    except Exception as e:
        logger.error(f"获取作品分类列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取作品分类列表失败"
        )


@app.get("/api/v1/works/{work_id}", response_model=WorkDetail)
async def get_work_detail(
    work_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取指定作品的详细信息
    
    Args:
        work_id: 作品ID
        
    Returns:
        WorkDetail: 作品详情（包括分类信息、HTML访问URL等）
        
    Raises:
        HTTPException: 作品不存在或不可见时返回404
        
    Notes:
        - 只能查询 visible=True 的作品
        - html_path 会被转换为完整的访问URL
    """
    try:
        result = work_service.get_work_detail(work_id)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="作品不存在或已下线"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取作品详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取作品详情失败"
        )


# ==================== 课程文档模块 API ====================

@app.get("/api/v1/documents/categories", response_model=CourseCategoryTreeResponse)
async def get_course_category_tree(current_user: UserInfo = Depends(get_current_user)):
    """
    获取课程目录树结构
    
    Returns:
        CourseCategoryTreeResponse: 目录树，包含所有层级的目录
    """
    try:
        result = course_service.get_category_tree()
        return result
    except Exception as e:
        logger.error(f"获取课程目录树失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取课程目录树失败"
        )


@app.get("/api/v1/documents/category/{category_id}/documents", response_model=CourseDocumentListResponse)
async def get_course_documents_by_category(
    category_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取指定目录下的文档列表
    
    Args:
        category_id: 目录ID
        
    Returns:
        CourseDocumentListResponse: 文档列表
    """
    try:
        result = course_service.get_documents_by_category(category_id)
        return result
    except Exception as e:
        logger.error(f"获取目录文档列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取目录文档列表失败"
        )


@app.get("/api/v1/documents/{doc_id}", response_model=CourseDocumentDetail)
async def get_course_document_detail(
    doc_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取文档详情
    
    Args:
        doc_id: 文档ID
        
    Returns:
        CourseDocumentDetail: 文档详情，包含Markdown内容和上下文导航
        
    Raises:
        HTTPException: 文档不存在时返回404
    """
    try:
        result = course_service.get_document_detail(doc_id)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取文档详情失败"
        )

