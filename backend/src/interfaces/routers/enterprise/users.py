# -*- coding: utf-8 -*-
"""企业用户管理路由（企业后台）"""
import logging
from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from src.models import UserInfo
from src.database import get_db
from src.interfaces.dependencies import require_enterprise_admin
from src.services.user_service import UserService
from src.db_models import UserModel, AIConsumptionModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["企业-用户管理"])


@router.get("")
async def get_users(
    page: int = 1,
    page_size: int = 20,
    username: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_by: str = "created_at",
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取企业用户列表"""
    if page_size > 100:
        page_size = 100

    query = db.query(UserModel).filter(
        UserModel.enterprise_id == current_user.enterprise_id
    )

    if username:
        query = query.filter(UserModel.username.like(f"%{username}%"))
    if is_active is not None:
        query = query.filter(UserModel.is_active == is_active)

    total = query.count()

    # 排序
    if sort_by == "total_consumed":
        # 子查询获取用户消耗积分
        consumption_subquery = db.query(
            AIConsumptionModel.user_id,
            func.sum(AIConsumptionModel.total_points).label("total")
        ).filter(
            AIConsumptionModel.enterprise_id == current_user.enterprise_id
        ).group_by(AIConsumptionModel.user_id).subquery()

        query = query.outerjoin(
            consumption_subquery, UserModel.user_id == consumption_subquery.c.user_id
        ).order_by(desc(consumption_subquery.c.total))
    else:
        query = query.order_by(desc(UserModel.created_at))

    users = query.offset((page - 1) * page_size).limit(page_size).all()

    # 批量获取用户消耗积分
    user_ids = [u.user_id for u in users]
    consumption_map = {}
    if user_ids:
        consumptions = db.query(
            AIConsumptionModel.user_id,
            func.sum(AIConsumptionModel.total_points).label("total")
        ).filter(
            AIConsumptionModel.user_id.in_(user_ids)
        ).group_by(AIConsumptionModel.user_id).all()
        consumption_map = {c.user_id: c.total or 0 for c in consumptions}

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
            is_active=u.is_active,
            enterprise_id=u.enterprise_id,
            is_enterprise_admin=u.is_enterprise_admin or False,
            total_consumed=consumption_map.get(u.user_id, 0),
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


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    request: dict,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新企业用户"""
    user = db.query(UserModel).filter(
        UserModel.user_id == user_id,
        UserModel.enterprise_id == current_user.enterprise_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新允许的字段
    if "nickname" in request:
        user.nickname = request["nickname"]
    if "email" in request:
        user.email = request["email"]
    if "is_active" in request:
        user.is_active = request["is_active"]
    if "is_enterprise_admin" in request:
        user.is_enterprise_admin = request["is_enterprise_admin"]

    try:
        db.commit()
        return {"message": "更新成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    request: dict,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """重置用户密码"""
    from src.services.auth_service import AuthService

    user = db.query(UserModel).filter(
        UserModel.user_id == user_id,
        UserModel.enterprise_id == current_user.enterprise_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    new_password = request.get("new_password")
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少6个字符")

    auth_service = AuthService()
    auth_service.set_password(user, new_password)

    try:
        db.commit()
        return {"message": "密码重置成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


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
