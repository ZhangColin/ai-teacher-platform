# -*- coding: utf-8 -*-
"""导航模块路由"""
from fastapi import APIRouter, Depends
from src.models import NavigationResponse
from src.interfaces.dependencies import get_config_service
from src.services.config_service import ConfigService
from src.interfaces.auth import get_current_user

router = APIRouter()


@router.get("/navigation", response_model=NavigationResponse, tags=["导航"])
async def get_navigation(
    current_user = Depends(get_current_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """获取导航模块配置"""
    modules = config_service.get_navigation_modules()
    return NavigationResponse(modules=modules)