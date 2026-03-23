# -*- coding: utf-8 -*-
"""消费记录路由（企业后台）"""
import logging
from typing import Annotated, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from src.models import UserInfo, ConsumptionListResponse, ConsumptionItem
from src.database import get_db
from src.interfaces.dependencies import require_enterprise_admin
from src.services.point_service import PointService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consumptions", tags=["企业-消费记录"])


@router.get("", response_model=ConsumptionListResponse)
async def get_consumptions(
    page: int = 1,
    page_size: int = 20,
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取 AI 消费记录"""
    if page_size > 100:
        page_size = 100

    point_service = PointService(db)
    consumptions, total = point_service.get_consumptions(
        current_user.enterprise_id, page, page_size, user_id, start_date, end_date
    )

    items = [
        ConsumptionItem(
            id=str(c.id),
            user_id=c.user_id,
            username=None,  # TODO: 关联查询用户名
            model_provider=c.model_provider,
            model_name=c.model_name,
            prompt_tokens=c.prompt_tokens,
            completion_tokens=c.completion_tokens,
            total_tokens=c.total_tokens,
            gratis_points_used=c.gratis_points_used,
            paid_points_used=c.paid_points_used,
            total_points=c.total_points,
            created_at=c.created_at
        )
        for c in consumptions
    ]

    return ConsumptionListResponse(
        consumptions=items,
        total=total,
        page=page
    )


@router.get("/stats")
async def get_consumption_stats(
    days: int = 30,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取消费统计数据"""
    from src.db_models import AIConsumptionModel
    from sqlalchemy import func, extract
    from datetime import timedelta

    if days > 365:
        days = 365

    start_date = datetime.now() - timedelta(days=days)

    # 获取趋势数据（按日期分组）
    trend_query = db.query(
        func.date(AIConsumptionModel.created_at).label('date'),
        func.sum(AIConsumptionModel.total_points).label('points')
    ).filter(
        AIConsumptionModel.enterprise_id == current_user.enterprise_id,
        AIConsumptionModel.created_at >= start_date
    ).group_by(
        func.date(AIConsumptionModel.created_at)
    ).order_by(
        func.date(AIConsumptionModel.created_at)
    )

    trend_data = [
        {"date": str(row.date), "points": row.points or 0}
        for row in trend_query.all()
    ]

    # 获取模型分布数据
    model_query = db.query(
        AIConsumptionModel.model_name,
        func.sum(AIConsumptionModel.total_points).label('points')
    ).filter(
        AIConsumptionModel.enterprise_id == current_user.enterprise_id
    ).group_by(
        AIConsumptionModel.model_name
    ).order_by(
        func.sum(AIConsumptionModel.total_points).desc()
    )

    model_data = [
        {"name": row.model_name, "value": row.points or 0}
        for row in model_query.all()
    ]

    return {
        "trend": trend_data,
        "model_distribution": model_data
    }
