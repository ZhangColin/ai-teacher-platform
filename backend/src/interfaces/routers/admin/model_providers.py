# -*- coding: utf-8 -*-
"""模型供应商配置管理 API 路由"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.interfaces.dependencies import get_db, require_admin
from src.services.model_provider_service import ModelProviderService
from src.models import (
    ModelProviderListResponse,
    ModelProviderListItem,
    CreateModelProviderRequest,
    CreateModelProviderResponse,
    UpdateModelProviderRequest,
    UpdateModelProviderResponse,
    ModelConfigListResponse,
    ModelConfigListItem,
    CreateModelConfigRequest,
    CreateModelConfigResponse,
    UpdateModelConfigRequest,
    UpdateModelConfigResponse,
    AvailableModelResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/model-providers", tags=["模型供应商配置"])


def get_model_provider_service(db: Session = Depends(get_db)) -> ModelProviderService:
    """获取模型供应商服务实例"""
    return ModelProviderService(db)


# ==================== 内置定义 ====================

@router.get("/builtin-providers")
async def get_builtin_providers():
    """
    获取内置供应商列表

    系统支持的供应商类型，管理员可以选择其中一种进行配置
    """
    from src.services.builtin_models import get_builtin_providers
    providers = get_builtin_providers()
    return {"providers": providers}


@router.get("/builtin-models")
async def get_builtin_models(provider_code: Optional[str] = None):
    """
    获取内置模型列表

    Args:
        provider_code: 可选，按供应商筛选

    Returns:
        模型列表
    """
    from src.services.builtin_models import get_builtin_models
    models = get_builtin_models(provider_code)
    return {"models": models}


# ==================== 模型供应商管理 ====================

@router.get("", response_model=ModelProviderListResponse)
async def list_providers(
    include_disabled: bool = False,
    service: ModelProviderService = Depends(get_model_provider_service),
    _admin: None = Depends(require_admin)
):
    """
    获取所有模型供应商

    Args:
        include_disabled: 是否包含已禁用的供应商（默认false）

    Returns:
        供应商列表
    """
    providers = service.get_all_providers(include_disabled=include_disabled)
    return ModelProviderListResponse(providers=providers)


@router.get("/{provider_id}", response_model=ModelProviderListItem)
async def get_provider(
    provider_id: str,
    service: ModelProviderService = Depends(get_model_provider_service),
    _admin: None = Depends(require_admin)
):
    """
    根据ID获取供应商

    Args:
        provider_id: 供应商ID

    Returns:
        供应商信息

    Raises:
        HTTPException: 供应商不存在
    """
    provider = service.get_provider_by_id(provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"供应商 ID '{provider_id}' 不存在"
        )
    return provider


@router.post("", response_model=CreateModelProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    request: CreateModelProviderRequest,
    service: ModelProviderService = Depends(get_model_provider_service),
    _admin: None = Depends(require_admin)
):
    """
    创建模型供应商

    Args:
        request: 创建请求

    Returns:
        新创建的供应商信息

    Raises:
        HTTPException: 供应商代码已存在
    """
    try:
        provider = service.create_provider(request)
        return CreateModelProviderResponse(provider=provider)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{provider_id}", response_model=UpdateModelProviderResponse)
async def update_provider(
    provider_id: str,
    request: UpdateModelProviderRequest,
    service: ModelProviderService = Depends(get_model_provider_service),
    _admin: None = Depends(require_admin)
):
    """
    更新模型供应商

    Args:
        provider_id: 供应商ID
        request: 更新请求

    Returns:
        更新后的供应商信息

    Raises:
        HTTPException: 供应商不存在
    """
    try:
        provider = service.update_provider(provider_id, request)
        return UpdateModelProviderResponse(provider=provider)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: str,
    service: ModelProviderService = Depends(get_model_provider_service),
    _admin: None = Depends(require_admin)
):
    """
    删除模型供应商

    注意：删除供应商会级联删除其下的所有模型配置

    Args:
        provider_id: 供应商ID

    Raises:
        HTTPException: 供应商不存在
    """
    try:
        service.delete_provider(provider_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== 模型配置管理 ====================

@router.get("/{provider_id}/models", response_model=ModelConfigListResponse)
async def list_models(
    provider_id: str,
    include_disabled: bool = False,
    service: ModelProviderService = Depends(get_model_provider_service),
    _admin: None = Depends(require_admin)
):
    """
    获取指定供应商的所有模型配置

    Args:
        provider_id: 供应商ID
        include_disabled: 是否包含已禁用的模型（默认false）

    Returns:
        模型配置列表
    """
    models = service.get_all_models(provider_id=provider_id, include_disabled=include_disabled)
    return ModelConfigListResponse(models=models)


@router.get("/models/all", response_model=ModelConfigListResponse)
async def list_all_models(
    provider_id: Optional[str] = None,
    include_disabled: bool = False,
    service: ModelProviderService = Depends(get_model_provider_service),
    _admin: None = Depends(require_admin)
):
    """
    获取所有模型配置（可按供应商过滤）

    Args:
        provider_id: 可选的供应商ID过滤
        include_disabled: 是否包含已禁用的模型（默认false）

    Returns:
        模型配置列表
    """
    models = service.get_all_models(provider_id=provider_id, include_disabled=include_disabled)
    return ModelConfigListResponse(models=models)


@router.get("/models/{model_id}", response_model=ModelConfigListItem)
async def get_model(
    model_id: str,
    service: ModelProviderService = Depends(get_model_provider_service),
    _admin: None = Depends(require_admin)
):
    """
    根据ID获取模型配置

    Args:
        model_id: 模型配置ID

    Returns:
        模型配置信息

    Raises:
        HTTPException: 模型配置不存在
    """
    model = service.get_model_by_id(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型配置 ID '{model_id}' 不存在"
        )
    return model


@router.post("/models", response_model=CreateModelConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_model_config(
    request: CreateModelConfigRequest,
    service: ModelProviderService = Depends(get_model_provider_service),
    _admin: None = Depends(require_admin)
):
    """
    创建模型配置

    Args:
        request: 创建请求

    Returns:
        新创建的模型配置信息

    Raises:
        HTTPException: 供应商不存在或模型代码已存在
    """
    try:
        model = service.create_model_config(request)
        return CreateModelConfigResponse(model=model)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/models/{model_id}", response_model=UpdateModelConfigResponse)
async def update_model_config(
    model_id: str,
    request: UpdateModelConfigRequest,
    service: ModelProviderService = Depends(get_model_provider_service),
    _admin: None = Depends(require_admin)
):
    """
    更新模型配置

    Args:
        model_id: 模型配置ID
        request: 更新请求

    Returns:
        更新后的模型配置信息

    Raises:
        HTTPException: 模型配置不存在
    """
    try:
        model = service.update_model_config(model_id, request)
        return UpdateModelConfigResponse(model=model)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_config(
    model_id: str,
    service: ModelProviderService = Depends(get_model_provider_service),
    _admin: None = Depends(require_admin)
):
    """
    删除模型配置

    Args:
        model_id: 模型配置ID

    Raises:
        HTTPException: 模型配置不存在
    """
    try:
        service.delete_model_config(model_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
