"""Domain models for Agent platform."""
import uuid
import bcrypt
import logging
import enum
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)


# ==================== 企业积分系统枚举 ====================

class EnterpriseStatus(str, enum.Enum):
    """企业状态枚举"""
    active = "active"
    suspended = "suspended"
    archived = "archived"


class PointTransactionType(str, enum.Enum):
    """积分交易类型枚举"""
    recharge = "recharge"
    gift = "gift"
    consume = "consume"
    refund = "refund"
    adjust = "adjust"


class PointSourceType(str, enum.Enum):
    """积分来源类型枚举"""
    online_payment = "online_payment"
    offline_payment = "offline_payment"
    admin_gift = "admin_gift"
    admin_adjust = "admin_adjust"


class NavigationModule(BaseModel):
    """导航模块配置（用于顶部导航栏）"""
    name: str = Field(..., description="模块显示名称")
    type: Literal["ai_tools", "page"] = Field(..., description="模块类型：ai_tools=AI工具模块，page=独立页面")
    config_source: Optional[str] = Field(None, description="配置来源（type=ai_tools时使用，工具集配置目录路径，如：tools/ai_tools）")
    page_path: Optional[str] = Field(None, description="页面路径（type=page时使用，前端路由路径，如：/common-tools）")
    icon: Optional[str] = Field(None, description="图标标识（可选）")
    order: int = Field(999, description="排序顺序（数字越小越靠前，默认999）")

    def validate(self) -> bool:
        """验证导航模块配置是否有效"""
        if not self.name or not self.type:
            return False
        # ai_tools 类型必须有 config_source
        if self.type == "ai_tools" and not self.config_source:
            return False
        # page 类型必须有 page_path
        if self.type == "page" and not self.page_path:
            return False
        return True


class NavigationResponse(BaseModel):
    """导航配置响应"""
    modules: List[NavigationModule] = Field(..., description="导航模块列表")


class Tool(BaseModel):
    """工具配置实体（聚合根）"""
    tool_id: str = Field(..., description="工具唯一标识符")
    name: str = Field(..., description="工具名称")
    description: Optional[str] = Field(None, description="工具描述")
    system_prompt: Optional[str] = Field(None, description="系统提示词，定义工具的业务逻辑（如使用system_prompt_file则可选）")
    category: str = Field(..., description="分类名称")
    icon: Optional[str] = Field(None, description="图标标识（可选）")
    visible: bool = Field(True, description="是否在工具选择器中显示")
    type: Literal["normal", "placeholder", "media"] = Field("normal", description="工具类型")
    welcome_message: str = Field(..., description="欢迎语（配置化展示）")
    order: int = Field(999, description="排序顺序（数字越小越靠前，默认999）")
    navigation_module_id: str = Field("ai_tools", description="所属导航模块ID（默认ai_tools，保持向后兼容）")
    system_prompt_file: Optional[str] = Field(None, description="系统提示词文件路径（相对于工具集配置目录），如果指定则从文件加载system_prompt")
    model: Optional[str] = Field(None, description="使用的AI模型（格式：provider:model_name，如 deepseek:deepseek-coder），如果未指定则使用系统默认")
    
    # 多模态支持字段（新增）
    content_type: Optional[Literal["text", "multimodal"]] = Field(
        "text", 
        description="内容类型：text=文本对话，multimodal=多模态生成（图片、音频、视频）"
    )
    media_type: Optional[Literal["image", "audio", "video"]] = Field(
        None, 
        description="媒体类型（仅当content_type=multimodal时有效）"
    )
    
    def validate(self) -> bool:
        """验证工具配置是否完整有效"""
        if not self.tool_id or not self.name:
            return False
        if not self.category or not self.welcome_message:
            return False
        # system_prompt 和 system_prompt_file 至少有一个
        if not self.system_prompt and not self.system_prompt_file:
            return False
        # 如果是多模态工具，必须指定media_type
        if self.content_type == "multimodal" and not self.media_type:
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
    type: Literal["normal", "placeholder", "media"] = Field("normal", description="工具类型")
    welcome_message: Optional[str] = Field(None, description="欢迎语（可选，用于占位工具）")
    navigation_module_id: str = Field(..., description="所属导航模块ID")
    model: Optional[str] = Field(None, description="使用的AI模型（格式：provider:model_name），如果未指定则使用系统默认")

    # 多模态支持字段（新增）
    content_type: Optional[Literal["text", "multimodal"]] = Field(
        "text",
        description="内容类型：text=文本对话，multimodal=多模态生成"
    )
    media_type: Optional[Literal["image", "audio", "video"]] = Field(
        None,
        description="媒体类型（仅当content_type=multimodal时有效）"
    )


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

    # 模型选择相关字段（新增）
    model_provider: Optional[str] = Field(None, description="AI服务提供商")
    model_name: Optional[str] = Field(None, description="使用的模型名称")
    
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


class MultiModalContent(BaseModel):
    """多模态内容结构（用于JSON序列化）"""
    content_type: Literal["image", "audio", "video"] = Field(..., description="内容类型")
    media_urls: List[str] = Field(..., description="媒体文件URL列表（支持多个）")
    metadata: Optional[dict] = Field(None, description="额外元数据")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content_type": "image",
                "media_urls": ["https://example.com/image1.png", "https://example.com/image2.png"],
                "metadata": {
                    "size": "1024x1024",
                    "count": 2,
                    "style": "auto",
                    "cost": {
                        "tokens": 0,
                        "amount": 0.0,
                        "currency": "CNY"
                    }
                }
            }
        }
    )


class TokenUsage(BaseModel):
    """Token使用信息值对象"""
    model_provider: str = Field(..., description="AI服务提供商（deepseek/openai/kimi/glm）")
    model_name: str = Field(..., description="模型名称（如deepseek-chat/gpt-4）")
    prompt_tokens: int = Field(..., description="提示词token数")
    completion_tokens: int = Field(..., description="完成token数")
    total_tokens: int = Field(..., description="总token数")


class Message(BaseModel):
    """消息实体（支持文本和多模态）"""
    message_id: Optional[str] = Field(None, description="消息 UUID（可选，用于数据库存储）")
    session_id: Optional[str] = Field(None, description="关联的会话ID（可选，用于数据库存储）")
    role: Literal["user", "assistant"] = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容（文本消息为Markdown格式，多模态消息为用户提示词）")
    created_at: Optional[datetime] = Field(None, description="消息创建时间（可选，用于数据库存储）")
    timestamp: Optional[datetime] = Field(None, description="消息时间戳（API 响应使用，兼容前端）")
    artifacts: List[Artifact] = Field(
        default_factory=list,
        description="消息中包含的成果物列表（从 content 中解析）"
    )

    # 多模态支持字段
    media_content: Optional[str] = Field(
        None,
        description="多模态内容JSON字符串（图片、音频、视频等）。存储MultiModalContent的JSON序列化结果"
    )

    # 模型和Token相关字段（新增）
    model_provider: Optional[str] = Field(None, description="AI服务提供商")
    model_name: Optional[str] = Field(None, description="使用的模型名称")
    prompt_tokens: Optional[int] = Field(None, description="用户消息的token消耗")
    completion_tokens: Optional[int] = Field(None, description="AI回复的token消耗")
    total_tokens: Optional[int] = Field(None, description="本条消息的总token消耗")

    @property
    def parsed_media_content(self) -> Optional[MultiModalContent]:
        """
        解析多模态内容JSON为对象
        
        Returns:
            MultiModalContent对象，如果media_content为空则返回None
        """
        if self.media_content:
            try:
                import json
                data = json.loads(self.media_content)
                return MultiModalContent(**data)
            except Exception as e:
                logger.warning(f"解析多模态内容失败: {e}")
                return None
        return None
    
    def set_media_content(self, media: MultiModalContent) -> None:
        """
        设置多模态内容
        
        Args:
            media: MultiModalContent对象
        """
        import json
        self.media_content = json.dumps(media.model_dump(), ensure_ascii=False)


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
    model: Optional[str] = Field(None, description="会话级别的模型选择（格式：provider:model_name，如 deepseek:deepseek-chat）")


class ChatResponse(BaseModel):
    """对话响应"""
    session_id: str = Field(..., description="会话 UUID。首次调用返回新创建的session_id，后续调用返回原session_id")
    reply: str = Field(..., description="AI 的文本回复内容（完整 Markdown 文本）")
    artifacts: List[Artifact] = Field(
        default_factory=list,
        description="从回复中解析出的成果物列表（代码块内容）"
    )
    token_usage: Optional[TokenUsage] = Field(None, description="本次对话的token消耗（调试用，前端不展示）")


class User(BaseModel):
    """用户实体（聚合根）"""
    user_id: str = Field(..., description="用户唯一标识（UUID）")
    username: str = Field(..., description="用户名（必填，用于登录，必须唯一）", min_length=1, max_length=50)
    nickname: Optional[str] = Field(None, description="用户昵称（可选，用于显示，如未填写则使用用户名）")
    email: Optional[str] = Field(None, description="用户邮箱（可选，用于登录）", pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, description="用户手机号（可选，用于登录）", pattern=r'^1[3-9]\d{9}$')
    password_hash: str = Field(..., description="密码哈希值（bcrypt加密）")
    avatar: Optional[str] = Field(None, description="用户头像URL（可选，默认头像）")
    is_admin: bool = Field(False, description="是否为管理员（默认为false）")
    is_active: bool = Field(True, description="用户是否激活（默认为true）")
    enterprise_id: Optional[str] = Field(None, description="所属企业ID")
    is_enterprise_admin: bool = Field(False, description="是否为企业管理员")
    created_at: datetime = Field(default_factory=datetime.now, description="用户创建时间")

    def verify_password(self, password: str) -> bool:
        """验证密码是否正确"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def _hash_password(self, password: str) -> str:
        """哈希密码（内部方法）"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def is_administrator(self) -> bool:
        """判断是否为管理员"""
        return self.is_admin

    @classmethod
    def create(cls, username: str, password: str, nickname: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None, avatar: Optional[str] = None, is_admin: bool = False) -> "User":
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
            is_admin=is_admin,
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
    is_admin: bool = Field(False, description="是否为管理员")
    # 企业相关字段
    enterprise_id: Optional[str] = Field(None, description="所属企业ID")
    enterprise_name: Optional[str] = Field(None, description="所属企业名称")
    is_enterprise_admin: bool = Field(False, description="是否为企业管理员")


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
    is_admin: bool = Field(False, description="是否为管理员（默认为false）")
    is_active: bool = Field(True, description="用户是否激活（默认为true）")
    # 企业相关字段
    enterprise_id: str = Field(..., description="所属企业ID（必填）")
    is_enterprise_admin: bool = Field(False, description="是否为企业管理员（默认为false）")


class UserListItem(BaseModel):
    """用户列表项"""
    user_id: str = Field(..., description="用户唯一标识（UUID）")
    username: str = Field(..., description="用户名（用于登录）")
    nickname: Optional[str] = Field(None, description="用户昵称（可选，用于显示，如未填写则使用用户名）")
    email: Optional[str] = Field(None, description="用户邮箱（可选，用于登录）")
    phone: Optional[str] = Field(None, description="用户手机号（可选，用于登录）")
    avatar: Optional[str] = Field(None, description="用户头像URL")
    is_admin: bool = Field(False, description="是否为管理员")
    is_active: bool = Field(True, description="用户是否激活")
    enterprise_id: Optional[str] = Field(None, description="所属企业ID")
    enterprise_name: Optional[str] = Field(None, description="所属企业名称")
    is_enterprise_admin: bool = Field(False, description="是否为企业管理员")
    total_consumed: int = Field(0, description="总消耗积分")
    created_at: datetime = Field(..., description="用户创建时间")


class CreateUserResponse(BaseModel):
    """创建用户响应"""
    user: UserListItem = Field(..., description="新创建的用户信息")


class UserListResponse(BaseModel):
    """用户列表响应"""
    users: List[UserListItem] = Field(..., description="用户列表")
    total: int = Field(..., description="用户总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


class UpdateUserRequest(BaseModel):
    """更新用户信息请求"""
    username: Optional[str] = Field(None, description="用户名", min_length=1, max_length=50)
    nickname: Optional[str] = Field(None, description="用户昵称", max_length=50)
    email: Optional[str] = Field(None, description="用户邮箱", pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, description="用户手机号", pattern=r'^1[3-9]\d{9}$')
    is_admin: Optional[bool] = Field(None, description="是否为管理员")
    is_active: Optional[bool] = Field(None, description="用户是否激活")
    # 企业相关字段
    enterprise_id: Optional[str] = Field(None, description="所属企业ID")
    is_enterprise_admin: Optional[bool] = Field(None, description="是否为企业管理员")


class UpdateUserResponse(BaseModel):
    """更新用户信息响应"""
    user: UserListItem = Field(..., description="更新后的用户信息")


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    new_password: str = Field(..., description="新密码", min_length=6)


class ResetPasswordResponse(BaseModel):
    """重置密码响应"""
    message: str = Field(..., description="操作结果消息")
    new_password: str = Field(..., description="新密码（明文，用于告知用户）")


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


class MarkdownToWordRequest(BaseModel):
    """Markdown转Word请求"""
    content: str = Field(..., description="Markdown内容", min_length=1)
    filename: Optional[str] = Field(None, description="生成的文件名（不含扩展名），默认使用时间戳")


# ==================== 常用工具模块 ====================

class ToolCategory(BaseModel):
    """工具分类实体（聚合根）"""
    id: str = Field(..., description="分类唯一标识（UUID）")
    name: str = Field(..., description="分类名称（如：文档工具）", min_length=1, max_length=50)
    icon: Optional[str] = Field(None, description="分类图标（heroicons名称，可选）")
    order: int = Field(default=0, description="排序顺序（数字越小越靠前）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class CommonTool(BaseModel):
    """常用工具实体（聚合根）"""
    id: str = Field(..., description="工具唯一标识（UUID）")
    name: str = Field(..., description="工具名称（如：Markdown编辑器）", min_length=1, max_length=100)
    description: str = Field(..., description="工具描述（一句话说明工具功能）", min_length=1, max_length=200)
    category_id: str = Field(..., description="所属分类ID（关联ToolCategory）")
    type: Literal["built_in", "html"] = Field(..., description="工具类型：'built_in'（内置工具）或 'html'（HTML工具）")
    icon: Optional[str] = Field(None, description="图标标识（heroicons名称，如：'document-text'）")
    html_path: Optional[str] = Field(None, description="HTML文件路径（仅type='html'时必填，相对于static目录）")
    order: int = Field(default=0, description="排序顺序（数字越小越靠前）")
    visible: bool = Field(default=True, description="是否可见（用于后台控制工具上下线）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    def is_html_tool(self) -> bool:
        """判断是否为HTML工具"""
        return self.type == "html"
    
    def is_built_in_tool(self) -> bool:
        """判断是否为内置工具"""
        return self.type == "built_in"
    
    def get_frontend_route(self) -> str:
        """获取前端路由路径（用于内置工具跳转）"""
        return f"/common-tools/tool/{self.id}"
    
    def validate(self) -> bool:
        """验证工具配置是否完整有效"""
        # HTML工具必须有html_path
        if self.type == "html" and not self.html_path:
            return False
        # 内置工具不应有html_path
        if self.type == "built_in" and self.html_path:
            return False
        return True


class CommonToolListItem(BaseModel):
    """工具列表项（用于API响应）"""
    id: str = Field(..., description="工具ID")
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    type: Literal["built_in", "html"] = Field(..., description="工具类型：'built_in' 或 'html'")
    icon: Optional[str] = Field(None, description="图标标识")
    order: int = Field(..., description="排序顺序")


class ToolCategoryGroup(BaseModel):
    """工具分类组（用于API响应）"""
    id: str = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    icon: Optional[str] = Field(None, description="分类图标")
    order: int = Field(..., description="分类排序")
    tools: List[CommonToolListItem] = Field(..., description="该分类下的工具列表")


class CommonToolCategoryResponse(BaseModel):
    """工具分类响应（用于API响应）"""
    categories: List[ToolCategoryGroup] = Field(..., description="分类列表（按order排序）")


class CommonToolDetail(BaseModel):
    """工具详情（用于API响应）"""
    id: str = Field(..., description="工具ID")
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    category_id: str = Field(..., description="所属分类ID")
    category_name: str = Field(..., description="所属分类名称")
    type: Literal["built_in", "html"] = Field(..., description="工具类型：'built_in' 或 'html'")
    icon: Optional[str] = Field(None, description="图标标识")
    order: int = Field(..., description="排序顺序")
    html_url: Optional[str] = Field(None, description="HTML文件访问URL（仅type='html'时有值）")
    created_at: datetime = Field(..., description="创建时间")


# ==================== 作品展示模块 ====================

class WorkCategory(BaseModel):
    """作品分类实体（聚合根）"""
    id: str = Field(..., description="分类唯一标识（UUID）")
    name: str = Field(..., description="分类名称", min_length=1, max_length=50)
    icon: Optional[str] = Field(None, description="分类图标（heroicons名称，可选）")
    order: int = Field(default=0, description="排序顺序（数字越小越靠前）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class Work(BaseModel):
    """作品实体（聚合根）"""
    id: str = Field(..., description="作品唯一标识（UUID）")
    name: str = Field(..., description="作品名称", min_length=1, max_length=100)
    description: str = Field(..., description="作品描述", min_length=1, max_length=200)
    category_id: str = Field(..., description="所属分类ID（关联WorkCategory）")
    icon: Optional[str] = Field(None, description="图标标识（heroicons名称）")
    html_path: str = Field(..., description="HTML文件路径（相对于static目录，必填）")
    order: int = Field(default=0, description="排序顺序（数字越小越靠前）")
    visible: bool = Field(default=True, description="是否可见（用于后台控制作品上下线）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    def get_html_url(self) -> str:
        """获取HTML文件访问URL"""
        return f"/static/{self.html_path}"


class WorkListItem(BaseModel):
    """作品列表项（用于API响应）"""
    id: str = Field(..., description="作品ID")
    name: str = Field(..., description="作品名称")
    description: str = Field(..., description="作品描述")
    icon: Optional[str] = Field(None, description="图标标识")
    order: int = Field(..., description="排序顺序")


class WorkCategoryGroup(BaseModel):
    """作品分类组（用于API响应）"""
    id: str = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    icon: Optional[str] = Field(None, description="分类图标")
    order: int = Field(..., description="分类排序")
    works: List[WorkListItem] = Field(..., description="该分类下的作品列表")


class WorkCategoryResponse(BaseModel):
    """作品分类响应（用于API响应）"""
    categories: List[WorkCategoryGroup] = Field(..., description="分类列表（按order排序）")


class WorkDetail(BaseModel):
    """作品详情（用于API响应）"""
    id: str = Field(..., description="作品ID")
    name: str = Field(..., description="作品名称")
    description: str = Field(..., description="作品描述")
    category_id: str = Field(..., description="所属分类ID")
    category_name: str = Field(..., description="所属分类名称")
    icon: Optional[str] = Field(None, description="图标标识")
    order: int = Field(..., description="排序顺序")
    html_url: str = Field(..., description="HTML文件访问URL")
    created_at: datetime = Field(..., description="创建时间")


# ==================== 后台管理 - 工具管理模块 ====================

class AdminCommonToolListItem(BaseModel):
    """管理后台 - 工具列表项"""
    id: str = Field(..., description="工具ID")
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    category_id: str = Field(..., description="所属分类ID")
    category_name: str = Field(..., description="所属分类名称")
    type: str = Field(..., description="工具类型：'built_in' 或 'html'")
    icon: Optional[str] = Field(None, description="图标标识")
    html_path: Optional[str] = Field(None, description="HTML文件路径（仅HTML工具）")
    order: int = Field(..., description="排序顺序")
    visible: bool = Field(..., description="是否可见")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class AdminCommonToolListResponse(BaseModel):
    """管理后台 - 工具列表响应"""
    tools: List[AdminCommonToolListItem] = Field(..., description="工具列表")
    total: int = Field(..., description="工具总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


class CreateBuiltInToolRequest(BaseModel):
    """创建内置工具请求"""
    name: str = Field(..., description="工具名称", min_length=1, max_length=100)
    description: str = Field(..., description="工具描述", min_length=1, max_length=200)
    category_id: str = Field(..., description="所属分类ID")
    icon: Optional[str] = Field(None, description="图标标识（heroicons名称）")
    order: int = Field(0, description="排序顺序（默认0）")
    visible: bool = Field(True, description="是否可见（默认true）")


class UpdateToolRequest(BaseModel):
    """更新工具请求"""
    name: Optional[str] = Field(None, description="工具名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="工具描述", min_length=1, max_length=200)
    category_id: Optional[str] = Field(None, description="所属分类ID")
    icon: Optional[str] = Field(None, description="图标标识（heroicons名称）")
    order: Optional[int] = Field(None, description="排序顺序")
    visible: Optional[bool] = Field(None, description="是否可见")


class CreateToolResponse(BaseModel):
    """创建工具响应"""
    tool: AdminCommonToolListItem = Field(..., description="新创建的工具信息")


class UpdateToolResponse(BaseModel):
    """更新工具响应"""
    tool: AdminCommonToolListItem = Field(..., description="更新后的工具信息")


class MoveToolResponse(BaseModel):
    """移动工具响应"""
    message: str = Field(..., description="操作结果消息")
    tool: AdminCommonToolListItem = Field(..., description="移动后的工具信息")


class ToggleVisibilityResponse(BaseModel):
    """切换可见性响应"""
    message: str = Field(..., description="操作结果消息")
    tool: AdminCommonToolListItem = Field(..., description="更新后的工具信息")


# ==================== 后台管理 - 工具分类管理模块 ====================

class AdminToolCategoryListItem(BaseModel):
    """管理后台 - 工具分类列表项"""
    id: str = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    icon: Optional[str] = Field(None, description="分类图标")
    order: int = Field(..., description="排序顺序")
    tool_count: int = Field(..., description="该分类下的工具数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class AdminToolCategoryListResponse(BaseModel):
    """管理后台 - 工具分类列表响应"""
    categories: List[AdminToolCategoryListItem] = Field(..., description="分类列表")


class CreateToolCategoryRequest(BaseModel):
    """创建工具分类请求"""
    name: str = Field(..., description="分类名称", min_length=1, max_length=50)
    icon: Optional[str] = Field(None, description="分类图标（heroicons名称）")
    order: int = Field(0, description="排序顺序（默认0）")


class UpdateToolCategoryRequest(BaseModel):
    """更新工具分类请求"""
    name: Optional[str] = Field(None, description="分类名称", min_length=1, max_length=50)
    icon: Optional[str] = Field(None, description="分类图标（heroicons名称）")
    order: Optional[int] = Field(None, description="排序顺序")


class CreateToolCategoryResponse(BaseModel):
    """创建工具分类响应"""
    category: AdminToolCategoryListItem = Field(..., description="新创建的分类信息")


class UpdateToolCategoryResponse(BaseModel):
    """更新工具分类响应"""
    category: AdminToolCategoryListItem = Field(..., description="更新后的分类信息")


class MoveCategoryResponse(BaseModel):
    """移动分类响应"""
    message: str = Field(..., description="操作结果消息")
    category: AdminToolCategoryListItem = Field(..., description="移动后的分类信息")


# ==================== 后台管理 - 作品管理模块 ====================

class AdminWorkListItem(BaseModel):
    """管理后台 - 作品列表项"""
    id: str = Field(..., description="作品ID")
    name: str = Field(..., description="作品名称")
    description: str = Field(..., description="作品描述")
    category_id: str = Field(..., description="所属分类ID")
    category_name: str = Field(..., description="所属分类名称")
    icon: Optional[str] = Field(None, description="图标标识")
    html_path: str = Field(..., description="HTML文件路径")
    order: int = Field(..., description="排序顺序")
    visible: bool = Field(..., description="是否可见")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class AdminWorkListResponse(BaseModel):
    """管理后台 - 作品列表响应"""
    works: List[AdminWorkListItem] = Field(..., description="作品列表")
    total: int = Field(..., description="作品总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


class UpdateWorkRequest(BaseModel):
    """更新作品请求"""
    name: Optional[str] = Field(None, description="作品名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="作品描述", min_length=1, max_length=200)
    category_id: Optional[str] = Field(None, description="所属分类ID")
    icon: Optional[str] = Field(None, description="图标标识（heroicons名称）")
    order: Optional[int] = Field(None, description="排序顺序")
    visible: Optional[bool] = Field(None, description="是否可见")


class CreateWorkResponse(BaseModel):
    """创建作品响应"""
    work: AdminWorkListItem = Field(..., description="新创建的作品信息")


class UpdateWorkResponse(BaseModel):
    """更新作品响应"""
    work: AdminWorkListItem = Field(..., description="更新后的作品信息")


class MoveWorkResponse(BaseModel):
    """移动作品响应"""
    message: str = Field(..., description="操作结果消息")
    work: AdminWorkListItem = Field(..., description="移动后的作品信息")


class ToggleWorkVisibilityResponse(BaseModel):
    """切换作品可见性响应"""
    message: str = Field(..., description="操作结果消息")
    work: AdminWorkListItem = Field(..., description="更新后的作品信息")


# ==================== 后台管理 - 作品分类管理模块 ====================

class AdminWorkCategoryListItem(BaseModel):
    """管理后台 - 作品分类列表项"""
    id: str = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    icon: Optional[str] = Field(None, description="分类图标")
    order: int = Field(..., description="排序顺序")
    work_count: int = Field(..., description="该分类下的作品数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class AdminWorkCategoryListResponse(BaseModel):
    """管理后台 - 作品分类列表响应"""
    categories: List[AdminWorkCategoryListItem] = Field(..., description="分类列表")


class CreateWorkCategoryRequest(BaseModel):
    """创建作品分类请求"""
    name: str = Field(..., description="分类名称", min_length=1, max_length=50)
    icon: Optional[str] = Field(None, description="分类图标（heroicons名称）")
    order: int = Field(0, description="排序顺序（默认0）")


class UpdateWorkCategoryRequest(BaseModel):
    """更新作品分类请求"""
    name: Optional[str] = Field(None, description="分类名称", min_length=1, max_length=50)
    icon: Optional[str] = Field(None, description="分类图标（heroicons名称）")
    order: Optional[int] = Field(None, description="排序顺序")


class CreateWorkCategoryResponse(BaseModel):
    """创建作品分类响应"""
    category: AdminWorkCategoryListItem = Field(..., description="新创建的分类信息")


class UpdateWorkCategoryResponse(BaseModel):
    """更新作品分类响应"""
    category: AdminWorkCategoryListItem = Field(..., description="更新后的分类信息")


class MoveWorkCategoryResponse(BaseModel):
    """移动作品分类响应"""
    message: str = Field(..., description="操作结果消息")
    category: AdminWorkCategoryListItem = Field(..., description="移动后的分类信息")


# ==================== 课程文档模块 - 前台接口 ====================

class CourseCategoryNode(BaseModel):
    """目录节点（递归结构）"""
    id: str = Field(..., description="目录ID")
    name: str = Field(..., description="目录名称")
    parent_id: Optional[str] = Field(None, description="父目录ID")
    order: int = Field(..., description="排序顺序")
    children: List["CourseCategoryNode"] = Field(default_factory=list, description="子目录列表")


class CourseCategoryTreeResponse(BaseModel):
    """目录树响应"""
    categories: List[CourseCategoryNode] = Field(..., description="目录树")


class CourseDocumentListItem(BaseModel):
    """文档列表项"""
    id: str = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    summary: str = Field(..., description="文档摘要")
    order: int = Field(..., description="排序顺序")


class CourseDocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: List[CourseDocumentListItem] = Field(..., description="文档列表")


class CourseDocumentDetail(BaseModel):
    """文档详情"""
    id: str = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    summary: str = Field(..., description="文档摘要")
    content: str = Field(..., description="Markdown内容")
    category_id: str = Field(..., description="所属目录ID")
    order: int = Field(..., description="排序顺序")
    prev_doc_id: Optional[str] = Field(None, description="上一篇文档ID（同一目录下）")
    next_doc_id: Optional[str] = Field(None, description="下一篇文档ID（同一目录下）")
    created_at: datetime = Field(..., description="创建时间")


# ==================== 后台管理 - 文档目录管理模块 ====================

class AdminCourseCategoryListItem(BaseModel):
    """管理后台 - 目录列表项"""
    id: str = Field(..., description="目录ID")
    name: str = Field(..., description="目录名称")
    parent_id: Optional[str] = Field(None, description="父目录ID")
    parent_name: Optional[str] = Field(None, description="父目录名称")
    order: int = Field(..., description="排序顺序")
    document_count: int = Field(..., description="该目录下的文档数量（不包括子目录）")
    children_count: int = Field(..., description="子目录数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class AdminCourseCategoryListResponse(BaseModel):
    """管理后台 - 目录列表响应"""
    categories: List[AdminCourseCategoryListItem] = Field(..., description="目录列表")


class CreateCourseCategoryRequest(BaseModel):
    """创建目录请求"""
    name: str = Field(..., description="目录名称", min_length=1, max_length=100)
    parent_id: Optional[str] = Field(None, description="父目录ID（NULL表示根目录）")
    order: int = Field(0, description="排序顺序（默认0）")


class UpdateCourseCategoryRequest(BaseModel):
    """更新目录请求"""
    name: Optional[str] = Field(None, description="目录名称", min_length=1, max_length=100)
    parent_id: Optional[str] = Field(None, description="父目录ID（可以移动到其他目录下）")
    order: Optional[int] = Field(None, description="排序顺序", ge=0)


class CreateCourseCategoryResponse(BaseModel):
    """创建目录响应"""
    category: AdminCourseCategoryListItem = Field(..., description="新创建的目录信息")


class UpdateCourseCategoryResponse(BaseModel):
    """更新目录响应"""
    category: AdminCourseCategoryListItem = Field(..., description="更新后的目录信息")


class MoveCourseCategoryResponse(BaseModel):
    """移动目录响应"""
    message: str = Field(..., description="操作结果消息")
    category: AdminCourseCategoryListItem = Field(..., description="移动后的目录信息")


# ==================== 后台管理 - 文档管理模块 ====================

class AdminCourseDocumentListItem(BaseModel):
    """管理后台 - 文档列表项"""
    id: str = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    summary: str = Field(..., description="文档摘要")
    category_id: str = Field(..., description="所属目录ID")
    category_name: str = Field(..., description="所属目录名称")
    category_path: str = Field(..., description="所属目录完整路径（如: AI基础知识 > 什么是AI）")
    order: int = Field(..., description="排序顺序")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class AdminCourseDocumentListResponse(BaseModel):
    """管理后台 - 文档列表响应"""
    documents: List[AdminCourseDocumentListItem] = Field(..., description="文档列表")
    total: int = Field(..., description="文档总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


class CreateCourseDocumentRequest(BaseModel):
    """创建文档请求"""
    title: str = Field(..., description="文档标题", min_length=1, max_length=200)
    summary: str = Field(..., description="文档摘要", min_length=1, max_length=500)
    category_id: str = Field(..., description="所属目录ID")
    order: int = Field(0, description="排序顺序（默认0）")


class UpdateCourseDocumentRequest(BaseModel):
    """更新文档信息请求"""
    title: Optional[str] = Field(None, description="文档标题", min_length=1, max_length=200)
    summary: Optional[str] = Field(None, description="文档摘要", min_length=1, max_length=500)
    category_id: Optional[str] = Field(None, description="所属目录ID（可以移动到其他目录）")
    order: Optional[int] = Field(None, description="排序顺序", ge=0)


class CreateCourseDocumentResponse(BaseModel):
    """创建文档响应"""
    document: AdminCourseDocumentListItem = Field(..., description="新创建的文档信息")


class UpdateCourseDocumentResponse(BaseModel):
    """更新文档响应"""
    document: AdminCourseDocumentListItem = Field(..., description="更新后的文档信息")


class MoveCourseDocumentResponse(BaseModel):
    """移动文档响应"""
    message: str = Field(..., description="操作结果消息")
    document: AdminCourseDocumentListItem = Field(..., description="移动后的文档信息")


# ==================== 多模态生成模块 ====================

class MediaGenerateRequest(BaseModel):
    """多模态生成请求"""
    message: str = Field(..., description="用户提示词", min_length=1)
    session_id: Optional[str] = Field(None, description="会话ID（可选）。首次为空，后续传入")
    
    # 图片参数
    size: Optional[str] = Field("1024x1024", description="生成尺寸（图片/视频适用）")
    count: Optional[int] = Field(1, description="生成数量", ge=1, le=4)
    style: Optional[str] = Field("auto", description="生成风格")
    
    # 音频参数
    voice: Optional[str] = Field(None, description="音色ID（音频适用）")
    
    # 视频参数
    fps: Optional[int] = Field(None, description="视频帧率（30或60）")
    quality: Optional[str] = Field(None, description="视频质量（quality或speed）")
    with_audio: Optional[bool] = Field(False, description="是否生成AI音效（视频适用）")


class MediaGenerateResponse(BaseModel):
    """多模态生成响应（立即返回）"""
    session_id: str = Field(..., description="会话ID")
    message_id: str = Field(..., description="消息ID")
    task_id: str = Field(..., description="生成任务ID，用于轮询状态")
    status: Literal["pending", "processing", "completed"] = Field("pending", description="任务状态（同步模式可能直接返回completed）")
    
    # 同步模式下直接返回的字段
    media_urls: Optional[List[str]] = Field(None, description="媒体URLs（同步模式）")
    content_type: Optional[Literal["image", "audio", "video"]] = Field(None, description="内容类型（同步模式）")


class TaskStatusResponse(BaseModel):
    """任务状态查询响应"""
    task_id: str = Field(..., description="任务ID")
    status: Literal["pending", "processing", "completed", "failed"] = Field(..., description="任务状态")
    progress: Optional[int] = Field(None, description="进度百分比（0-100）", ge=0, le=100)
    
    # 完成时返回
    content_type: Optional[Literal["image", "audio", "video"]] = Field(None, description="内容类型（完成时）")
    media_urls: Optional[List[str]] = Field(None, description="媒体文件URL列表（完成时）")
    metadata: Optional[dict] = Field(None, description="额外元数据（完成时）")
    
    # 失败时返回
    error_message: Optional[str] = Field(None, description="错误信息（失败时）")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "task_id": "task_123",
                    "status": "processing",
                    "progress": 50
                },
                {
                    "task_id": "task_123",
                    "status": "completed",
                    "content_type": "image",
                    "media_urls": ["https://example.com/image1.png", "https://example.com/image2.png"],
                    "metadata": {"size": "1024x1024", "count": 2}
                },
                {
                    "task_id": "task_123",
                    "status": "failed",
                    "error_message": "生成失败：内容违规"
                }
            ]
        }
    )


# ==================== 导航模块管理模型 ====================

class AdminNavigationModuleListItem(BaseModel):
    """管理后台 - 导航模块列表项"""
    id: str = Field(..., description="模块ID")
    name: str = Field(..., description="模块名称")
    type: Literal["ai_tools", "page"] = Field(..., description="模块类型")
    config_source: Optional[str] = Field(None, description="配置来源")
    page_path: Optional[str] = Field(None, description="页面路径")
    icon: Optional[str] = Field(None, description="图标")
    order: int = Field(..., description="排序顺序")


class AdminNavigationModuleListResponse(BaseModel):
    """管理后台 - 导航模块列表响应"""
    modules: List[AdminNavigationModuleListItem] = Field(..., description="导航模块列表")


class CreateNavigationModuleRequest(BaseModel):
    """创建导航模块请求"""
    name: str = Field(..., description="模块名称", min_length=1, max_length=50)
    type: Literal["ai_tools", "page"] = Field(..., description="模块类型")
    config_source: Optional[str] = Field(None, description="配置来源（type=ai_tools时必填）")
    page_path: Optional[str] = Field(None, description="页面路径（type=page时必填）")
    icon: Optional[str] = Field(None, description="图标")
    order: int = Field(0, description="排序顺序")


class CreateNavigationModuleResponse(BaseModel):
    """创建导航模块响应"""
    module: AdminNavigationModuleListItem = Field(..., description="新创建的模块信息")


class UpdateNavigationModuleRequest(BaseModel):
    """更新导航模块请求"""
    name: Optional[str] = Field(None, description="模块名称", min_length=1, max_length=50)
    type: Optional[Literal["ai_tools", "page"]] = Field(None, description="模块类型")
    config_source: Optional[str] = Field(None, description="配置来源")
    page_path: Optional[str] = Field(None, description="页面路径")
    icon: Optional[str] = Field(None, description="图标")
    order: Optional[int] = Field(None, description="排序顺序")


class UpdateNavigationModuleResponse(BaseModel):
    """更新导航模块响应"""
    module: AdminNavigationModuleListItem = Field(..., description="更新后的模块信息")


class MoveNavigationModuleResponse(BaseModel):
    """移动导航模块响应"""
    message: str = Field(..., description="操作结果消息")
    module: AdminNavigationModuleListItem = Field(..., description="移动后的模块信息")


# ==================== 导航模块分类管理模型 ====================

class AdminNavigationModuleCategoryListItem(BaseModel):
    """导航模块分类列表项"""
    id: str = Field(..., description="分类ID")
    navigation_module_id: str = Field(..., description="所属导航模块ID")
    navigation_module_name: str = Field(..., description="导航模块名称")
    name: str = Field(..., description="分类名称")
    icon: Optional[str] = Field(None, description="图标")
    order: int = Field(..., description="排序")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class AdminNavigationModuleCategoryListResponse(BaseModel):
    """导航模块分类列表响应"""
    categories: List[AdminNavigationModuleCategoryListItem]


class CreateNavigationModuleCategoryRequest(BaseModel):
    """创建导航模块分类请求"""
    navigation_module_id: str = Field(..., description="所属导航模块ID")
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    icon: Optional[str] = Field(None, max_length=50, description="图标")
    order: int = Field(0, ge=0, description="排序")


class CreateNavigationModuleCategoryResponse(BaseModel):
    """创建导航模块分类响应"""
    id: str = Field(..., description="分类ID")
    message: str = Field(..., description="响应消息")


class UpdateNavigationModuleCategoryRequest(BaseModel):
    """更新导航模块分类请求"""
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    icon: Optional[str] = Field(None, max_length=50, description="图标")
    order: int = Field(..., ge=0, description="排序")


class UpdateNavigationModuleCategoryResponse(BaseModel):
    """更新导航模块分类响应"""
    id: str = Field(..., description="分类ID")
    message: str = Field(..., description="响应消息")


# ==================== AI工具分类管理模型 ====================

class AdminAIToolCategoryListItem(BaseModel):
    """管理后台 - AI工具分类列表项"""
    id: str = Field(..., description="分类ID")
    navigation_module_id: str = Field(..., description="所属导航模块ID")
    navigation_module_name: str = Field(..., description="导航模块名称")
    name: str = Field(..., description="分类名称")
    icon: Optional[str] = Field(None, description="图标")
    order: int = Field(..., description="排序顺序")


class AdminAIToolCategoryListResponse(BaseModel):
    """管理后台 - AI工具分类列表响应"""
    categories: List[AdminAIToolCategoryListItem] = Field(..., description="分类列表")


class CreateAIToolCategoryRequest(BaseModel):
    """创建AI工具分类请求"""
    navigation_module_id: str = Field(..., description="所属导航模块ID")
    name: str = Field(..., description="分类名称", min_length=1, max_length=50)
    icon: Optional[str] = Field(None, description="图标")
    order: int = Field(0, description="排序顺序")


class CreateAIToolCategoryResponse(BaseModel):
    """创建AI工具分类响应"""
    category: AdminAIToolCategoryListItem = Field(..., description="新创建的分类信息")


class UpdateAIToolCategoryRequest(BaseModel):
    """更新AI工具分类请求"""
    name: Optional[str] = Field(None, description="分类名称", min_length=1, max_length=50)
    icon: Optional[str] = Field(None, description="图标")
    order: Optional[int] = Field(None, description="排序顺序")


class UpdateAIToolCategoryResponse(BaseModel):
    """更新AI工具分类响应"""
    category: AdminAIToolCategoryListItem = Field(..., description="更新后的分类信息")


class MoveAIToolCategoryResponse(BaseModel):
    """移动AI工具分类响应"""
    message: str = Field(..., description="操作结果消息")
    category: AdminAIToolCategoryListItem = Field(..., description="移动后的分类信息")


# ==================== AI工具管理模型 ====================

class AdminAIToolListItem(BaseModel):
    """管理后台 - AI工具列表项"""
    id: str = Field(..., description="工具ID")
    tool_id: str = Field(..., description="工具唯一标识")
    navigation_module_id: str = Field(..., description="所属导航模块ID")
    navigation_module_name: str = Field(..., description="导航模块名称")
    category_id: Optional[str] = Field(None, description="所属分类ID")
    category_name: Optional[str] = Field(None, description="分类名称")
    name: str = Field(..., description="工具名称")
    description: Optional[str] = Field(None, description="工具描述")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    icon: Optional[str] = Field(None, description="图标")
    type: Literal["normal", "media"] = Field(..., description="工具类型")
    content_type: Optional[str] = Field(None, description="内容类型")
    media_type: Optional[str] = Field(None, description="媒体类型")
    model: Optional[str] = Field(None, description="使用的模型")
    welcome_message: Optional[str] = Field(None, description="欢迎消息")
    visible: bool = Field(..., description="是否可见")
    order: int = Field(..., description="排序顺序")


class AdminAIToolListResponse(BaseModel):
    """管理后台 - AI工具列表响应"""
    tools: List[AdminAIToolListItem] = Field(..., description="工具列表")
    total: int = Field(..., description="工具总数")


class CreateAIToolRequest(BaseModel):
    """创建AI工具请求"""
    tool_id: str = Field(..., description="工具唯一标识", min_length=1, max_length=50)
    navigation_module_id: str = Field(..., description="所属导航模块ID")
    category_id: str = Field(..., description="分类ID（必选）")
    name: str = Field(..., description="工具名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="工具描述")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    icon: Optional[str] = Field(None, description="图标")
    type: Literal["normal", "media"] = Field("normal", description="工具类型")
    content_type: Optional[Literal["text", "multimodal"]] = Field(None, description="内容类型")
    media_type: Optional[Literal["image", "audio", "video"]] = Field(None, description="媒体类型")
    model: Optional[str] = Field(None, description="使用的模型")
    welcome_message: Optional[str] = Field(None, description="欢迎消息")
    visible: bool = Field(True, description="是否可见")
    order: int = Field(0, description="排序顺序")


class CreateAIToolResponse(BaseModel):
    """创建AI工具响应"""
    tool: AdminAIToolListItem = Field(..., description="新创建的工具信息")


class UpdateAIToolRequest(BaseModel):
    """更新AI工具请求"""
    tool_id: Optional[str] = Field(None, description="工具唯一标识", min_length=1, max_length=50)
    navigation_module_id: Optional[str] = Field(None, description="所属导航模块ID")
    category_id: Optional[str] = Field(None, description="分类ID（必选）")
    name: Optional[str] = Field(None, description="工具名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="工具描述")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    icon: Optional[str] = Field(None, description="图标")
    type: Optional[Literal["normal", "media"]] = Field(None, description="工具类型")
    content_type: Optional[Literal["text", "multimodal"]] = Field(None, description="内容类型")
    media_type: Optional[Literal["image", "audio", "video"]] = Field(None, description="媒体类型")
    model: Optional[str] = Field(None, description="使用的模型")
    welcome_message: Optional[str] = Field(None, description="欢迎消息")
    visible: Optional[bool] = Field(None, description="是否可见")
    order: Optional[int] = Field(None, description="排序顺序")


class UpdateAIToolResponse(BaseModel):
    """更新AI工具响应"""
    tool: AdminAIToolListItem = Field(..., description="更新后的工具信息")


class MoveAIToolResponse(BaseModel):
    """移动AI工具响应"""
    message: str = Field(..., description="操作结果消息")
    tool: AdminAIToolListItem = Field(..., description="移动后的工具信息")


class ToggleAIToolVisibilityResponse(BaseModel):
    """切换AI工具可见性响应"""
    message: str = Field(..., description="操作结果消息")
    tool: AdminAIToolListItem = Field(..., description="更新后的工具信息")


# ==================== 模型供应商配置模块 ====================

class ModelProviderListItem(BaseModel):
    """模型供应商列表项"""
    id: str = Field(..., description="供应商ID")
    provider_code: str = Field(..., description="供应商代码（如：openai, deepseek）")
    provider_name: str = Field(..., description="供应商名称")
    base_url: Optional[str] = Field(None, description="API地址")
    is_enabled: bool = Field(..., description="是否启用")
    is_default: bool = Field(..., description="是否为默认供应商")
    order: int = Field(..., description="排序顺序")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ModelProviderListResponse(BaseModel):
    """模型供应商列表响应"""
    providers: List[ModelProviderListItem] = Field(..., description="供应商列表")


class CreateModelProviderRequest(BaseModel):
    """创建模型供应商请求"""
    provider_code: str = Field(..., description="供应商代码（如：openai, deepseek）", min_length=1, max_length=50)
    provider_name: str = Field(..., description="供应商名称", min_length=1, max_length=100)
    api_key: str = Field(..., description="API密钥（明文，将被加密存储）", min_length=1)
    base_url: Optional[str] = Field(None, description="API地址")
    is_enabled: bool = Field(True, description="是否启用（默认true）")
    is_default: bool = Field(False, description="是否为默认供应商（默认false）")
    order: int = Field(0, description="排序顺序（默认0）")


class CreateModelProviderResponse(BaseModel):
    """创建模型供应商响应"""
    provider: ModelProviderListItem = Field(..., description="新创建的供应商信息")


class UpdateModelProviderRequest(BaseModel):
    """更新模型供应商请求"""
    provider_name: Optional[str] = Field(None, description="供应商名称", min_length=1, max_length=100)
    api_key: Optional[str] = Field(None, description="API密钥（明文，将被加密存储）")
    base_url: Optional[str] = Field(None, description="API地址")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    is_default: Optional[bool] = Field(None, description="是否为默认供应商")
    order: Optional[int] = Field(None, description="排序顺序")


class UpdateModelProviderResponse(BaseModel):
    """更新模型供应商响应"""
    provider: ModelProviderListItem = Field(..., description="更新后的供应商信息")


class ModelConfigListItem(BaseModel):
    """模型配置列表项"""
    id: str = Field(..., description="配置ID")
    provider_id: str = Field(..., description="供应商ID")
    provider_code: str = Field(..., description="供应商代码")
    provider_name: str = Field(..., description="供应商名称")
    model_code: str = Field(..., description="模型代码")
    model_name: str = Field(..., description="模型名称")
    capabilities: List[str] = Field(..., description="支持的能力列表")
    is_enabled: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ModelConfigListResponse(BaseModel):
    """模型配置列表响应"""
    models: List[ModelConfigListItem] = Field(..., description="模型配置列表")


class CreateModelConfigRequest(BaseModel):
    """创建模型配置请求"""
    provider_id: str = Field(..., description="供应商ID")
    model_code: str = Field(..., description="模型代码（如：gpt-4, deepseek-chat）", min_length=1, max_length=50)
    model_name: str = Field(..., description="模型名称", min_length=1, max_length=100)
    capabilities: str = Field(..., description="支持的能力（逗号分隔，如：chat,image）", min_length=1)
    is_enabled: bool = Field(True, description="是否启用（默认true）")


class CreateModelConfigResponse(BaseModel):
    """创建模型配置响应"""
    model: ModelConfigListItem = Field(..., description="新创建的模型配置信息")


class UpdateModelConfigRequest(BaseModel):
    """更新模型配置请求"""
    model_code: Optional[str] = Field(None, description="模型代码", min_length=1, max_length=50)
    model_name: Optional[str] = Field(None, description="模型名称", min_length=1, max_length=100)
    capabilities: Optional[str] = Field(None, description="支持的能力（逗号分隔）")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class UpdateModelConfigResponse(BaseModel):
    """更新模型配置响应"""
    model: ModelConfigListItem = Field(..., description="更新后的模型配置信息")


class AvailableModelResponse(BaseModel):
    """可用模型响应"""
    models: List[ModelConfigListItem] = Field(..., description="可用模型列表（仅返回已启用的）")


# ==================== 企业积分系统模型 ====================

class EnterpriseInfo(BaseModel):
    """企业信息"""
    id: str
    name: str
    code: str
    status: EnterpriseStatus
    balance_gratis: int
    balance_paid: int
    debt_points: int
    total_points: int
    user_count: int = 0
    created_at: datetime


class CreateEnterpriseRequest(BaseModel):
    """创建企业请求"""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    initial_gratis: int = Field(0, ge=0)


class UpdateEnterpriseRequest(BaseModel):
    """更新企业请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[EnterpriseStatus] = None


class EnterpriseListResponse(BaseModel):
    """企业列表响应"""
    enterprises: List[EnterpriseInfo]
    total: int
    page: int
    page_size: int


class PointBalanceResponse(BaseModel):
    """积分余额响应"""
    balance_gratis: int
    balance_paid: int
    debt_points: int
    total_points: int


class AddPointsRequest(BaseModel):
    """增加积分请求"""
    amount: int = Field(..., gt=0)
    source_type: PointSourceType
    remark: Optional[str] = None


class TransactionItem(BaseModel):
    """交易记录项"""
    id: str
    type: PointTransactionType
    source_type: PointSourceType
    amount: int
    balance_before: int
    balance_after: int
    remark: Optional[str]
    created_at: datetime


class TransactionListResponse(BaseModel):
    """交易记录列表响应"""
    transactions: List[TransactionItem]
    total: int
    page: int


class ConsumptionItem(BaseModel):
    """消费记录项"""
    id: str
    user_id: str
    username: Optional[str] = None
    nickname: Optional[str] = None
    model_provider: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    gratis_points_used: int
    paid_points_used: int
    total_points: int
    points: int  # 前端使用的字段别名
    created_at: datetime


class ConsumptionStats(BaseModel):
    """消费统计数据"""
    today_consumed: int
    month_consumed: int
    total_consumed: int


class ConsumptionListResponse(BaseModel):
    """消费记录列表响应"""
    items: List[ConsumptionItem]
    total: int
    page: int
    stats: Optional[ConsumptionStats] = None


class ModelPointRateItem(BaseModel):
    """模型汇率项"""
    id: str
    model_config_id: str
    provider_code: str
    model_code: str
    model_name: str
    tokens_per_point: int
    separate_io: bool
    tokens_per_point_input: Optional[int]
    tokens_per_point_output: Optional[int]
    is_enabled: bool


class CreatePointRateRequest(BaseModel):
    """创建汇率配置请求"""
    model_config_id: str
    tokens_per_point: int = Field(1000, gt=0)
    separate_io: bool = False
    tokens_per_point_input: Optional[int] = None
    tokens_per_point_output: Optional[int] = None


class UpdatePointRateRequest(BaseModel):
    """更新汇率配置请求"""
    tokens_per_point: Optional[int] = Field(None, gt=0)
    separate_io: Optional[bool] = None
    tokens_per_point_input: Optional[int] = None
    tokens_per_point_output: Optional[int] = None
    is_enabled: Optional[bool] = None


# ==================== 模型汇率批量设置 ====================

class RateConfigInfo(BaseModel):
    """汇率配置信息"""
    id: str
    tokens_per_point_input: int | None
    tokens_per_point_output: int | None
    is_enabled: bool


class ModelRateStatusItem(BaseModel):
    """模型汇率状态项"""
    model_config_id: str
    provider_id: str
    provider_code: str
    provider_name: str
    model_code: str
    model_name: str
    is_model_enabled: bool
    rate_config: RateConfigInfo | None


class ModelRatesStatusResponse(BaseModel):
    """模型汇率状态响应"""
    models: List[ModelRateStatusItem]


class RateUpdateItem(BaseModel):
    """汇率更新项"""
    model_config_id: str
    tokens_per_point_input: int
    tokens_per_point_output: int
    is_enabled: bool = True


class BatchUpdateRateRequest(BaseModel):
    """批量更新汇率请求"""
    updates: List[RateUpdateItem]


class BatchUpdateRateResponse(BaseModel):
    """批量更新汇率响应"""
    updated: int

