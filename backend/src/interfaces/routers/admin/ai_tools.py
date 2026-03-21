# -*- coding: utf-8 -*-
"""AI工具管理路由

提供AI工具的管理接口
"""
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from src.models import (
    UserInfo,
    AdminAIToolListResponse,
    AdminAIToolListItem,
    CreateAIToolRequest,
    CreateAIToolResponse,
    UpdateAIToolRequest,
    UpdateAIToolResponse,
    MoveAIToolResponse,
    ToggleAIToolVisibilityResponse,
)
from src.db_models import (
    AIToolModel,
    NavigationModuleModel,
    AIToolCategoryModel,
    AIToolType
)
from src.database import get_db
from src.interfaces.dependencies import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["管理员-AI工具"])


def _model_to_response(model: AIToolModel, db: Session) -> AdminAIToolListItem:
    """将数据库模型转换为响应模型"""
    # 获取导航模块名称
    nav_module = db.query(NavigationModuleModel).filter(
        NavigationModuleModel.id == model.navigation_module_id
    ).first()
    nav_module_name = nav_module.name if nav_module else ""

    # 获取分类名称
    category = db.query(AIToolCategoryModel).filter(
        AIToolCategoryModel.id == model.category_id
    ).first() if model.category_id else None

    return AdminAIToolListItem(
        id=str(model.id),
        tool_id=model.tool_id,
        navigation_module_id=str(model.navigation_module_id),
        navigation_module_name=nav_module_name,
        category_id=str(model.category_id) if model.category_id else None,
        category_name=category.name if category else None,
        name=model.name,
        description=model.description,
        system_prompt=model.system_prompt,
        icon=model.icon,
        type=model.type.value,
        content_type=model.content_type,
        media_type=model.media_type,
        model=model.model,
        welcome_message=model.welcome_message,
        visible=model.visible,
        order=model.order
    )


@router.get("/ai-tools", response_model=AdminAIToolListResponse)
async def get_ai_tools(
    navigation_module_id: Optional[str] = None,
    category_id: Optional[str] = None,
    visible: Optional[bool] = None,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取AI工具列表（管理后台）"""
    try:
        query = db.query(AIToolModel)

        if navigation_module_id:
            # 根据navigation_module_id查找工具
            query = query.filter(AIToolModel.navigation_module_id == navigation_module_id)

        if category_id:
            query = query.filter(AIToolModel.category_id == category_id)

        if visible is not None:
            query = query.filter(AIToolModel.visible == visible)

        tools = query.order_by(AIToolModel.order).all()

        return AdminAIToolListResponse(
            tools=[_model_to_response(t, db) for t in tools],
            total=len(tools)
        )
    except Exception as e:
        logger.error(f"获取AI工具列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/ai-tools", response_model=CreateAIToolResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_tool(
    request: CreateAIToolRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建AI工具（管理后台）"""
    try:
        # 验证导航模块存在
        nav_module = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.id == request.navigation_module_id
        ).first()
        if not nav_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"导航模块 '{request.navigation_module_id}' 不存在"
            )

        # 如果指定了分类，验证分类是否存在且属于该导航模块
        category = None
        if request.category_id:
            category = db.query(AIToolCategoryModel).filter(
                AIToolCategoryModel.id == request.category_id,
                AIToolCategoryModel.navigation_module_id == request.navigation_module_id
            ).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"工具分类 '{request.category_id}' 不存在或不属于该导航模块"
                )

        # 检查tool_id是否重复
        existing = db.query(AIToolModel).filter(
            AIToolModel.tool_id == request.tool_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"工具ID '{request.tool_id}' 已存在"
            )

        # 创建新工具
        db_tool = AIToolModel(
            tool_id=request.tool_id,
            navigation_module_id=request.navigation_module_id,
            category_id=category.id if category else None,
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            icon=request.icon,
            type=AIToolType(request.type),
            content_type=request.content_type,
            media_type=request.media_type,
            model=request.model,
            welcome_message=request.welcome_message,
            visible=request.visible,
            order=request.order
        )
        db.add(db_tool)
        db.commit()
        db.refresh(db_tool)

        return CreateAIToolResponse(
            tool=_model_to_response(db_tool, db)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建AI工具失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/ai-tools/{tool_id}", response_model=UpdateAIToolResponse)
async def update_ai_tool(
    tool_id: str,
    request: UpdateAIToolRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新AI工具（管理后台）"""
    try:
        tool = db.query(AIToolModel).filter(
            AIToolModel.tool_id == tool_id
        ).first()

        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI工具 '{tool_id}' 不存在"
            )

        # 更新字段
        if request.tool_id is not None:
            # 检查tool_id是否重复
            existing = db.query(AIToolModel).filter(
                AIToolModel.tool_id == request.tool_id,
                AIToolModel.id != tool.id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"工具ID '{request.tool_id}' 已被使用"
                )
            tool.tool_id = request.tool_id

        if request.navigation_module_id is not None:
            # 验证导航模块存在
            nav_module = db.query(NavigationModuleModel).filter(
                NavigationModuleModel.id == request.navigation_module_id
            ).first()
            if not nav_module:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"导航模块 '{request.navigation_module_id}' 不存在"
                )
            tool.navigation_module_id = request.navigation_module_id

        if request.category_id is not None:
            # 验证分类是否存在且属于当前导航模块
            if request.category_id:
                category = db.query(AIToolCategoryModel).filter(
                    AIToolCategoryModel.id == request.category_id,
                    AIToolCategoryModel.navigation_module_id == tool.navigation_module_id
                ).first()
                if not category:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"工具分类 '{request.category_id}' 不存在或不属于该导航模块"
                    )
            tool.category_id = request.category_id

        if request.name is not None:
            tool.name = request.name

        if request.description is not None:
            tool.description = request.description

        if request.system_prompt is not None:
            tool.system_prompt = request.system_prompt

        if request.icon is not None:
            tool.icon = request.icon

        if request.type is not None:
            tool.type = AIToolType(request.type)

        if request.content_type is not None:
            tool.content_type = request.content_type

        if request.media_type is not None:
            tool.media_type = request.media_type

        if request.model is not None:
            tool.model = request.model

        if request.welcome_message is not None:
            tool.welcome_message = request.welcome_message

        if request.visible is not None:
            tool.visible = request.visible

        if request.order is not None:
            tool.order = request.order

        db.commit()
        db.refresh(tool)

        return UpdateAIToolResponse(
            tool=_model_to_response(tool, db)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新AI工具失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/ai-tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_tool(
    tool_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除AI工具（管理后台）"""
    try:
        tool = db.query(AIToolModel).filter(
            AIToolModel.tool_id == tool_id
        ).first()

        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI工具 '{tool_id}' 不存在"
            )

        db.delete(tool)
        db.commit()

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除AI工具失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/ai-tools/{tool_id}/move-up", response_model=MoveAIToolResponse)
async def move_ai_tool_up(
    tool_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """上移AI工具（管理后台）"""
    try:
        tool = db.query(AIToolModel).filter(
            AIToolModel.tool_id == tool_id
        ).first()

        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI工具 '{tool_id}' 不存在"
            )

        # 找到当前工具前面的工具（同一导航模块下）
        previous_tool = db.query(AIToolModel).filter(
            AIToolModel.navigation_module_id == tool.navigation_module_id,
            AIToolModel.order < tool.order
        ).order_by(AIToolModel.order.desc()).first()

        if not previous_tool:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已经是第一个工具，无法上移"
            )

        # 交换order值
        tool.order, previous_tool.order = previous_tool.order, tool.order

        db.commit()
        db.refresh(tool)

        return MoveAIToolResponse(
            message="工具已上移",
            tool=_model_to_response(tool, db)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上移AI工具失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/ai-tools/{tool_id}/move-down", response_model=MoveAIToolResponse)
async def move_ai_tool_down(
    tool_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """下移AI工具（管理后台）"""
    try:
        tool = db.query(AIToolModel).filter(
            AIToolModel.tool_id == tool_id
        ).first()

        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI工具 '{tool_id}' 不存在"
            )

        # 找到当前工具后面的工具（同一导航模块下）
        next_tool = db.query(AIToolModel).filter(
            AIToolModel.navigation_module_id == tool.navigation_module_id,
            AIToolModel.order > tool.order
        ).order_by(AIToolModel.order.asc()).first()

        if not next_tool:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已经是最后一个工具，无法下移"
            )

        # 交换order值
        tool.order, next_tool.order = next_tool.order, tool.order

        db.commit()
        db.refresh(tool)

        return MoveAIToolResponse(
            message="工具已下移",
            tool=_model_to_response(tool, db)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下移AI工具失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/ai-tools/{tool_id}/toggle-visibility", response_model=ToggleAIToolVisibilityResponse)
async def toggle_ai_tool_visibility(
    tool_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """切换AI工具可见性（管理后台）"""
    try:
        tool = db.query(AIToolModel).filter(
            AIToolModel.tool_id == tool_id
        ).first()

        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI工具 '{tool_id}' 不存在"
            )

        # 切换可见性
        tool.visible = not tool.visible
        db.commit()
        db.refresh(tool)

        message = f"工具已{'显示' if tool.visible else '隐藏'}"

        return ToggleAIToolVisibilityResponse(
            message=message,
            tool=_model_to_response(tool, db)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换AI工具可见性失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
