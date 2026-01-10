"""Domain models for Agent platform."""
import uuid
import bcrypt
from datetime import datetime
from typing import List, Optional, Literal, Union
from pydantic import BaseModel, Field, ConfigDict


class NavigationModule(BaseModel):
    """导航模块配置（用于顶部导航栏）"""
    name: str = Field(..., description="模块显示名称")
    type: Literal["toolset", "page"] = Field(..., description="模块类型：toolset=工具集模块，page=独立页面")
    config_source: Optional[str] = Field(None, description="配置来源（type=toolset时使用，工具集配置目录路径，如：tools/ai_tools）")
    page_path: Optional[str] = Field(None, description="页面路径（type=page时使用，前端路由路径，如：/common-tools）")
    icon: Optional[str] = Field(None, description="图标标识（可选）")
    order: int = Field(999, description="排序顺序（数字越小越靠前，默认999）")
    
    def validate(self) -> bool:
        """验证导航模块配置是否有效"""
        if not self.name or not self.type:
            return False
        # toolset 类型必须有 config_source
        if self.type == "toolset" and not self.config_source:
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
    type: Literal["normal", "placeholder"] = Field("normal", description="工具类型")
    welcome_message: str = Field(..., description="欢迎语（配置化展示）")
    order: int = Field(999, description="排序顺序（数字越小越靠前，默认999）")
    toolset_id: str = Field("ai_tools", description="所属工具集ID（默认ai_tools，保持向后兼容）")
    system_prompt_file: Optional[str] = Field(None, description="系统提示词文件路径（相对于工具集配置目录），如果指定则从文件加载system_prompt")
    
    def validate(self) -> bool:
        """验证工具配置是否完整有效"""
        if not self.tool_id or not self.name:
            return False
        if not self.category or not self.welcome_message:
            return False
        # system_prompt 和 system_prompt_file 至少有一个
        if not self.system_prompt and not self.system_prompt_file:
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
    toolset_id: str = Field(..., description="所属工具集ID")


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

