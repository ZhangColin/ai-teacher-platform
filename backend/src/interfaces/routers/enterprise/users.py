# -*- coding: utf-8 -*-
"""企业用户管理路由（企业后台）"""
import logging
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.models import UserInfo
from src.database import get_db
from src.interfaces.dependencies import require_enterprise_admin
from src.services.user_service import UserService
from src.db_models import UserModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["企业-用户管理"])


@router.get("")
async def get_users(
    page: int = 1,
    page_size: int = 20,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取企业用户列表"""
    if page_size > 100:
        page_size = 100

    query = db.query(UserModel).filter(
        UserModel.enterprise_id == current_user.enterprise_id
    )

    total = query.count()

    users = query.order_by(desc(UserModel.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    from src.models import UserListItem
    items = [
        UserListItem(
            user_id=u.user_id,
            username=u.username,
            nickname=u.nickname or u.username,
            email=u.email,
            phone=u.phone,
            avatar=u.avatar,
            is_admin=u.is_admin,
            created_at=u.created_at
        )
        for u in users
    ]

    return {"users": items, "total": total, "page": page}


@router.post("")
async def create_user(
    request: dict,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建企业用户"""
    user_service = UserService()
    try:
        user = user_service.create_user(
            username=request["username"],
            nickname=request.get("nickname"),
            email=request.get("email"),
            password=request["password"],
            phone=request.get("phone"),
            is_enterprise_admin=False
        )

        # 关联到当前企业
        user_model = db.query(UserModel).filter(
            UserModel.user_id == user.user_id
        ).first()
        if user_model:
            user_model.enterprise_id = current_user.enterprise_id
            db.commit()

        return {"user_id": user.user_id, "message": "创建成功"}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除企业用户"""
    user = db.query(UserModel).filter(
        UserModel.user_id == user_id,
        UserModel.enterprise_id == current_user.enterprise_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    try:
        db.delete(user)
        db.commit()
        return {"message": "删除成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
