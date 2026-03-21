# -*- coding: utf-8 -*-
"""导航模块路由"""
from fastapi import APIRouter, Depends
from src.models import NavigationResponse
from src.interfaces.dependencies import get_config_service
from src.services.config_service import ConfigService

router = APIRouter(prefix="/api/v1", tags=["导航"])


@router.get("/navigation", response_model=NavigationResponse)
async def get_navigation(
    config_service: ConfigService = Depends(get_config_service)
):
    """获取导航模块配置（公开接口，无需认证）"""
    modules = config_service.get_navigation_modules()
    return NavigationResponse(modules=modules)