# -*- coding: utf-8 -*-
"""
模型配置路由

提供系统支持的模型列表查询接口
"""
import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.interfaces.dependencies import get_db, get_model_service
from src.services.model_service import ModelService, ModelInfo
from src.services.model_provider_service import ModelProviderService
from src.models import ModelConfigListItem, AvailableModelResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models", response_model=List[ModelInfo], tags=["模型配置"])
async def get_available_models(
    model_service: ModelService = Depends(get_model_service)
):
    """
    获取系统支持的所有可用模型列表（从配置文件读取）

    Returns:
        List[ModelInfo]: 模型列表，包含模型ID、名称、服务商和描述
    """
    try:
        models = model_service.get_available_models()
        logger.info(f"✅ 返回 {len(models)} 个可用模型")
        return models

    except Exception as e:
        logger.error(f"❌ 获取模型列表失败: {e}")
        return []


@router.get("/models/available", response_model=AvailableModelResponse, tags=["模型配置"])
async def get_available_models_from_db(
    provider_id: str = None,
    provider_code: str = None,
    capability: str = None,
    db: Session = Depends(get_db)
):
    """
    获取所有启用的可用模型列表（从数据库读取）

    这是新增的端点，用于替代原来的配置文件方式

    Args:
        provider_id: 可选的供应商ID过滤（数据库UUID）
        provider_code: 可选的供应商代码过滤（如 deepseek, openai, kimi 等）
        capability: 可选的能力过滤（如 chat、vision、image_generation 等）
        db: 数据库会话

    Returns:
        可用模型列表（仅返回启用供应商的启用模型）
    """
    try:
        service = ModelProviderService(db)

        # 如果提供了 provider_code，先转换为 provider_id
        actual_provider_id = provider_id
        if provider_code:
            provider = service.get_provider_by_code(provider_code)
            if provider:
                actual_provider_id = provider.id
            else:
                logger.warning(f"❌ 供应商代码 '{provider_code}' 不存在")
                return AvailableModelResponse(models=[])

        models = service.get_all_models(
            provider_id=actual_provider_id,
            include_disabled=False,  # 只返回启用的模型
            capability=capability
        )

        logger.info(f"✅ 返回 {len(models)} 个可用模型（从数据库）")
        return AvailableModelResponse(models=models)

    except Exception as e:
        logger.error(f"❌ 获取模型列表失败: {e}")
        return AvailableModelResponse(models=[])
