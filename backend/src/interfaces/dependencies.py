# -*- coding: utf-8 -*-
"""Interfaces layer dependency injection

This module provides dependency functions for FastAPI routes in the interfaces layer.
It bridges the new DDD structure with existing services.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import HTTPException, status, Depends
from src.routers.dependencies import (
    get_tool_service,
    get_ai_service,
    get_ai_service_with_db,
    get_session_service,
    get_artifact_parser,
    get_title_generator,
    get_auth_service,
    get_user_service,
    get_config_loader,
    get_conversion_service,
    get_common_tool_service,
    get_work_service,
    get_course_service,
    get_model_service,
)
from src.interfaces.auth import get_current_user
from src.models import UserInfo
from typing import Annotated

# 数据库依赖
from src.database import get_db

# Export all dependencies for use in interfaces layer routes
__all__ = [
    "get_tool_service",
    "get_ai_service",
    "get_ai_service_with_db",
    "get_session_service",
    "get_artifact_parser",
    "get_title_generator",
    "get_auth_service",
    "get_user_service",
    "get_config_loader",
    "get_conversion_service",
    "get_common_tool_service",
    "get_work_service",
    "get_course_service",
    "get_model_service",
    "get_current_user",
    "require_admin",  # 新增
    "get_config_service",  # 新增
    "get_model_provider_service",  # 新增
]


async def require_admin(current_user: Annotated[UserInfo, Depends(get_current_user)]) -> UserInfo:
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


def get_config_service():
    """获取配置服务实例（数据库版本）"""
    from src.services.config_service import ConfigService
    db = next(get_db())
    try:
        yield ConfigService(db)
    finally:
        db.close()


def get_model_provider_service():
    """获取模型供应商配置服务实例"""
    from src.services.model_provider_service import ModelProviderService
    db = next(get_db())
    try:
        yield ModelProviderService(db)
    finally:
        db.close()


def get_ai_service_with_db_dependency(db: Session = Depends(get_db)):
    """
    获取带数据库支持的 AI 服务（依赖注入函数）

    Args:
        db: 数据库会话

    Yields:
        AIService 实例
    """
    from src.services.ai_service import AIService
    try:
        yield AIService(db=db)
    finally:
        pass  # 数据库会话由 FastAPI 管理
