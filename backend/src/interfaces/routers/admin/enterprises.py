# -*- coding: utf-8 -*-
"""企业管理路由（后台管理员）"""
import logging
from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from src.models import (
    UserInfo,
    EnterpriseInfo,
    CreateEnterpriseRequest,
    UpdateEnterpriseRequest,
    EnterpriseListResponse,
    AddPointsRequest,
    EnterpriseStatus,
    PointSourceType,
)
from src.database import get_db
from src.interfaces.dependencies import require_admin
from src.services.enterprise_service import EnterpriseService
from src.services.point_service import PointService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/enterprises", tags=["管理员-企业管理"])


def _model_to_response(model) -> EnterpriseInfo:
    """将数据库模型转换为响应"""
    # 计算用户数
    from src.db_models import UserModel
    user_count = 0  # TODO: 实现用户数统计

    return EnterpriseInfo(
        id=str(model.id),
        name=model.name,
        code=model.code,
        status=model.status,
        balance_gratis=model.balance_gratis,
        balance_paid=model.balance_paid,
        debt_points=model.debt_points,
        total_points=model.total_points,
        user_count=user_count,
        created_at=model.created_at
    )


@router.get("", response_model=EnterpriseListResponse)
async def get_enterprises(
    page: int = 1,
    page_size: int = 20,
    status: Optional[EnterpriseStatus] = None,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取企业列表"""
    if page_size > 100:
        page_size = 100

    service = EnterpriseService(db)
    enterprises, total = service.get_all_enterprises(page, page_size, status)

    return EnterpriseListResponse(
        enterprises=[_model_to_response(e) for e in enterprises],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("", response_model=EnterpriseInfo, status_code=status.HTTP_201_CREATED)
async def create_enterprise(
    request: CreateEnterpriseRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建企业"""
    service = EnterpriseService(db)
    try:
        enterprise = service.create_enterprise(
            name=request.name,
            code=request.code,
            initial_gratis=request.initial_gratis
        )
        return _model_to_response(enterprise)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/consumptions")
async def get_all_consumptions(
    page: int = 1,
    page_size: int = 20,
    enterprise_id: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取所有消费记录（管理员）"""
    if page_size > 100:
        page_size = 100

    point_service = PointService(db)
    consumptions, total = point_service.get_all_consumptions(
        page=page,
        page_size=page_size,
        enterprise_id=enterprise_id,
        user_id=user_id
    )

    # 转换为响应格式
    items = []
    for c in consumptions:
        # 获取用户名和企业名
        from src.db_models import UserModel, EnterpriseModel
        user = db.query(UserModel).filter(UserModel.user_id == c.user_id).first()
        username = user.username if user else "未知用户"

        enterprise_name = "-"
        if user and user.enterprise_id:
            enterprise = db.query(EnterpriseModel).filter(EnterpriseModel.id == user.enterprise_id).first()
            if enterprise:
                enterprise_name = enterprise.name

        items.append({
            "id": str(c.id),
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "total_points": c.total_points,
            "model_provider": c.model_provider,
            "model_name": c.model_name,
            "prompt_tokens": c.prompt_tokens,
            "completion_tokens": c.completion_tokens,
            "user_id": c.user_id,
            "username": username,
            "enterprise_id": user.enterprise_id if user else None,
            "enterprise_name": enterprise_name
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/point-transactions")
async def get_all_point_transactions(
    page: int = 1,
    page_size: int = 20,
    enterprise_id: Optional[str] = None,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取所有充值记录（管理员）"""
    if page_size > 100:
        page_size = 100

    point_service = PointService(db)
    transactions, total = point_service.get_all_transactions(
        page=page,
        page_size=page_size,
        enterprise_id=enterprise_id
    )

    # 获取企业名称和操作人信息
    from src.db_models import EnterpriseModel, UserModel
    enterprise_ids = list(set([t.enterprise_id for t in transactions if t.enterprise_id]))
    operator_ids = list(set([t.operator_id for t in transactions if t.operator_id]))

    enterprises_map = {}
    if enterprise_ids:
        enterprises = db.query(EnterpriseModel).filter(EnterpriseModel.id.in_(enterprise_ids)).all()
        enterprises_map = {e.id: e.name for e in enterprises}

    operators_map = {}
    if operator_ids:
        operators = db.query(UserModel).filter(UserModel.user_id.in_(operator_ids)).all()
        operators_map = {u.user_id: u.username for u in operators}

    # 转换为响应格式
    items = []
    for t in transactions:
        source_type_label = {
            'offline_payment': '线下支付',
            'online_payment': '线上支付',
            'admin_gift': '赠送',
            'admin_adjust': '管理员调整'
        }.get(t.source_type, t.source_type)

        items.append({
            "id": str(t.id),
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "amount": t.amount,
            "source_type": t.source_type,
            "source_type_label": source_type_label,
            "remark": t.remark,
            "enterprise_id": t.enterprise_id,
            "enterprise_name": enterprises_map.get(t.enterprise_id) or "-",
            "operator_id": t.operator_id,
            "operator_name": operators_map.get(t.operator_id) or "-"
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{enterprise_id}", response_model=EnterpriseInfo)
async def get_enterprise(
    enterprise_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取企业详情"""
    service = EnterpriseService(db)
    enterprise = service.get_enterprise_by_id(enterprise_id)
    if not enterprise:
        raise HTTPException(status_code=404, detail="企业不存在")
    return _model_to_response(enterprise)


@router.patch("/{enterprise_id}", response_model=EnterpriseInfo)
async def update_enterprise(
    enterprise_id: str,
    request: UpdateEnterpriseRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新企业信息"""
    service = EnterpriseService(db)
    enterprise = service.update_enterprise(
        enterprise_id,
        name=request.name,
        status=request.status
    )
    if not enterprise:
        raise HTTPException(status_code=404, detail="企业不存在")
    return _model_to_response(enterprise)


@router.delete("/{enterprise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_enterprise(
    enterprise_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除企业"""
    service = EnterpriseService(db)
    try:
        success = service.delete_enterprise(enterprise_id)
        if not success:
            raise HTTPException(status_code=404, detail="企业不存在")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{enterprise_id}/add-points")
async def add_points_to_enterprise(
    enterprise_id: str,
    request: AddPointsRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """手动增加积分（充值/赠送）"""
    point_service = PointService(db)
    try:
        transaction = point_service.add_points(
            enterprise_id=enterprise_id,
            amount=request.amount,
            source_type=request.source_type,
            operator_id=current_user.user_id,
            remark=request.remark
        )
        return {"message": "积分增加成功", "transaction_id": str(transaction.id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{enterprise_id}/consumptions")
async def get_enterprise_consumptions(
    enterprise_id: str,
    page: int = 1,
    page_size: int = 20,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取企业消费记录"""
    if page_size > 100:
        page_size = 100

    point_service = PointService(db)
    consumptions, total = point_service.get_consumptions(
        enterprise_id=enterprise_id,
        page=page,
        page_size=page_size
    )

    # 转换为响应格式
    items = []
    for c in consumptions:
        # 获取用户名
        from src.db_models import UserModel
        user = db.query(UserModel).filter(UserModel.user_id == c.user_id).first()
        username = user.username if user else "未知用户"

        items.append({
            "id": str(c.id),
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "points": c.total_points,
            "model_provider": c.model_provider,
            "model_name": c.model_name,
            "prompt_tokens": c.prompt_tokens,
            "completion_tokens": c.completion_tokens,
            "user_id": c.user_id,
            "username": username
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }
