"""SQLAlchemy ORM 数据模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.mysql import CHAR
from .database import Base


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

