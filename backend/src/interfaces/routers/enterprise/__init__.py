# -*- coding: utf-8 -*-
"""企业后台路由"""
from fastapi import APIRouter, HTTPException, Depends
from . import users, points, consumptions
from src.interfaces.dependencies import require_enterprise_admin
from src.models import UserInfo, EnterpriseInfo
from src.database import get_db
from sqlalchemy.orm import Session
from typing import Annotated

router = APIRouter(prefix="/api/v1/enterprise", tags=["企业后台"])
# 注意：子路由不应该包含父路由前缀，否则会重复
router.include_router(points.router)
router.include_router(users.router)
router.include_router(consumptions.router)


@router.get("/enterprises/my", response_model=EnterpriseInfo)
async def get_my_enterprise(
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取当前用户所属企业信息"""
    from src.services.enterprise_service import EnterpriseService
    from src.interfaces.routers.admin.enterprises import _model_to_response

    service = EnterpriseService(db)
    enterprise = service.get_enterprise_by_id(current_user.enterprise_id)

    if not enterprise:
        raise HTTPException(status_code=404, detail="企业不存在")

    return _model_to_response(enterprise)


@router.get("/enterprises/{enterprise_id}", response_model=EnterpriseInfo)
async def get_enterprise(
    enterprise_id: str,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取企业信息（验证用户属于该企业）"""
    from src.services.enterprise_service import EnterpriseService
    from src.interfaces.routers.admin.enterprises import _model_to_response

    # 验证用户是否属于该企业
    if current_user.enterprise_id != enterprise_id:
        raise HTTPException(status_code=403, detail="无权访问其他企业信息")

    service = EnterpriseService(db)
    enterprise = service.get_enterprise_by_id(enterprise_id)

    if not enterprise:
        raise HTTPException(status_code=404, detail="企业不存在")

    return _model_to_response(enterprise)


@router.get("/enterprises/{enterprise_id}/transactions")
async def get_enterprise_transactions(
    enterprise_id: str,
    page: int = 1,
    page_size: int = 20,
    source_type: str = None,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取企业交易记录（验证用户属于该企业）"""
    from src.services.point_service import PointService
    from src.models import PointSourceType

    # 验证用户是否属于该企业
    if current_user.enterprise_id != enterprise_id:
        raise HTTPException(status_code=403, detail="无权访问其他企业信息")

    if page_size > 100:
        page_size = 100

    point_service = PointService(db)
    transactions, total = point_service.get_transactions(
        enterprise_id, page, page_size
    )

    # 过滤 source_type
    if source_type:
        from src.db_models import PointTransactionModel
        # 使用 .value 比较，因为 t.source_type 是枚举实例，source_type 是字符串
        transactions = [t for t in transactions if t.source_type.value == source_type]
        total = len(transactions)

    # 获取操作人信息
    from src.db_models import UserModel
    operator_ids = list(set([t.operator_id for t in transactions if t.operator_id]))

    operators_map = {}
    if operator_ids:
        operators = db.query(UserModel).filter(UserModel.user_id.in_(operator_ids)).all()
        operators_map = {u.user_id: u.username for u in operators}

    items = []
    for t in transactions:
        source_type_label = {
            'offline_payment': '线下支付',
            'online_payment': '线上支付',
            'admin_gift': '赠送',
            'admin_adjust': '管理员调整'
        }.get(t.source_type.value if hasattr(t.source_type, 'value') else t.source_type, str(t.source_type))

        # 转换充值金额（分 -> 元）
        payment_amount_yuan = None
        if t.payment_amount:
            payment_amount_yuan = t.payment_amount / 100

        items.append({
            "id": str(t.id),
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "type": t.type,
            "source_type": t.source_type,
            "source_type_label": source_type_label,
            "amount": t.amount,
            "balance_before": t.balance_before,
            "balance_after": t.balance_after,
            "payment_amount": payment_amount_yuan,  # 充值金额（元）
            "operator_id": t.operator_id,
            "operator_name": operators_map.get(t.operator_id) or "-",
            "remark": t.remark
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }
