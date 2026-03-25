# -*- coding: utf-8 -*-
"""管理员支付 API 路由"""
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.interfaces.dependencies import require_admin
from src.models import (
    UserInfo,
    PaymentOrderResponse,
    SystemConfigResponse,
    UpdateSystemConfigRequest,
    TestNotifyRequest,
)
from src.db_models import PaymentOrderModel, SystemConfigModel, PointTransactionModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/payment", tags=["admin-payment"])


def get_payment_service(db: Session = Depends(get_db)) -> "PaymentService":
    """获取支付服务实例"""
    from src.services.payment_service import PaymentService
    from src.services.point_service import PointService
    from src.services.icbc_client import IcbcClient
    import os

    icbc_client = IcbcClient(
        app_id=os.getenv("ICBC_APP_ID", ""),
        mer_id=os.getenv("ICBC_MER_ID", ""),
        mer_prtcl_no=os.getenv("ICBC_MER_PRTCL_NO", ""),
        private_key=os.getenv("ICBC_MY_PRIVATE_KEY", ""),
        public_key=os.getenv("ICBC_APIGW_PUBLIC_KEY", ""),
        device_info=os.getenv("ICBC_DEVICE_INFO", ""),
        notify_url=os.getenv("ICBC_NOTIFY_URL", ""),
    )
    point_service = PointService(db)
    return PaymentService(db, icbc_client, point_service)


@router.get("/orders")
async def list_all_orders(
    current_user: Annotated[UserInfo, Depends(require_admin)],
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
    status_filter: str = None,
):
    """
    获取所有支付订单（管理员）

    Args:
        current_user: 当前管理员用户
        db: 数据库会话
        page: 页码
        page_size: 每页数量
        status_filter: 状态筛选

    Returns:
        订单列表响应
    """
    query = db.query(PaymentOrderModel)

    if status_filter:
        query = query.filter(PaymentOrderModel.status == status_filter)

    total = query.count()

    orders = query.order_by(
        PaymentOrderModel.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    items = [PaymentOrderResponse.model_validate(order) for order in orders]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/config", response_model=SystemConfigResponse)
async def get_payment_config(
    current_user: Annotated[UserInfo, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """
    获取支付配置（管理员）

    Args:
        current_user: 当前管理员用户
        db: 数据库会话

    Returns:
        系统配置响应
    """
    config = db.query(SystemConfigModel).filter(
        SystemConfigModel.key == "points_per_yuan"
    ).first()

    if not config:
        # 返回默认值
        return SystemConfigResponse(
            key="points_per_yuan",
            value="100",
            description="1元对应的积分数量"
        )

    return SystemConfigResponse.model_validate(config)


@router.post("/config", response_model=SystemConfigResponse)
async def update_payment_config(
    request_data: UpdateSystemConfigRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """
    更新支付配置（管理员）

    Args:
        request_data: 更新配置请求
        current_user: 当前管理员用户
        db: 数据库会话

    Returns:
        系统配置响应
    """
    config = db.query(SystemConfigModel).filter(
        SystemConfigModel.key == "points_per_yuan"
    ).first()

    if config:
        config.value = str(request_data.points_per_yuan)
    else:
        config = SystemConfigModel(
            key="points_per_yuan",
            value=str(request_data.points_per_yuan),
            description="1元对应的积分数量"
        )
        db.add(config)

    db.commit()
    db.refresh(config)

    logger.info(f"管理员 {current_user.username} 更新支付配置: points_per_yuan={request_data.points_per_yuan}")

    return SystemConfigResponse.model_validate(config)


@router.post("/test-notify")
async def test_notify(
    request_data: TestNotifyRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)],
    payment_service=Depends(get_payment_service),
):
    """
    测试支付回调（管理员）

    Args:
        request_data: 测试回调请求
        current_user: 当前管理员用户
        payment_service: 支付服务

    Returns:
        处理结果
    """
    # 构造模拟的工行回调数据
    notify_data = {
        "return_code": request_data.return_code,
        "return_msg": "成功" if request_data.return_code == "0" else "失败",
        "out_trade_no": request_data.out_trade_no,
        "trade_status": "1" if request_data.return_code == "0" else "2",
        "total_amt": request_data.total_amt,
    }

    if request_data.third_trade_no:
        notify_data["trade_no"] = request_data.third_trade_no

    logger.info(f"管理员 {current_user.username} 测试支付回调: {notify_data}")

    # 跳过验签，直接处理
    order = payment_service.db.query(PaymentOrderModel).filter(
        PaymentOrderModel.out_trade_no == request_data.out_trade_no
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"订单不存在: {request_data.out_trade_no}"
        )

    # 防止重复处理
    if order.status == "paid":
        return {
            "success": True,
            "message": "订单已支付，跳过处理",
            "order_id": order.id
        }

    # 更新订单状态
    from src.db_models import PaymentOrderStatus
    if request_data.return_code == "0":
        order.status = PaymentOrderStatus.paid
        order.notify_verify_result = True
        order.notify_data = notify_data

        # 计算并增加积分
        points = payment_service._calculate_points(order.amount)
        from src.db_models import PointSourceType
        from src.services.point_service import PointService
        point_service = PointService(payment_service.db)

        # 获取用户企业
        enterprise = payment_service._get_user_enterprise(order.user_id)
        if enterprise:
            point_service.add_points(
                enterprise_id=enterprise.id,
                amount=points,
                source_type=PointSourceType.online_payment,
                operator_id=None,
                remark=f"测试回调充值 - 订单号:{order.out_trade_no}",
                payment_id=order.id,
                payment_amount=order.amount
            )

        payment_service.db.commit()

        return {
            "success": True,
            "message": f"测试回调处理成功，增加 {points} 积分",
            "order_id": order.id,
            "points": points
        }
    else:
        order.status = PaymentOrderStatus.failed
        payment_service.db.commit()

        return {
            "success": False,
            "message": "测试回调处理失败",
            "order_id": order.id
        }
