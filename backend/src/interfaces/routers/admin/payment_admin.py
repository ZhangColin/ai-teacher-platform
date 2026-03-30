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
    CreateRefundRequest,
)
from src.db_models import PaymentOrderModel, SystemConfigModel, PointTransactionModel, PaymentRefundModel, RefundStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/payment", tags=["admin-payment"])


def get_payment_service(db: Session = Depends(get_db)) -> "PaymentService":
    """获取支付服务实例"""
    from src.services.payment_service import PaymentService
    from src.services.point_service import PointService
    from src.services.icbc_qrcode_client import IcbcQrCodeClient
    from src.config.icbc_config import get_icbc_client_config

    config = get_icbc_client_config()
    icbc_client = IcbcQrCodeClient(
        app_id=config["app_id"],
        mer_id=config["mer_id"],
        mer_prtcl_no=config["mer_prtcl_no"],
        access_type=config["access_type"],
        cur_type=config["cur_type"],
        goods_name=config["goods_name"],
        body=config["body"],
        notify_type=config["notify_type"],
        result_type=config["result_type"],
        notify_url=config["notify_url"],
        private_key_pem=config["private_key_pem"],
        public_key_pem=config["public_key_pem"],
    )
    point_service = PointService(db)
    return PaymentService(db, icbc_client, point_service)


def get_refund_service(db: Session = Depends(get_db)) -> "RefundService":
    """获取退款服务实例"""
    from src.services.refund_service import RefundService
    from src.services.icbc_qrcode_client import IcbcQrCodeClient
    from src.config.icbc_config import get_icbc_client_config

    config = get_icbc_client_config()
    icbc_client = IcbcQrCodeClient(
        app_id=config["app_id"],
        mer_id=config["mer_id"],
        mer_prtcl_no=config["mer_prtcl_no"],
        access_type=config["access_type"],
        cur_type=config["cur_type"],
        goods_name=config["goods_name"],
        body=config["body"],
        notify_type=config["notify_type"],
        result_type=config["result_type"],
        notify_url=config["notify_url"],
        private_key_pem=config["private_key_pem"],
        public_key_pem=config["public_key_pem"],
    )
    return RefundService(db, icbc_client)


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


# ==================== 退款管理接口 ====================

@router.get("/refunds")
async def list_refunds(
    current_user: Annotated[UserInfo, Depends(require_admin)],
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
    status: str = None,
    out_trade_no: str = None,
    out_refund_no: str = None,
):
    """
    获取退款订单列表（管理员）

    Args:
        current_user: 当前管理员用户
        db: 数据库会话
        page: 页码
        page_size: 每页数量
        status: 状态筛选
        out_trade_no: 商户订单号筛选
        out_refund_no: 退款流水号筛选

    Returns:
        退款订单列表响应
    """
    from src.services.refund_service import RefundService
    from src.services.icbc_qrcode_client import IcbcQrCodeClient
    from src.config.icbc_config import get_icbc_client_config

    config = get_icbc_client_config()
    icbc_client = IcbcQrCodeClient(
        app_id=config["app_id"],
        mer_id=config["mer_id"],
        mer_prtcl_no=config["mer_prtcl_no"],
        access_type=config["access_type"],
        cur_type=config["cur_type"],
        goods_name=config["goods_name"],
        body=config["body"],
        notify_type=config["notify_type"],
        result_type=config["result_type"],
        notify_url=config["notify_url"],
        private_key_pem=config["private_key_pem"],
        public_key_pem=config["public_key_pem"],
    )
    refund_service = RefundService(db, icbc_client)

    refunds, total = refund_service.list_refunds(
        page=page,
        page_size=page_size,
        status=status,
        out_trade_no=out_trade_no,
        out_refund_no=out_refund_no,
    )

    # 构建响应列表
    items = []
    for refund in refunds:
        # 获取关联的支付订单号
        payment_order = db.query(PaymentOrderModel).filter(
            PaymentOrderModel.id == refund.payment_order_id
        ).first()

        item = {
            "id": refund.id,
            "out_refund_no": refund.out_refund_no,
            "payment_order_id": refund.payment_order_id,
            "payment_order_out_trade_no": payment_order.out_trade_no if payment_order else None,
            "refund_amount": refund.refund_amount,
            "real_refund_amount": refund.real_refund_amount,
            "status": refund.status.value if isinstance(refund.status, RefundStatus) else refund.status,
            "third_refund_no": refund.third_refund_no,
            "operator_id": refund.operator_id,
            "operator_name": refund.operator_name,
            "refund_reason": refund.refund_reason,
            "submitted_at": refund.submitted_at.isoformat() if refund.submitted_at else None,
            "success_at": refund.success_at.isoformat() if refund.success_at else None,
            "failed_at": refund.failed_at.isoformat() if refund.failed_at else None,
            "created_at": refund.created_at.isoformat(),
        }
        items.append(item)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/refunds/{refund_id}")
async def get_refund_detail(
    refund_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)],
    refund_service=Depends(get_refund_service),
):
    """
    获取退款订单详情（管理员）

    Args:
        refund_id: 退款订单ID
        current_user: 当前管理员用户
        refund_service: 退款服务

    Returns:
        退款订单详情
    """
    from sqlalchemy.orm import Session

    refund = refund_service.get_refund_by_id(refund_id)
    if not refund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"退款订单不存在: {refund_id}"
        )

    # 获取关联的支付订单
    db: Session = refund_service.db
    payment_order = db.query(PaymentOrderModel).filter(
        PaymentOrderModel.id == refund.payment_order_id
    ).first()

    return {
        "id": refund.id,
        "out_refund_no": refund.out_refund_no,
        "payment_order_id": refund.payment_order_id,
        "payment_order_out_trade_no": payment_order.out_trade_no if payment_order else None,
        "payment_order_amount": payment_order.amount if payment_order else None,
        "refund_amount": refund.refund_amount,
        "real_refund_amount": refund.real_refund_amount,
        "status": refund.status.value if isinstance(refund.status, RefundStatus) else refund.status,
        "third_refund_no": refund.third_refund_no,
        "icbc_refund_response": refund.icbc_refund_response,
        "icbc_query_response": refund.icbc_query_response,
        "operator_id": refund.operator_id,
        "operator_name": refund.operator_name,
        "refund_reason": refund.refund_reason,
        "submitted_at": refund.submitted_at.isoformat() if refund.submitted_at else None,
        "success_at": refund.success_at.isoformat() if refund.success_at else None,
        "failed_at": refund.failed_at.isoformat() if refund.failed_at else None,
        "created_at": refund.created_at.isoformat(),
        "updated_at": refund.updated_at.isoformat(),
    }


@router.post("/refunds/create")
async def create_refund(
    request_data: CreateRefundRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)],
    refund_service=Depends(get_refund_service),
):
    """
    发起退款（管理员）

    Args:
        request_data: 创建退款请求
        current_user: 当前管理员用户
        refund_service: 退款服务

    Returns:
        创建的退款订单
    """
    logger.info(f"管理员 {current_user.username} 发起退款: 订单={request_data.payment_order_id}, 金额={request_data.refund_amount}")

    refund = await refund_service.create_refund(
        payment_order_id=request_data.payment_order_id,
        refund_amount=request_data.refund_amount,
        operator_id=current_user.user_id,
        operator_name=current_user.nickname or current_user.username,
        refund_reason=request_data.refund_reason,
    )

    return {
        "id": refund.id,
        "out_refund_no": refund.out_refund_no,
        "payment_order_id": refund.payment_order_id,
        "refund_amount": refund.refund_amount,
        "status": refund.status.value if isinstance(refund.status, RefundStatus) else refund.status,
        "created_at": refund.created_at.isoformat(),
    }


@router.post("/refunds/{refund_id}/query")
async def query_refund_status(
    refund_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)],
    refund_service=Depends(get_refund_service),
):
    """
    查询退款状态（管理员）

    Args:
        refund_id: 退款订单ID
        current_user: 当前管理员用户
        refund_service: 退款服务

    Returns:
        更新后的退款订单
    """
    logger.info(f"管理员 {current_user.username} 查询退款状态: {refund_id}")

    refund = await refund_service.query_refund_status(refund_id)

    return {
        "id": refund.id,
        "out_refund_no": refund.out_refund_no,
        "status": refund.status.value if isinstance(refund.status, RefundStatus) else refund.status,
        "real_refund_amount": refund.real_refund_amount,
        "third_refund_no": refund.third_refund_no,
        "success_at": refund.success_at.isoformat() if refund.success_at else None,
        "failed_at": refund.failed_at.isoformat() if refund.failed_at else None,
        # 添加工行响应数据
        "icbc_refund_response": refund.icbc_refund_response,
        "icbc_query_response": refund.icbc_query_response,
    }


@router.get("/orders/{order_id}/refunds")
async def get_payment_order_refunds(
    order_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """
    获取支付订单的退款记录（管理员）

    Args:
        order_id: 支付订单ID
        current_user: 当前管理员用户
        db: 数据库会话

    Returns:
        退款记录列表
    """
    refunds = db.query(PaymentRefundModel).filter(
        PaymentRefundModel.payment_order_id == order_id
    ).order_by(PaymentRefundModel.created_at.desc()).all()

    items = []
    for refund in refunds:
        items.append({
            "id": refund.id,
            "out_refund_no": refund.out_refund_no,
            "refund_amount": refund.refund_amount,
            "real_refund_amount": refund.real_refund_amount,
            "status": refund.status.value if isinstance(refund.status, RefundStatus) else refund.status,
            "operator_name": refund.operator_name,
            "refund_reason": refund.refund_reason,
            "created_at": refund.created_at.isoformat(),
            "success_at": refund.success_at.isoformat() if refund.success_at else None,
        })

    return {"items": items}
