# -*- coding: utf-8 -*-
"""导航模块管理路由

提供导航模块的管理接口
"""
import logging
from typing import Annotated, List

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from src.models import (
    UserInfo,
    AdminNavigationModuleListResponse,
    AdminNavigationModuleListItem,
    CreateNavigationModuleRequest,
    CreateNavigationModuleResponse,
    UpdateNavigationModuleRequest,
    UpdateNavigationModuleResponse,
    MoveNavigationModuleResponse,
)
from src.db_models import NavigationModuleModel
from src.database import get_db
from src.interfaces.dependencies import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["管理员-导航模块"])


def _model_to_response(model: NavigationModuleModel) -> AdminNavigationModuleListItem:
    """将数据库模型转换为响应模型"""
    type_value = model.type.value
    # 兼容处理：如果是 toolset（旧数据），返回 ai_tools
    if type_value == "toolset":
        type_value = "ai_tools"
    return AdminNavigationModuleListItem(
        id=str(model.id),
        name=model.name,
        type=type_value,
        config_source=model.config_source,
        page_path=model.page_path,
        icon=model.icon,
        order=model.order
    )


@router.get("/navigation-modules", response_model=AdminNavigationModuleListResponse)
async def get_navigation_modules(
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取导航模块列表（管理后台）"""
    try:
        modules = db.query(NavigationModuleModel).order_by(NavigationModuleModel.order).all()
        return AdminNavigationModuleListResponse(
            modules=[_model_to_response(m) for m in modules]
        )
    except Exception as e:
        logger.error(f"获取导航模块列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/navigation-modules", response_model=CreateNavigationModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_navigation_module(
    request: CreateNavigationModuleRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建导航模块（管理后台）"""
    try:
        # 验证配置
        if request.type == "ai_tools" and not request.config_source:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ai_tools类型必须指定config_source"
            )
        if request.type == "page" and not request.page_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page类型必须指定page_path"
            )

        # 检查名称是否重复
        existing = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.name == request.name
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"导航模块名称 '{request.name}' 已存在"
            )

        # 创建新模块
        from src.db_models import NavigationModuleType
        db_module = NavigationModuleModel(
            name=request.name,
            type=NavigationModuleType(request.type),
            config_source=request.config_source,
            page_path=request.page_path,
            icon=request.icon,
            order=request.order
        )
        db.add(db_module)
        db.commit()
        db.refresh(db_module)

        return CreateNavigationModuleResponse(
            module=_model_to_response(db_module)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建导航模块失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/navigation-modules/{module_id}", response_model=UpdateNavigationModuleResponse)
async def update_navigation_module(
    module_id: str,
    request: UpdateNavigationModuleRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新导航模块（管理后台）"""
    try:
        module = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.id == module_id
        ).first()

        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"导航模块 '{module_id}' 不存在"
            )

        # 更新字段
        if request.name is not None:
            # 检查名称是否重复
            existing = db.query(NavigationModuleModel).filter(
                NavigationModuleModel.name == request.name,
                NavigationModuleModel.id != module_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"导航模块名称 '{request.name}' 已被使用"
                )
            module.name = request.name

        if request.type is not None:
            from src.db_models import NavigationModuleType
            module.type = NavigationModuleType(request.type)

        if request.config_source is not None:
            module.config_source = request.config_source

        if request.page_path is not None:
            module.page_path = request.page_path

        if request.icon is not None:
            module.icon = request.icon

        if request.order is not None:
            module.order = request.order

        db.commit()
        db.refresh(module)

        return UpdateNavigationModuleResponse(
            module=_model_to_response(module)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新导航模块失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/navigation-modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_navigation_module(
    module_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除导航模块（管理后台）"""
    try:
        module = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.id == module_id
        ).first()

        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"导航模块 '{module_id}' 不存在"
            )

        db.delete(module)
        db.commit()

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除导航模块失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/navigation-modules/{module_id}/move-up", response_model=MoveNavigationModuleResponse)
async def move_navigation_module_up(
    module_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """上移导航模块（管理后台）"""
    try:
        module = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.id == module_id
        ).first()

        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"导航模块 '{module_id}' 不存在"
            )

        # 找到当前模块前面的模块
        previous_module = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.order < module.order
        ).order_by(NavigationModuleModel.order.desc()).first()

        if not previous_module:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已经是第一个模块，无法上移"
            )

        # 交换order值
        module.order, previous_module.order = previous_module.order, module.order

        db.commit()
        db.refresh(module)

        return MoveNavigationModuleResponse(
            message="导航模块已上移",
            module=_model_to_response(module)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上移导航模块失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/navigation-modules/{module_id}/move-down", response_model=MoveNavigationModuleResponse)
async def move_navigation_module_down(
    module_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """下移导航模块（管理后台）"""
    try:
        module = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.id == module_id
        ).first()

        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"导航模块 '{module_id}' 不存在"
            )

        # 找到当前模块后面的模块
        next_module = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.order > module.order
        ).order_by(NavigationModuleModel.order.asc()).first()

        if not next_module:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已经是最后一个模块，无法下移"
            )

        # 交换order值
        module.order, next_module.order = next_module.order, module.order

        db.commit()
        db.refresh(module)

        return MoveNavigationModuleResponse(
            message="导航模块已下移",
            module=_model_to_response(module)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下移导航模块失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
