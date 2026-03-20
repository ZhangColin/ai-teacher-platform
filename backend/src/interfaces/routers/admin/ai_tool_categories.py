# -*- coding: utf-8 -*-
"""AI工具分类管理路由

提供AI工具分类的管理接口
"""
import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from src.models import (
    UserInfo,
    AdminAIToolCategoryListResponse,
    AdminAIToolCategoryListItem,
    CreateAIToolCategoryRequest,
    CreateAIToolCategoryResponse,
    UpdateAIToolCategoryRequest,
    UpdateAIToolCategoryResponse,
    MoveAIToolCategoryResponse,
)
from src.db_models import AIToolCategoryModel, ToolsetModel
from src.database import get_db
from src.interfaces.dependencies import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["管理员-AI工具分类"])


def _model_to_response(model: AIToolCategoryModel) -> AdminAIToolCategoryListItem:
    """将数据库模型转换为响应模型"""
    return AdminAIToolCategoryListItem(
        id=str(model.id),
        toolset_id=str(model.toolset_id),
        name=model.name,
        icon=model.icon,
        order=model.order
    )


@router.get("/ai-tool-categories", response_model=AdminAIToolCategoryListResponse)
async def get_ai_tool_categories(
    toolset_id: str = None,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取AI工具分类列表（管理后台）"""
    try:
        query = db.query(AIToolCategoryModel)

        if toolset_id:
            # 根据toolset_id查找工具集
            toolset = db.query(ToolsetModel).filter(
                ToolsetModel.toolset_id == toolset_id
            ).first()
            if toolset:
                query = query.filter(AIToolCategoryModel.toolset_id == toolset.id)

        categories = query.order_by(AIToolCategoryModel.order).all()
        return AdminAIToolCategoryListResponse(
            categories=[_model_to_response(c) for c in categories]
        )
    except Exception as e:
        logger.error(f"获取AI工具分类列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/ai-tool-categories", response_model=CreateAIToolCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_tool_category(
    request: CreateAIToolCategoryRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建AI工具分类（管理后台）"""
    try:
        # 查找工具集
        toolset = db.query(ToolsetModel).filter(
            ToolsetModel.toolset_id == request.toolset_id
        ).first()

        if not toolset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具集 '{request.toolset_id}' 不存在"
            )

        # 检查同一工具集下分类名称是否重复
        existing = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.toolset_id == toolset.id,
            AIToolCategoryModel.name == request.name
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"工具集 '{request.toolset_id}' 下已存在分类 '{request.name}'"
            )

        # 创建新分类
        db_category = AIToolCategoryModel(
            toolset_id=toolset.id,
            name=request.name,
            icon=request.icon,
            order=request.order
        )
        db.add(db_category)
        db.commit()
        db.refresh(db_category)

        return CreateAIToolCategoryResponse(
            category=_model_to_response(db_category)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建AI工具分类失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/ai-tool-categories/{category_id}", response_model=UpdateAIToolCategoryResponse)
async def update_ai_tool_category(
    category_id: str,
    request: UpdateAIToolCategoryRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新AI工具分类（管理后台）"""
    try:
        category = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.id == category_id
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI工具分类 '{category_id}' 不存在"
            )

        # 更新字段
        if request.name is not None:
            # 检查同一工具集下分类名称是否重复
            existing = db.query(AIToolCategoryModel).filter(
                AIToolCategoryModel.toolset_id == category.toolset_id,
                AIToolCategoryModel.name == request.name,
                AIToolCategoryModel.id != category_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"同一工具集下已存在分类 '{request.name}'"
                )
            category.name = request.name

        if request.icon is not None:
            category.icon = request.icon

        if request.order is not None:
            category.order = request.order

        db.commit()
        db.refresh(category)

        return UpdateAIToolCategoryResponse(
            category=_model_to_response(category)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新AI工具分类失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/ai-tool-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_tool_category(
    category_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除AI工具分类（管理后台）"""
    try:
        category = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.id == category_id
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI工具分类 '{category_id}' 不存在"
            )

        # 检查是否有关联的工具
        from src.db_models import AIToolModel
        tools_count = db.query(AIToolModel).filter(
            AIToolModel.category_id == category_id
        ).count()

        if tools_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"分类下还有 {tools_count} 个工具，无法删除"
            )

        db.delete(category)
        db.commit()

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除AI工具分类失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/ai-tool-categories/{category_id}/move-up", response_model=MoveAIToolCategoryResponse)
async def move_ai_tool_category_up(
    category_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """上移AI工具分类（管理后台）"""
    try:
        category = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.id == category_id
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI工具分类 '{category_id}' 不存在"
            )

        # 找到当前分类前面的分类（同一工具集下）
        previous_category = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.toolset_id == category.toolset_id,
            AIToolCategoryModel.order < category.order
        ).order_by(AIToolCategoryModel.order.desc()).first()

        if not previous_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已经是第一个分类，无法上移"
            )

        # 交换order值
        category.order, previous_category.order = previous_category.order, category.order

        db.commit()
        db.refresh(category)

        return MoveAIToolCategoryResponse(
            message="分类已上移",
            category=_model_to_response(category)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上移AI工具分类失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/ai-tool-categories/{category_id}/move-down", response_model=MoveAIToolCategoryResponse)
async def move_ai_tool_category_down(
    category_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """下移AI工具分类（管理后台）"""
    try:
        category = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.id == category_id
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI工具分类 '{category_id}' 不存在"
            )

        # 找到当前分类后面的分类（同一工具集下）
        next_category = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.toolset_id == category.toolset_id,
            AIToolCategoryModel.order > category.order
        ).order_by(AIToolCategoryModel.order.asc()).first()

        if not next_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已经是最后一个分类，无法下移"
            )

        # 交换order值
        category.order, next_category.order = next_category.order, category.order

        db.commit()
        db.refresh(category)

        return MoveAIToolCategoryResponse(
            message="分类已下移",
            category=_model_to_response(category)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下移AI工具分类失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
