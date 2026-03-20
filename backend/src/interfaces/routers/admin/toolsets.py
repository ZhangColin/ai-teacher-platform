# -*- coding: utf-8 -*-
"""工具集管理路由

提供工具集的管理接口
"""
import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from src.models import (
    UserInfo,
    AdminToolsetListResponse,
    AdminToolsetListItem,
    CreateToolsetRequest,
    CreateToolsetResponse,
    UpdateToolsetRequest,
    UpdateToolsetResponse,
    MoveToolsetResponse,
)
from src.db_models import ToolsetModel
from src.database import get_db
from src.interfaces.dependencies import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["管理员-工具集"])


def _model_to_response(model: ToolsetModel) -> AdminToolsetListItem:
    """将数据库模型转换为响应模型"""
    return AdminToolsetListItem(
        id=str(model.id),
        toolset_id=model.toolset_id,
        name=model.name,
        description=model.description,
        icon=model.icon,
        order=model.order
    )


@router.get("/toolsets", response_model=AdminToolsetListResponse)
async def get_toolsets(
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取工具集列表（管理后台）"""
    try:
        toolsets = db.query(ToolsetModel).order_by(ToolsetModel.order).all()
        return AdminToolsetListResponse(
            toolsets=[_model_to_response(t) for t in toolsets]
        )
    except Exception as e:
        logger.error(f"获取工具集列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/toolsets", response_model=CreateToolsetResponse, status_code=status.HTTP_201_CREATED)
async def create_toolset(
    request: CreateToolsetRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建工具集（管理后台）"""
    try:
        # 检查toolset_id是否重复
        existing = db.query(ToolsetModel).filter(
            ToolsetModel.toolset_id == request.toolset_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"工具集ID '{request.toolset_id}' 已存在"
            )

        # 创建新工具集
        db_toolset = ToolsetModel(
            toolset_id=request.toolset_id,
            name=request.name,
            description=request.description,
            icon=request.icon,
            order=request.order
        )
        db.add(db_toolset)
        db.commit()
        db.refresh(db_toolset)

        return CreateToolsetResponse(
            toolset=_model_to_response(db_toolset)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建工具集失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/toolsets/{toolset_id}", response_model=UpdateToolsetResponse)
async def update_toolset(
    toolset_id: str,
    request: UpdateToolsetRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新工具集（管理后台）"""
    try:
        toolset = db.query(ToolsetModel).filter(
            ToolsetModel.toolset_id == toolset_id
        ).first()

        if not toolset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具集 '{toolset_id}' 不存在"
            )

        # 更新字段
        if request.toolset_id is not None:
            # 检查toolset_id是否重复
            existing = db.query(ToolsetModel).filter(
                ToolsetModel.toolset_id == request.toolset_id,
                ToolsetModel.id != toolset.id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"工具集ID '{request.toolset_id}' 已被使用"
                )
            toolset.toolset_id = request.toolset_id

        if request.name is not None:
            toolset.name = request.name

        if request.description is not None:
            toolset.description = request.description

        if request.icon is not None:
            toolset.icon = request.icon

        if request.order is not None:
            toolset.order = request.order

        db.commit()
        db.refresh(toolset)

        return UpdateToolsetResponse(
            toolset=_model_to_response(toolset)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新工具集失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/toolsets/{toolset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_toolset(
    toolset_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除工具集（管理后台）"""
    try:
        toolset = db.query(ToolsetModel).filter(
            ToolsetModel.toolset_id == toolset_id
        ).first()

        if not toolset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具集 '{toolset_id}' 不存在"
            )

        # 检查是否有关联的工具或分类
        from src.db_models import AIToolModel, AIToolCategoryModel
        tools_count = db.query(AIToolModel).filter(
            AIToolModel.toolset_id == toolset.id
        ).count()
        categories_count = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.toolset_id == toolset.id
        ).count()

        if tools_count > 0 or categories_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"工具集下还有 {tools_count} 个工具和 {categories_count} 个分类，无法删除"
            )

        db.delete(toolset)
        db.commit()

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除工具集失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/toolsets/{toolset_id}/move-up", response_model=MoveToolsetResponse)
async def move_toolset_up(
    toolset_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """上移工具集（管理后台）"""
    try:
        toolset = db.query(ToolsetModel).filter(
            ToolsetModel.toolset_id == toolset_id
        ).first()

        if not toolset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具集 '{toolset_id}' 不存在"
            )

        # 找到当前工具集前面的工具集
        previous_toolset = db.query(ToolsetModel).filter(
            ToolsetModel.order < toolset.order
        ).order_by(ToolsetModel.order.desc()).first()

        if not previous_toolset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已经是第一个工具集，无法上移"
            )

        # 交换order值
        toolset.order, previous_toolset.order = previous_toolset.order, toolset.order

        db.commit()
        db.refresh(toolset)

        return MoveToolsetResponse(
            message="工具集已上移",
            toolset=_model_to_response(toolset)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上移工具集失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/toolsets/{toolset_id}/move-down", response_model=MoveToolsetResponse)
async def move_toolset_down(
    toolset_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """下移工具集（管理后台）"""
    try:
        toolset = db.query(ToolsetModel).filter(
            ToolsetModel.toolset_id == toolset_id
        ).first()

        if not toolset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具集 '{toolset_id}' 不存在"
            )

        # 找到当前工具集后面的工具集
        next_toolset = db.query(ToolsetModel).filter(
            ToolsetModel.order > toolset.order
        ).order_by(ToolsetModel.order.asc()).first()

        if not next_toolset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已经是最后一个工具集，无法下移"
            )

        # 交换order值
        toolset.order, next_toolset.order = next_toolset.order, toolset.order

        db.commit()
        db.refresh(toolset)

        return MoveToolsetResponse(
            message="工具集已下移",
            toolset=_model_to_response(toolset)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下移工具集失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
