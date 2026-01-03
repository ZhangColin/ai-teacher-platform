"""Domain models for Agent platform."""
import uuid
import bcrypt
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class Tool(BaseModel):
    """工具配置实体（聚合根）"""
    tool_id: str = Field(..., description="工具唯一标识符")
    name: str = Field(..., description="工具名称")
    description: Optional[str] = Field(None, description="工具描述")
    system_prompt: str = Field(..., description="系统提示词，定义工具的业务逻辑")
    category: str = Field(..., description="分类名称")
    icon: Optional[str] = Field(None, description="图标标识（可选）")
    visible: bool = Field(True, description="是否在工具选择器中显示")
    type: Literal["normal", "placeholder"] = Field("normal", description="工具类型")
    welcome_message: str = Field(..., description="欢迎语（配置化展示）")
    order: int = Field(999, description="排序顺序（数字越小越靠前，默认999）")
    
    def validate(self) -> bool:
        """验证工具配置是否完整有效"""
        if not self.tool_id or not self.name or not self.system_prompt:
            return False
        if not self.category or not self.welcome_message:
            return False
        return True


# 保留 Agent 类以保持向后兼容（后续可以删除）
class UIConfig(BaseModel):
    """UI 配置值对象（不可变）- 已废弃，保留以保持向后兼容"""
    model_config = ConfigDict(frozen=True)
    
    show_preview: bool = Field(..., description="是否开启侧边预览栏")
    preview_types: List[str] = Field(
        default_factory=list,
        description="支持的预览类型列表（如 ['markdown', 'html', 'svg']）"
    )


class Agent(BaseModel):
    """Agent 配置实体（聚合根）- 已废弃，保留以保持向后兼容，请使用 Tool"""
    agent_id: str = Field(..., description="Agent 唯一标识符")
    name: str = Field(..., description="功能名称")
    description: Optional[str] = Field(None, description="功能描述")
    system_prompt: str = Field(..., description="系统提示词，定义 Agent 的业务逻辑")
    ui_config: UIConfig = Field(..., description="UI 配置")
    capabilities: List[str] = Field(
        default_factory=list,
        description="Agent 能力列表（如 ['export_text', 'preview_html']）"
    )
    
    def validate(self) -> bool:
        """验证 Agent 配置是否完整有效"""
        if not self.agent_id or not self.name or not self.system_prompt:
            return False
        if not self.ui_config:
            return False
        return True


class AgentListItem(BaseModel):
    """Agent 列表项（用于 API 响应）- 已废弃，保留以保持向后兼容"""
    agent_id: str = Field(..., description="Agent 唯一标识符")
    name: str = Field(..., description="功能名称")
    description: Optional[str] = Field(None, description="功能描述")
    icon: Optional[str] = Field(None, description="图标标识（可选）")


class AgentListResponse(BaseModel):
    """Agent 列表响应 - 已废弃，保留以保持向后兼容"""
    agents: List[AgentListItem] = Field(..., description="Agent 列表")


class ToolListItem(BaseModel):
    """工具列表项（用于 API 响应）"""
    tool_id: str = Field(..., description="工具唯一标识符")
    name: str = Field(..., description="工具名称")
    description: Optional[str] = Field(None, description="工具描述")
    icon: Optional[str] = Field(None, description="图标标识（可选）")
    category: str = Field(..., description="分类名称")
    visible: bool = Field(True, description="是否在工具选择器中显示")
    type: Literal["normal", "placeholder"] = Field("normal", description="工具类型")
    welcome_message: Optional[str] = Field(None, description="欢迎语（可选，用于占位工具）")


class CategoryGroup(BaseModel):
    """分类组（用于 API 响应）"""
    name: str = Field(..., description="分类名称")
    icon: Optional[str] = Field(None, description="分类图标（可选）")
    tools: List[ToolListItem] = Field(..., description="该分类下的工具列表")


class ToolListResponse(BaseModel):
    """工具列表响应"""
    categories: List[CategoryGroup] = Field(..., description="按分类组织的工具列表")


class Artifact(BaseModel):
    """成果物值对象（不可变）"""
    model_config = ConfigDict(frozen=True)
    
    type: str = Field(..., description="成果物类型，由代码块语言标识决定")
    content: str = Field(..., description="代码块中的原始内容")
    language: str = Field(..., description="代码块的语言标识（如 'markdown', 'html', 'svg'）")
    timestamp: datetime = Field(default_factory=datetime.now, description="成果物生成时间")


class Session(BaseModel):
    """会话实体（聚合根）"""
    session_id: str = Field(..., description="会话 UUID")
    user_id: str = Field(..., description="关联的用户ID（UUID）")
    tool_id: str = Field(..., description="关联的工具标识")
    title: str = Field(..., description="会话标题（自动生成）")
    created_at: datetime = Field(default_factory=datetime.now, description="会话创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="最后更新时间")
    
    def generate_title(self, first_message: str, max_length: int = 50) -> str:
        """
        基于第一条用户消息生成会话标题
        
        Args:
            first_message: 第一条用户消息内容
            max_length: 标题最大长度（默认50）
            
        Returns:
            生成的会话标题
        """
        # 去除首尾空白
        title = first_message.strip()
        
        # 如果超过最大长度，截断并添加省略号
        if len(title) > max_length:
            title = title[:max_length].rstrip() + "..."
        
        # 如果为空，使用默认标题
        if not title:
            title = "新对话"
        
        return title
    
    def update_timestamp(self):
        """更新会话的最后更新时间"""
        self.updated_at = datetime.now()


class Message(BaseModel):
    """消息实体"""
    message_id: Optional[str] = Field(None, description="消息 UUID（可选，用于数据库存储）")
    session_id: Optional[str] = Field(None, description="关联的会话ID（可选，用于数据库存储）")
    role: Literal["user", "assistant"] = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容（Markdown 格式）")
    created_at: Optional[datetime] = Field(None, description="消息创建时间（可选，用于数据库存储）")
    timestamp: Optional[datetime] = Field(None, description="消息时间戳（API 响应使用，兼容前端）")
    artifacts: List[Artifact] = Field(
        default_factory=list,
        description="消息中包含的成果物列表（从 content 中解析）"
    )


class SessionInitResponse(BaseModel):
    """会话初始化响应"""
    session_id: str = Field(..., description="会话 UUID")
    welcome_message: str = Field(..., description="AI 生成的欢迎语（第一条消息）")
    ui_config: UIConfig = Field(..., description="UI 配置，如是否开启预览、预览类型等")
    artifacts: List[Artifact] = Field(
        default_factory=list,
        description="欢迎语中可能包含的成果物（如代码块）"
    )


class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., description="用户输入的消息", min_length=1)
    session_id: Optional[str] = Field(None, description="会话 UUID（可选）。如果有则继续会话，没有则创建新会话")
    history: Optional[List[Message]] = Field(
        None,
        description="历史消息列表（可选）。如果提供，后端使用该历史；如果不提供，后端从数据库读取"
    )


class ChatResponse(BaseModel):
    """对话响应"""
    session_id: str = Field(..., description="会话 UUID。首次调用返回新创建的session_id，后续调用返回原session_id")
    reply: str = Field(..., description="AI 的文本回复内容（完整 Markdown 文本）")
    artifacts: List[Artifact] = Field(
        default_factory=list,
        description="从回复中解析出的成果物列表（代码块内容）"
    )


class User(BaseModel):
    """用户实体（聚合根）"""
    user_id: str = Field(..., description="用户唯一标识（UUID）")
    username: str = Field(..., description="用户名（必填，用于登录，必须唯一）", min_length=1, max_length=50)
    nickname: Optional[str] = Field(None, description="用户昵称（可选，用于显示，如未填写则使用用户名）")
    email: Optional[str] = Field(None, description="用户邮箱（可选，用于登录）", pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, description="用户手机号（可选，用于登录）", pattern=r'^1[3-9]\d{9}$')
    password_hash: str = Field(..., description="密码哈希值（bcrypt加密）")
    avatar: Optional[str] = Field(None, description="用户头像URL（可选，默认头像）")
    created_at: datetime = Field(default_factory=datetime.now, description="用户创建时间")
    
    def verify_password(self, password: str) -> bool:
        """验证密码是否正确"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    @classmethod
    def create(cls, username: str, password: str, nickname: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None, avatar: Optional[str] = None) -> "User":
        """创建新用户（密码自动加密）"""
        # 生成UUID
        user_id = str(uuid.uuid4())
        
        # 使用bcrypt加密密码
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        return cls(
            user_id=user_id,
            username=username,
            nickname=nickname,
            email=email,
            phone=phone,
            password_hash=password_hash,
            avatar=avatar,
            created_at=datetime.now()
        )


class UserInfo(BaseModel):
    """用户信息（用于API响应，不包含密码）"""
    user_id: str = Field(..., description="用户唯一标识（UUID）")
    username: str = Field(..., description="用户名（用于登录）")
    nickname: Optional[str] = Field(None, description="用户昵称（可选，用于显示，如未填写则使用用户名）")
    email: Optional[str] = Field(None, description="用户邮箱（可选，用于登录）")
    phone: Optional[str] = Field(None, description="用户手机号（可选，用于登录）")
    avatar: Optional[str] = Field(None, description="用户头像URL（可选，默认头像）")


class LoginRequest(BaseModel):
    """登录请求"""
    account: str = Field(..., description="用户账号（邮箱或手机号）")
    password: str = Field(..., description="用户密码", min_length=6)
    remember_me: bool = Field(default=False, description="是否记住我（影响Token有效期）")


class LoginResponse(BaseModel):
    """登录响应"""
    token: str = Field(..., description="JWT Token，用于后续请求的身份验证")
    user: UserInfo = Field(..., description="用户基本信息")
    expires_in: int = Field(..., description="Token有效期（秒），如：604800（7天）或86400（24小时）")


class UserInfoResponse(BaseModel):
    """获取当前用户信息响应"""
    user: UserInfo = Field(..., description="用户基本信息")


class CreateUserRequest(BaseModel):
    """创建用户请求"""
    username: str = Field(..., description="用户名（必填，用于登录，必须唯一）", min_length=1, max_length=50)
    nickname: Optional[str] = Field(None, description="用户昵称（可选，用于显示，如未填写则使用用户名）")
    email: Optional[str] = Field(None, description="用户邮箱（可选，用于登录）", pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, description="用户手机号（可选，用于登录）", pattern=r'^1[3-9]\d{9}$')
    password: str = Field(..., description="用户密码", min_length=6)
    avatar: Optional[str] = Field(None, description="用户头像URL（可选，默认使用系统默认头像）")


class CreateUserResponse(BaseModel):
    """创建用户响应"""
    user: UserInfo = Field(..., description="新创建的用户信息")


class UserListItem(BaseModel):
    """用户列表项"""
    user_id: str = Field(..., description="用户唯一标识（UUID）")
    username: str = Field(..., description="用户名（用于登录）")
    nickname: Optional[str] = Field(None, description="用户昵称（可选，用于显示，如未填写则使用用户名）")
    email: Optional[str] = Field(None, description="用户邮箱（可选，用于登录）")
    phone: Optional[str] = Field(None, description="用户手机号（可选，用于登录）")
    avatar: Optional[str] = Field(None, description="用户头像URL")
    created_at: datetime = Field(..., description="用户创建时间")


class UserListResponse(BaseModel):
    """用户列表响应"""
    users: List[UserListItem] = Field(..., description="用户列表")
    total: int = Field(..., description="用户总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


class ConversationListItem(BaseModel):
    """对话列表项（用于 API 响应）"""
    session_id: str = Field(..., description="会话 UUID")
    title: str = Field(..., description="会话标题")
    updated_at: datetime = Field(..., description="最后更新时间")


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    conversations: List[ConversationListItem] = Field(..., description="对话列表")


class UpdateSessionRequest(BaseModel):
    """更新会话请求"""
    title: str = Field(..., description="新的会话标题", min_length=1, max_length=200)


class UpdateSessionResponse(BaseModel):
    """更新会话响应"""
    session_id: str = Field(..., description="会话 UUID")
    title: str = Field(..., description="更新后的会话标题")


class SessionDetailResponse(BaseModel):
    """会话详情响应"""
    session_id: str = Field(..., description="会话 UUID")
    tool_id: str = Field(..., description="工具唯一标识符")
    title: str = Field(..., description="会话标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="最后更新时间")
    messages: List[Message] = Field(..., description="消息列表")

