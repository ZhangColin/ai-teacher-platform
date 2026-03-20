# -*- coding: utf-8 -*-
"""
模型配置路由

提供系统支持的模型列表查询接口
"""
import logging
from fastapi import APIRouter, Depends
from src.interfaces.dependencies import get_model_service
from src.services.model_service import ModelService, ModelInfo
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models", response_model=List[ModelInfo], tags=["模型配置"])
async def get_available_models(
    model_service: ModelService = Depends(get_model_service)
):
    """
    获取系统支持的所有可用模型列表

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
