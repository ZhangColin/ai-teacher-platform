# -*- coding: utf-8 -*-
"""导航模块分类管理路由

提供导航模块下分类的管理接口
"""
import logging
from typing import Annotated, List
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from src.models import (
    UserInfo,
    AdminNavigationModuleCategoryListResponse,
    AdminNavigationModuleCategoryListItem,
    CreateNavigationModuleCategoryRequest,
    CreateNavigationModuleCategoryResponse,
    UpdateNavigationModuleCategoryRequest,
    UpdateNavigationModuleCategoryResponse,
)
from src.db_models import (
    NavigationModuleModel,
    AIToolCategoryModel,
)
from src.database import get_db
from src.interfaces.dependencies import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["管理员-导航模块分类"])


def _model_to_response(model: AIToolCategoryModel, nav_module: NavigationModuleModel) -> AdminNavigationModuleCategoryListItem:
    """将数据库模型转换为响应模型"""
    return AdminNavigationModuleCategoryListItem(
        id=str(model.id),
        navigation_module_id=str(model.navigation_module_id),
        navigation_module_name=nav_module.name,
        name=model.name,
        icon=model.icon,
        order=model.order,
        created_at=model.created_at.isoformat(),
        updated_at=model.updated_at.isoformat(),
    )


@router.get("/navigation-modules/{module_id}/categories", response_model=AdminNavigationModuleCategoryListResponse)
async def get_categories(
    module_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取导航模块的分类列表"""
    try:
        # 验证导航模块存在
        nav_module = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.id == module_id
        ).first()
        if not nav_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="导航模块不存在"
            )

        categories = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.navigation_module_id == module_id
        ).order_by(AIToolCategoryModel.order).all()

        return AdminNavigationModuleCategoryListResponse(
            categories=[_model_to_response(c, nav_module) for c in categories]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分类列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/navigation-modules/{module_id}/categories",
             response_model=CreateNavigationModuleCategoryResponse,
             status_code=status.HTTP_201_CREATED)
async def create_category(
    module_id: str,
    request: CreateNavigationModuleCategoryRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建导航模块分类"""
    try:
        # 验证导航模块存在且类型为 ai_tools
        nav_module = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.id == module_id
        ).first()
        if not nav_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="导航模块不存在"
            )
        if nav_module.type.value != "ai_tools" and nav_module.type.value != "toolset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有AI工具类型的导航模块才能创建分类"
            )

        # 检查名称是否重复
        existing = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.navigation_module_id == module_id,
            AIToolCategoryModel.name == request.name
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"分类名称 '{request.name}' 已存在"
            )

        # 创建分类
        db_category = AIToolCategoryModel(
            id=str(uuid.uuid4()),
            navigation_module_id=module_id,
            name=request.name,
            icon=request.icon,
            order=request.order,
        )
        db.add(db_category)
        db.commit()

        return CreateNavigationModuleCategoryResponse(
            id=str(db_category.id),
            message="创建分类成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建分类失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/navigation-modules/{module_id}/categories/{category_id}",
            response_model=UpdateNavigationModuleCategoryResponse)
async def update_category(
    module_id: str,
    category_id: str,
    request: UpdateNavigationModuleCategoryRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新导航模块分类"""
    try:
        category = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.id == category_id,
            AIToolCategoryModel.navigation_module_id == module_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类不存在"
            )

        # 检查名称是否重复
        existing = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.navigation_module_id == module_id,
            AIToolCategoryModel.name == request.name,
            AIToolCategoryModel.id != category_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"分类名称 '{request.name}' 已存在"
            )

        category.name = request.name
        category.icon = request.icon
        category.order = request.order
        category.updated_at = datetime.now()
        db.commit()

        return UpdateNavigationModuleCategoryResponse(
            id=str(category.id),
            message="更新分类成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新分类失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/navigation-modules/{module_id}/categories/{category_id}",
               status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    module_id: str,
    category_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除导航模块分类"""
    try:
        category = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.id == category_id,
            AIToolCategoryModel.navigation_module_id == module_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类不存在"
            )

        db.delete(category)
        db.commit()

        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除分类失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
