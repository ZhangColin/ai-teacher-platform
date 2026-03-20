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
from src.db_models import AIToolModel, ToolsetModel, AIToolCategoryModel, AIToolType
from src.database import get_db
from src.interfaces.dependencies import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["管理员-AI工具"])


def _model_to_response(model: AIToolModel) -> AdminAIToolListItem:
    """将数据库模型转换为响应模型"""
    return AdminAIToolListItem(
        id=str(model.id),
        tool_id=model.tool_id,
        toolset_id=model.toolset_id,
        category_id=str(model.category_id) if model.category_id else None,
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
    toolset_id: Optional[str] = None,
    category_id: Optional[str] = None,
    visible: Optional[bool] = None,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取AI工具列表（管理后台）"""
    try:
        query = db.query(AIToolModel)

        if toolset_id:
            # 根据toolset_id查找工具集
            toolset = db.query(ToolsetModel).filter(
                ToolsetModel.toolset_id == toolset_id
            ).first()
            if toolset:
                query = query.filter(AIToolModel.toolset_id == toolset.id)

        if category_id:
            query = query.filter(AIToolModel.category_id == category_id)

        if visible is not None:
            query = query.filter(AIToolModel.visible == visible)

        tools = query.order_by(AIToolModel.order).all()

        return AdminAIToolListResponse(
            tools=[_model_to_response(t) for t in tools],
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
        # 查找工具集
        toolset = db.query(ToolsetModel).filter(
            ToolsetModel.toolset_id == request.toolset_id
        ).first()

        if not toolset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具集 '{request.toolset_id}' 不存在"
            )

        # 如果指定了分类，验证分类是否存在
        category = None
        if request.category_id:
            category = db.query(AIToolCategoryModel).filter(
                AIToolCategoryModel.id == request.category_id
            ).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"工具分类 '{request.category_id}' 不存在"
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
            toolset_id=toolset.id,
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
            tool=_model_to_response(db_tool)
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

        if request.category_id is not None:
            # 验证分类是否存在
            if request.category_id:
                category = db.query(AIToolCategoryModel).filter(
                    AIToolCategoryModel.id == request.category_id
                ).first()
                if not category:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"工具分类 '{request.category_id}' 不存在"
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
            tool=_model_to_response(tool)
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

        # 找到当前工具前面的工具（同一工具集下）
        previous_tool = db.query(AIToolModel).filter(
            AIToolModel.toolset_id == tool.toolset_id,
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
            tool=_model_to_response(tool)
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

        # 找到当前工具后面的工具（同一工具集下）
        next_tool = db.query(AIToolModel).filter(
            AIToolModel.toolset_id == tool.toolset_id,
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
            tool=_model_to_response(tool)
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
            tool=_model_to_response(tool)
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
