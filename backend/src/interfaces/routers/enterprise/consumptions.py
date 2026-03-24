# -*- coding: utf-8 -*-
"""消费记录路由（企业后台）"""
import logging
import csv
import io
from typing import Annotated, Optional
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.models import (
    UserInfo, ConsumptionListResponse, ConsumptionItem, ConsumptionStats
)
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
    model_name: Optional[str] = None,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取 AI 消费记录"""
    from src.db_models import AIConsumptionModel, UserModel

    if page_size > 100:
        page_size = 100

    point_service = PointService(db)
    consumptions, total = point_service.get_consumptions(
        current_user.enterprise_id, page, page_size, user_id, start_date, end_date
    )

    # 获取用户ID列表，批量查询用户信息
    user_ids = [c.user_id for c in consumptions]
    users_map = {}
    if user_ids:
        users = db.query(UserModel).filter(UserModel.user_id.in_(user_ids)).all()
        users_map = {u.user_id: u for u in users}

    # 计算统计数据
    stats = _calculate_consumption_stats(db, current_user.enterprise_id)

    items = [
        ConsumptionItem(
            id=str(c.id),
            user_id=c.user_id,
            username=users_map.get(c.user_id).username if c.user_id in users_map else None,
            nickname=users_map.get(c.user_id).nickname if c.user_id in users_map else None,
            model_provider=c.model_provider,
            model_name=c.model_name,
            prompt_tokens=c.prompt_tokens,
            completion_tokens=c.completion_tokens,
            total_tokens=c.total_tokens,
            gratis_points_used=c.gratis_points_used,
            paid_points_used=c.paid_points_used,
            total_points=c.total_points,
            points=c.total_points,  # 前端使用的字段
            created_at=c.created_at
        )
        for c in consumptions
    ]

    return ConsumptionListResponse(
        items=items,
        total=total,
        page=page,
        stats=stats
    )


@router.get("/models")
async def get_consumption_models(
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取消费记录中使用过的模型列表"""
    from src.db_models import AIConsumptionModel
    from sqlalchemy import distinct

    models = db.query(distinct(AIConsumptionModel.model_name)).filter(
        AIConsumptionModel.enterprise_id == current_user.enterprise_id
    ).order_by(AIConsumptionModel.model_name).all()

    return {"models": [m[0] for m in models if m[0]]}


@router.get("/export")
async def export_consumptions(
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    model_name: Optional[str] = None,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """导出消费记录为 CSV"""
    from src.db_models import AIConsumptionModel, UserModel

    # 构建查询
    query = db.query(AIConsumptionModel).filter(
        AIConsumptionModel.enterprise_id == current_user.enterprise_id
    )

    if user_id:
        query = query.filter(AIConsumptionModel.user_id == user_id)
    if start_date:
        query = query.filter(AIConsumptionModel.created_at >= start_date)
    if end_date:
        query = query.filter(AIConsumptionModel.created_at <= end_date)
    if model_name:
        query = query.filter(AIConsumptionModel.model_name == model_name)

    consumptions = query.order_by(AIConsumptionModel.created_at.desc()).all()

    # 获取用户信息
    user_ids = list(set([c.user_id for c in consumptions]))
    users_map = {}
    if user_ids:
        users = db.query(UserModel).filter(UserModel.user_id.in_(user_ids)).all()
        users_map = {u.user_id: u for u in users}

    # 创建 CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # 写入 BOM 以支持 Excel 打开中文
    output.seek(0)
    output.truncate()

    # 写入表头
    writer.writerow([
        "时间", "用户名", "昵称", "消耗积分", "供应商", "模型",
        "输入Token", "输出Token", "总Token", "赠送积分", "充值积分"
    ])

    # 写入数据
    for c in consumptions:
        user = users_map.get(c.user_id)
        writer.writerow([
            c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else "",
            user.username if user else "",
            user.nickname if user else "",
            c.total_points,
            c.model_provider,
            c.model_name,
            c.prompt_tokens,
            c.completion_tokens,
            c.total_tokens,
            c.gratis_points_used,
            c.paid_points_used
        ])

    # 生成带 BOM 的 UTF-8 内容
    csv_content = output.getvalue()
    csv_bytes = '\ufeff' + csv_content  # 添加 BOM

    return StreamingResponse(
        io.BytesIO(csv_bytes.encode('utf-8')),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=consumptions_{date.today()}.csv"
        }
    )


@router.get("/stats")
async def get_consumption_stats(
    days: int = 30,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取消费统计数据（图表用）"""
    from src.db_models import AIConsumptionModel
    from sqlalchemy import func
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


def _calculate_consumption_stats(db: Session, enterprise_id: str) -> ConsumptionStats:
    """计算消费统计数据"""
    from src.db_models import AIConsumptionModel
    from sqlalchemy import func

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 今日消耗
    today_result = db.query(func.sum(AIConsumptionModel.total_points)).filter(
        AIConsumptionModel.enterprise_id == enterprise_id,
        AIConsumptionModel.created_at >= today_start
    ).scalar()
    today_consumed = today_result or 0

    # 本月消耗
    month_result = db.query(func.sum(AIConsumptionModel.total_points)).filter(
        AIConsumptionModel.enterprise_id == enterprise_id,
        AIConsumptionModel.created_at >= month_start
    ).scalar()
    month_consumed = month_result or 0

    # 总消耗
    total_result = db.query(func.sum(AIConsumptionModel.total_points)).filter(
        AIConsumptionModel.enterprise_id == enterprise_id
    ).scalar()
    total_consumed = total_result or 0

    return ConsumptionStats(
        today_consumed=today_consumed,
        month_consumed=month_consumed,
        total_consumed=total_consumed
    )
