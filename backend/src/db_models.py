"""SQLAlchemy ORM 数据模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Enum, ForeignKey, Index, Integer, Boolean
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from .database import Base
import enum


class UserModel(Base):
    """用户数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "users"
    
    user_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    nickname = Column(String(50), nullable=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(11), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(String(500), nullable=True)
    is_admin = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # 关系
    sessions = relationship("SessionModel", back_populates="user", cascade="all, delete-orphan")


class MessageRole(enum.Enum):
    """消息角色枚举"""
    user = "user"
    assistant = "assistant"


class SessionModel(Base):
    """会话数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "sessions"

    session_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(CHAR(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    tool_id = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, index=True)

    # 模型选择相关字段（新增）
    model_provider = Column(String(50), nullable=True, comment="AI服务提供商（deepseek/openai/kimi/glm）")
    model_name = Column(String(100), nullable=True, comment="使用的模型名称（如deepseek-chat/gpt-4）")

    # Token统计相关字段（新增）
    total_tokens = Column(Integer, nullable=False, default=0, comment="会话总token消耗")
    total_prompt_tokens = Column(Integer, nullable=False, default=0, comment="会话总prompt token消耗")
    total_completion_tokens = Column(Integer, nullable=False, default=0, comment="会话总completion token消耗")

    # 关系
    user = relationship("UserModel", back_populates="sessions")
    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan", order_by="MessageModel.created_at")

    # 联合索引
    __table_args__ = (
        Index("idx_user_tool", "user_id", "tool_id"),
    )


class MessageModel(Base):
    """消息数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "messages"

    message_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(CHAR(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)

    # 多模态支持字段
    media_content = Column(Text, nullable=True, comment="多模态内容JSON字符串")

    # 模型和Token相关字段（新增）
    model_provider = Column(String(50), nullable=True, comment="AI服务提供商")
    model_name = Column(String(100), nullable=True, comment="使用的模型名称")
    prompt_tokens = Column(Integer, nullable=True, comment="用户消息的token消耗")
    completion_tokens = Column(Integer, nullable=True, comment="AI回复的token消耗")
    total_tokens = Column(Integer, nullable=True, comment="本条消息的总token消耗")

    # 关系
    session = relationship("SessionModel", back_populates="messages")
    artifacts = relationship("ArtifactModel", back_populates="message", cascade="all, delete-orphan")


class ArtifactModel(Base):
    """成果物数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "artifacts"
    
    artifact_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(CHAR(36), ForeignKey("messages.message_id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # 关系
    message = relationship("MessageModel", back_populates="artifacts")


class CommonToolType(enum.Enum):
    """常用工具类型枚举"""
    built_in = "built_in"
    html = "html"


class ToolCategoryModel(Base):
    """工具分类数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "tool_categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, unique=True)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    tools = relationship("CommonToolModel", back_populates="category", cascade="all, delete-orphan")


class CommonToolModel(Base):
    """常用工具数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "common_tools"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(String(200), nullable=False)
    category_id = Column(String(36), ForeignKey("tool_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    type = Column(Enum(CommonToolType), nullable=False)
    icon = Column(String(50), nullable=True)
    html_path = Column(String(255), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    visible = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    category = relationship("ToolCategoryModel", back_populates="tools")
    
    # 联合索引（按分类和排序查询）
    __table_args__ = (
        Index("idx_common_tool_category_order", "category_id", "order"),
    )


class WorkCategoryModel(Base):
    """作品分类数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "work_categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, unique=True)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    works = relationship("WorkModel", back_populates="category", cascade="all, delete-orphan")


class WorkModel(Base):
    """作品数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "works"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(String(200), nullable=False)
    category_id = Column(String(36), ForeignKey("work_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    icon = Column(String(50), nullable=True)
    html_path = Column(String(255), nullable=False)
    order = Column(Integer, nullable=False, default=0)
    visible = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    category = relationship("WorkCategoryModel", back_populates="works")
    
    # 联合索引（按分类和排序查询）
    __table_args__ = (
        Index("idx_work_category_order", "category_id", "order"),
    )


class CourseCategoryModel(Base):
    """文档目录数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "course_categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    parent_id = Column(String(36), ForeignKey("course_categories.id", ondelete="RESTRICT"), nullable=True, index=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    children = relationship("CourseCategoryModel", back_populates="parent", remote_side="CourseCategoryModel.id")
    parent = relationship("CourseCategoryModel", back_populates="children", remote_side="CourseCategoryModel.parent_id")
    documents = relationship("CourseDocumentModel", back_populates="category", cascade="all, delete-orphan")
    
    # 联合索引（按父目录和排序查询）
    __table_args__ = (
        Index("idx_course_category_parent_order", "parent_id", "order"),
    )


class CourseDocumentModel(Base):
    """文档数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "course_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    summary = Column(String(500), nullable=False)
    file_path = Column(String(255), nullable=False)
    category_id = Column(String(36), ForeignKey("course_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    category = relationship("CourseCategoryModel", back_populates="documents")

    # 联合索引（按分类和排序查询）
    __table_args__ = (
        Index("idx_course_document_category_order", "category_id", "order"),
    )


class NavigationModuleType(enum.Enum):
    """导航模块类型枚举"""
    toolset = "toolset"
    page = "page"


class AIToolType(enum.Enum):
    """AI工具类型枚举"""
    normal = "normal"
    media = "media"


class NavigationModuleModel(Base):
    """导航模块数据库模型"""
    __tablename__ = "navigation_modules"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False)
    type = Column(Enum(NavigationModuleType), nullable=False)
    config_source = Column(String(100), nullable=True)
    page_path = Column(String(100), nullable=True)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 联合索引
    __table_args__ = (
        Index("idx_navigation_module_order", "order"),
    )


class ToolsetModel(Base):
    """工具集数据库模型"""
    __tablename__ = "toolsets"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    toolset_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    categories = relationship("AIToolCategoryModel", back_populates="toolset", cascade="all, delete-orphan")
    tools = relationship("AIToolModel", back_populates="toolset", cascade="all, delete-orphan")


class AIToolCategoryModel(Base):
    """AI工具分类数据库模型"""
    __tablename__ = "ai_tool_categories"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    toolset_id = Column(CHAR(36), ForeignKey("toolsets.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    toolset = relationship("ToolsetModel", back_populates="categories")
    tools = relationship("AIToolModel", back_populates="category", cascade="all, delete-orphan")


class AIToolModel(Base):
    """AI工具数据库模型"""
    __tablename__ = "ai_tools"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String(50), unique=True, nullable=False, index=True)
    toolset_id = Column(CHAR(36), ForeignKey("toolsets.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(CHAR(36), ForeignKey("ai_tool_categories.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    type = Column(Enum(AIToolType), nullable=False, default=AIToolType.normal)
    content_type = Column(String(20), nullable=True)
    media_type = Column(String(20), nullable=True)
    model = Column(String(100), nullable=True)
    welcome_message = Column(Text, nullable=True)
    visible = Column(Boolean, nullable=False, default=True, index=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    toolset = relationship("ToolsetModel", back_populates="tools")
    category = relationship("AIToolCategoryModel", back_populates="tools")

    # 联合索引
    __table_args__ = (
        Index("idx_ai_tool_toolset_order", "toolset_id", "order"),
        Index("idx_ai_tool_category_order", "category_id", "order"),
    )


class TokenUsageLogModel(Base):
    """Token使用日志数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "token_usage_logs"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(CHAR(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(CHAR(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(CHAR(36), ForeignKey("messages.message_id", ondelete="CASCADE"), nullable=False, index=True)

    # 模型信息
    model_provider = Column(String(50), nullable=False, comment="AI服务提供商")
    model_name = Column(String(100), nullable=False, comment="模型名称")

    # Token消耗
    prompt_tokens = Column(Integer, nullable=False, comment="Prompt token数")
    completion_tokens = Column(Integer, nullable=False, comment="Completion token数")
    total_tokens = Column(Integer, nullable=False, comment="总token数")

    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)

    # 联合索引
    __table_args__ = (
        Index("idx_token_user_date", "user_id", "created_at"),
        Index("idx_token_session", "session_id"),
        Index("idx_token_provider", "model_provider"),
    )


class ModelProviderModel(Base):
    """模型供应商配置数据库模型"""
    __tablename__ = "model_providers"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_code = Column(String(50), unique=True, nullable=False, index=True, comment='供应商代码')
    provider_name = Column(String(100), nullable=False, comment='供应商名称')
    api_key_encrypted = Column(Text, nullable=False, comment='加密后的API密钥')
    base_url = Column(String(500), nullable=True, comment='API地址')
    is_enabled = Column(Boolean, nullable=False, default=True, comment='是否启用')
    is_default = Column(Boolean, nullable=False, default=False, comment='是否为默认供应商')
    order = Column(Integer, nullable=False, default=0, index=True, comment='排序')
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    models = relationship("ModelConfigModel", back_populates="provider", cascade="all, delete-orphan")


class ModelConfigModel(Base):
    """模型配置数据库模型"""
    __tablename__ = "model_configs"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(CHAR(36), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    model_code = Column(String(50), nullable=False, comment='模型代码')
    model_name = Column(String(100), nullable=False, comment='模型名称')
    capabilities = Column(String(50), nullable=False, comment='支持的能力，逗号分隔')
    is_enabled = Column(Boolean, nullable=False, default=True, comment='是否启用')
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    provider = relationship("ModelProviderModel", back_populates="models")

    # 联合唯一约束
    __table_args__ = (
        Index("uk_provider_model", "provider_id", "model_code", unique=True),
    )

