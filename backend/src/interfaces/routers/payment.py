# -*- coding: utf-8 -*-
"""支付 API 路由"""
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.orm import Session

from src.database import get_db
from src.interfaces.dependencies import get_current_user
from src.models import (
    UserInfo,
    CreatePaymentOrderRequest,
    PaymentOrderResponse,
    RechargeListResponse,
    PaymentOrderStatus,
)
from src.db_models import PaymentOrderModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payment", tags=["payment"])


def get_icbc_client():
    """获取工行客户端实例"""
    from src.services.icbc_client import IcbcClient
    import os

    return IcbcClient(
        app_id=os.getenv("ICBC_APP_ID", ""),
        mer_id=os.getenv("ICBC_MER_ID", ""),
        mer_prtcl_no=os.getenv("ICBC_MER_PRTCL_NO", ""),
        private_key=os.getenv("ICBC_PRIVATE_KEY", ""),
        public_key=os.getenv("ICBC_PUBLIC_KEY", ""),
        device_info=os.getenv("ICBC_DEVICE_INFO", ""),
        notify_url=os.getenv("ICBC_NOTIFY_URL", ""),
    )


def get_payment_service(db: Session = Depends(get_db)) -> "PaymentService":
    """获取支付服务实例"""
    from src.services.payment_service import PaymentService
    from src.services.point_service import PointService

    icbc_client = get_icbc_client()
    point_service = PointService(db)
    return PaymentService(db, icbc_client, point_service)


@router.post("/create-order", response_model=PaymentOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_order(
    request_data: CreatePaymentOrderRequest,
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    payment_service=Depends(get_payment_service),
):
    """
    创建支付订单

    Args:
        request_data: 支付订单请求
        current_user: 当前登录用户
        payment_service: 支付服务

    Returns:
        支付订单响应

    Raises:
        HTTPException: 创建订单失败
    """
    try:
        result = await payment_service.create_payment_order(
            user_id=current_user.user_id,
            amount=request_data.amount,
            body="积分充值",
            expire_time=900,  # 15分钟
        )

        # 查询订单详情返回
        order = payment_service.db.query(PaymentOrderModel).filter(
            PaymentOrderModel.id == result["order_id"]
        ).first()

        return PaymentOrderResponse.model_validate(order)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建支付订单失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建支付订单失败"
        )


@router.get("/order/{order_id}", response_model=PaymentOrderResponse)
async def query_payment_order(
    order_id: str,
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    payment_service=Depends(get_payment_service),
):
    """
    查询支付订单状态

    Args:
        order_id: 订单ID
        current_user: 当前登录用户
        payment_service: 支付服务

    Returns:
        支付订单响应

    Raises:
        HTTPException: 订单不存在或无权访问
    """
    order = payment_service.db.query(PaymentOrderModel).filter(
        PaymentOrderModel.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    # 验证订单归属
    if order.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该订单"
        )

    # 主动查询支付状态
    try:
        await payment_service.query_payment_status(order_id)
        # 刷新订单数据
        payment_service.db.refresh(order)
    except Exception as e:
        logger.error(f"查询支付状态失败: {e}", exc_info=True)

    return PaymentOrderResponse.model_validate(order)


@router.get("/my-recharges", response_model=RechargeListResponse)
async def get_my_recharges(
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    payment_service=Depends(get_payment_service),
    page: int = 1,
    page_size: int = 20,
):
    """
    获取我的充值记录

    Args:
        current_user: 当前登录用户
        payment_service: 支付服务
        page: 页码
        page_size: 每页数量

    Returns:
        充值记录列表响应
    """
    orders, total = payment_service.get_recharge_records(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )

    # 计算积分
    points_per_yuan = payment_service._get_points_per_yuan()

    items = []
    for order in orders:
        # 计算积分
        points = (order.amount // 100) * points_per_yuan

        items.append({
            "id": order.id,
            "amount": order.amount,
            "points": points,
            "created_at": order.created_at,
        })

    return RechargeListResponse(items=items, total=total)


@router.post("/icbc/notify")
async def icbc_notify(
    request: Request,
    payment_service=Depends(get_payment_service),
):
    """
    处理工行支付回调

    Args:
        request: FastAPI 请求对象
        payment_service: 支付服务

    Returns:
        工行要求的标准响应
    """
    try:
        # 获取回调数据
        if request.headers.get("content-type", "").startswith("application/json"):
            notify_data = await request.json()
        else:
            from fastapi.datastructures import FormData
            form_data: FormData = await request.form()
            notify_data = dict(form_data)

        logger.info(f"收到工行支付回调: {notify_data}")

        # 验签并处理
        success = await payment_service.handle_notify(notify_data)

        if success:
            # 返回工行要求的标准响应
            return {"return_code": "0", "return_msg": "成功"}
        else:
            return {"return_code": "1", "return_msg": "失败"}

    except Exception as e:
        logger.error(f"处理工行回调失败: {e}", exc_info=True)
        return {"return_code": "1", "return_msg": "系统异常"}
