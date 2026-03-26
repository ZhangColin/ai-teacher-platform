# -*- coding: utf-8 -*-
"""支付 API 路由"""
import json
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.responses import JSONResponse
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

router = APIRouter(prefix="/api/v1/payment", tags=["payment"])


def get_icbc_client() -> "IcbcQrCodeClient":
    """获取工行客户端实例"""
    from src.services.icbc_qrcode_client import IcbcQrCodeClient
    from src.config.icbc_config import get_icbc_client_config

    config = get_icbc_client_config()
    return IcbcQrCodeClient(**config)


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
    db: Session = Depends(get_db),
    icbc_client: "IcbcQrCodeClient" = Depends(get_icbc_client),
):
    """
    工行支付回调接口

    工行支付网关在支付完成后会调用此接口通知支付结果
    """
    from urllib.parse import parse_qs
    from src.services.payment_service import PaymentService

    # 1. 获取回调参数（URL参数编码格式）
    body = await request.body()
    params = parse_qs(body.decode('utf-8'))

    # 将参数列表转换为单值（parse_qs 返回的是列表）
    notify_data = {k: v[0] if v else "" for k, v in params.items()}

    logger.info(f"收到工行支付回调: {notify_data}")

    # 2. 验签
    if not icbc_client.verify_notify(notify_data):
        logger.error("支付回调验签失败")
        raise HTTPException(status_code=400, detail="签名验证失败")

    # 3. 解析 biz_content
    try:
        biz_content_str = notify_data.get("biz_content", "{}")
        biz_content = json.loads(biz_content_str)
    except json.JSONDecodeError as e:
        logger.error(f"回调 biz_content 解析失败: {e}")
        raise HTTPException(status_code=400, detail="回调数据格式错误")

    # 4. 处理支付结果
    payment_service = PaymentService(db, icbc_client, None)  # point_service 暂时为None
    success = await payment_service.handle_notify(biz_content)

    if not success:
        logger.error("支付回调处理失败")
        raise HTTPException(status_code=500, detail="处理失败")

    # 5. 返回指定格式响应
    msg_id = notify_data.get("msg_id", "")
    response = icbc_client.sign_notify_response(0, msg_id)

    return JSONResponse(content=response)


@router.get("/config")
async def get_payment_config(db: Session = Depends(get_db)):
    """
    获取支付配置（用户端）

    返回积分兑换比例等公开配置信息
    """
    from src.db_models import SystemConfigModel

    config = db.query(SystemConfigModel).filter(
        SystemConfigModel.key == "points_per_yuan"
    ).first()

    points_per_yuan = 100  # 默认值
    if config:
        try:
            points_per_yuan = int(config.value)
        except (ValueError, TypeError):
            pass

    return {
        "points_per_yuan": points_per_yuan
    }
