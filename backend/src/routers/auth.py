# -*- coding: utf-8 -*-
"""认证相关路由

包含用户登录、获取当前用户信息等接口。
"""
import re
import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.models import LoginRequest, LoginResponse, UserInfo, UserInfoResponse

from .dependencies import get_auth_service, get_user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

# 全局共享的 security 实例（在其他模块中导入使用）
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> UserInfo:
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
    auth_service = get_auth_service()
    user_id = auth_service.get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 根据用户ID查询用户
    user_service = get_user_service()
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


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """用户登录（支持用户名、邮箱或手机号）"""
    user_service = get_user_service()
    auth_service = get_auth_service()

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


@router.get("/me", response_model=UserInfoResponse)
async def get_me(current_user: Annotated[UserInfo, Depends(get_current_user)]):
    """获取当前登录用户信息"""
    return UserInfoResponse(user=current_user)
