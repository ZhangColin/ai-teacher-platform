# -*- coding: utf-8 -*-
"""模型积分汇率配置路由（后台管理员）"""
import logging
from typing import Annotated, List
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from src.models import (
    UserInfo,
    ModelPointRateItem,
    CreatePointRateRequest,
    UpdatePointRateRequest,
    ModelRatesStatusResponse,
    ModelRateStatusItem,
    RateConfigInfo,
    BatchUpdateRateRequest,
    BatchUpdateRateResponse,
)
from src.database import get_db
from src.interfaces.dependencies import require_admin
from src.db_models import (
    ModelPointRateModel,
    ModelConfigModel,
    ModelProviderModel,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/point-rates", tags=["管理员-模型汇率"])


def _model_to_response(model: ModelPointRateModel) -> ModelPointRateItem:
    """将数据库模型转换为响应"""
    # 获取关联的模型配置信息
    config = model.model_config if hasattr(model, 'model_config') else None
    provider_code = ""
    model_code = ""
    model_name = ""

    if config:
        model_code = config.model_code
        model_name = config.model_name
        # 获取供应商信息
        provider = config.provider if hasattr(config, 'provider') else None
        if provider:
            provider_code = provider.provider_code

    return ModelPointRateItem(
        id=str(model.id),
        model_config_id=str(model.model_config_id),
        provider_code=provider_code,
        model_code=model_code,
        model_name=model_name,
        tokens_per_point=model.tokens_per_point,
        separate_io=model.separate_io,
        tokens_per_point_input=model.tokens_per_point_input,
        tokens_per_point_output=model.tokens_per_point_output,
        is_enabled=model.is_enabled,
    )


@router.get("", response_model=List[ModelPointRateItem])
async def get_point_rates(
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取所有汇率配置列表"""
    rates = db.query(ModelPointRateModel).order_by(
        ModelPointRateModel.created_at.desc()
    ).all()

    # 预加载关联数据
    for rate in rates:
        # 手动加载关联
        config = db.query(ModelConfigModel).filter(
            ModelConfigModel.id == rate.model_config_id
        ).first()
        if config:
            rate.model_config = config
            provider = db.query(ModelProviderModel).filter(
                ModelProviderModel.id == config.provider_id
            ).first()
            if provider:
                config.provider = provider

    return [_model_to_response(r) for r in rates]


@router.post("", response_model=ModelPointRateItem, status_code=status.HTTP_201_CREATED)
async def create_point_rate(
    request: CreatePointRateRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建汇率配置"""
    # 检查模型配置是否存在
    model_config = db.query(ModelConfigModel).filter(
        ModelConfigModel.id == request.model_config_id
    ).first()
    if not model_config:
        raise HTTPException(status_code=404, detail="模型配置不存在")

    # 检查是否已存在汇率配置
    existing = db.query(ModelPointRateModel).filter(
        ModelPointRateModel.model_config_id == request.model_config_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="该模型配置已有汇率记录，请使用更新接口")

    # 验证：如果 separate_io=True，必须提供 input/output 值
    if request.separate_io and (not request.tokens_per_point_input or not request.tokens_per_point_output):
        raise HTTPException(
            status_code=400,
            detail="区分输入输出时，必须提供 tokens_per_point_input 和 tokens_per_point_output"
        )

    try:
        rate = ModelPointRateModel(
            model_config_id=request.model_config_id,
            tokens_per_point=request.tokens_per_point,
            separate_io=request.separate_io,
            tokens_per_point_input=request.tokens_per_point_input,
            tokens_per_point_output=request.tokens_per_point_output,
            is_enabled=True,
        )
        db.add(rate)
        db.commit()
        db.refresh(rate)

        # 加载关联数据用于响应
        rate.model_config = model_config
        provider = db.query(ModelProviderModel).filter(
            ModelProviderModel.id == model_config.provider_id
        ).first()
        if provider:
            model_config.provider = provider

        logger.info(f"创建模型汇率配置成功 - 模型配置ID:{request.model_config_id}")
        return _model_to_response(rate)

    except Exception as e:
        db.rollback()
        logger.error(f"创建模型汇率配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{rate_id}", response_model=ModelPointRateItem)
async def update_point_rate(
    rate_id: str,
    request: UpdatePointRateRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新汇率配置"""
    rate = db.query(ModelPointRateModel).filter(
        ModelPointRateModel.id == rate_id
    ).first()
    if not rate:
        raise HTTPException(status_code=404, detail="汇率配置不存在")

    # 更新字段
    if request.tokens_per_point is not None:
        rate.tokens_per_point = request.tokens_per_point
    if request.separate_io is not None:
        rate.separate_io = request.separate_io
    if request.tokens_per_point_input is not None:
        rate.tokens_per_point_input = request.tokens_per_point_input
    if request.tokens_per_point_output is not None:
        rate.tokens_per_point_output = request.tokens_per_point_output
    if request.is_enabled is not None:
        rate.is_enabled = request.is_enabled

    # 验证
    if rate.separate_io and (not rate.tokens_per_point_input or not rate.tokens_per_point_output):
        raise HTTPException(
            status_code=400,
            detail="区分输入输出时，必须提供 tokens_per_point_input 和 tokens_per_point_output"
        )

    try:
        db.commit()
        db.refresh(rate)

        # 加载关联数据
        config = db.query(ModelConfigModel).filter(
            ModelConfigModel.id == rate.model_config_id
        ).first()
        if config:
            rate.model_config = config
            provider = db.query(ModelProviderModel).filter(
                ModelProviderModel.id == config.provider_id
            ).first()
            if provider:
                config.provider = provider

        logger.info(f"更新模型汇率配置成功 - ID:{rate_id}")
        return _model_to_response(rate)

    except Exception as e:
        db.rollback()
        logger.error(f"更新模型汇率配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_point_rate(
    rate_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除汇率配置"""
    rate = db.query(ModelPointRateModel).filter(
        ModelPointRateModel.id == rate_id
    ).first()
    if not rate:
        raise HTTPException(status_code=404, detail="汇率配置不存在")

    try:
        db.delete(rate)
        db.commit()
        logger.info(f"删除模型汇率配置成功 - ID:{rate_id}")
        return None

    except Exception as e:
        db.rollback()
        logger.error(f"删除模型汇率配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=ModelRatesStatusResponse)
async def get_model_rates_status(
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取所有已启用模型的汇率配置状态"""
    # 查询所有已启用的供应商
    enabled_providers = db.query(ModelProviderModel).filter(
        ModelProviderModel.is_enabled == True
    ).all()

    if not enabled_providers:
        return ModelRatesStatusResponse(models=[])

    provider_ids = [p.id for p in enabled_providers]

    # 查询这些供应商下所有已启用的模型
    models = db.query(ModelConfigModel).filter(
        ModelConfigModel.provider_id.in_(provider_ids),
        ModelConfigModel.is_enabled == True
    ).all()

    if not models:
        return ModelRatesStatusResponse(models=[])

    # 获取所有模型ID
    model_ids = [m.id for m in models]

    # 查询所有汇率配置
    rate_configs = db.query(ModelPointRateModel).filter(
        ModelPointRateModel.model_config_id.in_(model_ids)
    ).all()

    # 创建汇率配置字典
    rate_dict = {r.model_config_id: r for r in rate_configs}

    # 构建响应
    result_items = []
    for model in models:
        # 获取供应商信息
        provider = next((p for p in enabled_providers if p.id == model.provider_id), None)
        if not provider:
            continue

        # 获取汇率配置
        rate_config = rate_dict.get(model.id)

        rate_info = None
        if rate_config:
            rate_info = RateConfigInfo(
                id=str(rate_config.id),
                tokens_per_point_input=rate_config.tokens_per_point_input,
                tokens_per_point_output=rate_config.tokens_per_point_output,
                is_enabled=rate_config.is_enabled,
            )

        item = ModelRateStatusItem(
            model_config_id=str(model.id),
            provider_id=str(provider.id),
            provider_code=provider.provider_code,
            provider_name=provider.provider_name,
            model_code=model.model_code,
            model_name=model.model_name,
            is_model_enabled=model.is_enabled,
            rate_config=rate_info,
        )
        result_items.append(item)

    return ModelRatesStatusResponse(models=result_items)


@router.post("/batch-update", response_model=BatchUpdateRateResponse)
async def batch_update_rates(
    request: BatchUpdateRateRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """批量更新模型汇率配置

    事务处理：全部成功或全部回滚
    更新逻辑：已有配置则更新，无配置则创建
    """
    try:
        updated_count = 0

        for update_item in request.updates:
            # 查找现有汇率配置
            existing_rate = db.query(ModelPointRateModel).filter(
                ModelPointRateModel.model_config_id == update_item.model_config_id
            ).first()

            if existing_rate:
                # 更新现有配置
                existing_rate.tokens_per_point_input = update_item.tokens_per_point_input
                existing_rate.tokens_per_point_output = update_item.tokens_per_point_output
                existing_rate.separate_io = True  # 固定为 True
                existing_rate.is_enabled = update_item.is_enabled
            else:
                # 创建新配置
                new_rate = ModelPointRateModel(
                    model_config_id=update_item.model_config_id,
                    tokens_per_point=1000,  # 保留但不使用
                    separate_io=True,
                    tokens_per_point_input=update_item.tokens_per_point_input,
                    tokens_per_point_output=update_item.tokens_per_point_output,
                    is_enabled=update_item.is_enabled,
                )
                db.add(new_rate)

            updated_count += 1

        db.commit()
        logger.info(f"批量更新模型汇率成功 - 更新数量: {updated_count}")

        return BatchUpdateRateResponse(updated=updated_count)

    except Exception as e:
        db.rollback()
        logger.error(f"批量更新模型汇率失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
