"""SQLAlchemy ORM 数据模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Enum, ForeignKey, Index
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

