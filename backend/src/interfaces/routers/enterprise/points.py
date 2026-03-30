# -*- coding: utf-8 -*-
"""积分管理路由（企业后台）"""
import logging
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from src.models import UserInfo, PointBalanceResponse, TransactionListResponse, TransactionItem
from src.database import get_db
from src.interfaces.dependencies import require_enterprise_admin, require_enterprise_member
from src.services.point_service import PointService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/points", tags=["企业-积分"])


@router.get("/balance", response_model=PointBalanceResponse)
async def get_balance(
    current_user: Annotated[UserInfo, Depends(require_enterprise_member)] = None,
    db: Session = Depends(get_db)
):
    """获取企业积分余额（所有企业成员都可访问）"""
    point_service = PointService(db)
    balance = point_service.get_enterprise_balance(current_user.enterprise_id)

    if not balance:
        raise HTTPException(status_code=404, detail="企业不存在")

    return PointBalanceResponse(**balance)


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    page: int = 1,
    page_size: int = 20,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取积分交易记录"""
    if page_size > 100:
        page_size = 100

    point_service = PointService(db)
    transactions, total = point_service.get_transactions(
        current_user.enterprise_id, page, page_size
    )

    items = [
        TransactionItem(
            id=str(t.id),
            type=t.type,
            source_type=t.source_type,
            amount=t.amount,
            balance_before=t.balance_before,
            balance_after=t.balance_after,
            remark=t.remark,
            created_at=t.created_at
        )
        for t in transactions
    ]

    return TransactionListResponse(
        transactions=items,
        total=total,
        page=page
    )
