# -*- coding: utf-8 -*-
"""退款服务"""
import logging
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from src.db_models import (
    PaymentOrderModel, PaymentRefundModel, RefundStatus, PaymentOrderStatus
)

logger = logging.getLogger(__name__)


class RefundService:
    """退款服务"""

    def __init__(self, db: Session, icbc_client):
        """
        初始化退款服务

        Args:
            db: 数据库会话
            icbc_client: 工行客户端实例
        """
        self.db = db
        self.icbc_client = icbc_client

    def _generate_refund_no(self) -> str:
        """
        生成退款流水号

        格式：REF + yyyyMMddHHmmss + 8位随机数

        Returns:
            退款流水号
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = uuid.uuid4().hex[:8].upper()
        return f"REF{timestamp}{random_str}"

    def _can_refund(self, payment_order: PaymentOrderModel, refund_amount: int) -> bool:
        """
        检查是否可以退款

        Args:
            payment_order: 支付订单
            refund_amount: 退款金额（分）

        Returns:
            是否可以退款
        """
        # 检查订单状态
        if payment_order.status != PaymentOrderStatus.paid:
            logger.warning(f"订单状态不允许退款: {payment_order.status}")
            return False

        # 检查退款金额
        can_refund_amount = payment_order.amount - payment_order.refunded_amount
        if refund_amount > can_refund_amount:
            logger.warning(f"退款金额超过可退金额: 退款={refund_amount}, 可退={can_refund_amount}")
            return False

        return True

    async def create_refund(
        self,
        payment_order_id: str,
        refund_amount: int,
        operator_id: str,
        operator_name: str = "",
        refund_reason: str = "",
    ) -> PaymentRefundModel:
        """
        创建退款订单

        Args:
            payment_order_id: 支付订单ID
            refund_amount: 退款金额（分）
            operator_id: 操作人ID
            operator_name: 操作人姓名
            refund_reason: 退款原因

        Returns:
            退款订单

        Raises:
            ValueError: 订单不允许退款
            Exception: 工行接口调用失败
        """
        # 查询支付订单
        payment_order = self.db.query(PaymentOrderModel).filter(
            PaymentOrderModel.id == payment_order_id
        ).first()

        if not payment_order:
            raise ValueError(f"支付订单不存在: {payment_order_id}")

        # 检查是否可以退款
        if not self._can_refund(payment_order, refund_amount):
            raise ValueError("订单不允许退款或退款金额超过可退金额")

        # 生成退款流水号
        out_refund_no = self._generate_refund_no()

        # 创建退款订单
        refund = PaymentRefundModel(
            id=str(uuid.uuid4()),
            out_refund_no=out_refund_no,
            payment_order_id=payment_order_id,
            refund_amount=refund_amount,
            status=RefundStatus.refund_created,
            operator_id=operator_id,
            operator_name=operator_name,
            refund_reason=refund_reason,
            submitted_at=datetime.now(),
        )

        self.db.add(refund)
        self.db.flush()  # 获取 refund.id

        logger.info(f"创建退款订单: {refund.id}, 流水号: {out_refund_no}")

        try:
            # 调用工行退款接口
            icbc_response = await self.icbc_client.refund_order(
                out_trade_no=payment_order.out_trade_no,
                out_refund_no=out_refund_no,
                refund_amount=refund_amount,
                order_id=payment_order.third_trade_no,
            )

            # 保存工行响应
            refund.icbc_refund_response = icbc_response

            # 解析响应
            return_code = icbc_response.get("return_code")
            if return_code == "0":
                # 退款提交成功
                refund.status = RefundStatus.refund_processing
                refund.third_refund_no = icbc_response.get("intrx_serial_no")

                # 尝试获取实际退款金额
                if "real_reject_amt" in icbc_response:
                    try:
                        refund.real_refund_amount = int(icbc_response["real_reject_amt"])
                    except (ValueError, TypeError):
                        pass

                logger.info(f"退款提交成功: {refund.id}")
            else:
                # 退款提交失败
                refund.status = RefundStatus.refund_failed
                refund.failed_at = datetime.now()
                logger.warning(f"退款提交失败: {refund.id}, 错误码: {return_code}")

            # 更新支付订单的退款统计
            payment_order.refunded_amount += refund_amount
            payment_order.refund_count += 1

            self.db.commit()
            self.db.refresh(refund)

            return refund

        except Exception as e:
            # 回滚退款创建
            self.db.rollback()
            logger.error(f"创建退款失败: {e}")
            raise

    async def query_refund_status(self, refund_id: str) -> PaymentRefundModel:
        """
        查询退款状态

        Args:
            refund_id: 退款订单ID

        Returns:
            更新后的退款订单

        Raises:
            ValueError: 退款订单不存在
        """
        # 查询退款订单
        refund = self.db.query(PaymentRefundModel).filter(
            PaymentRefundModel.id == refund_id
        ).first()

        if not refund:
            raise ValueError(f"退款订单不存在: {refund_id}")

        # 如果已经是最终状态，不需要查询
        if refund.status in [RefundStatus.refund_success, RefundStatus.refund_cancelled]:
            return refund

        # 查询关联的支付订单
        payment_order = self.db.query(PaymentOrderModel).filter(
            PaymentOrderModel.id == refund.payment_order_id
        ).first()

        if not payment_order:
            logger.error(f"关联的支付订单不存在: {refund.payment_order_id}")
            return refund

        try:
            # 调用工行查询接口
            icbc_response = await self.icbc_client.query_refund(
                out_trade_no=payment_order.out_trade_no,
                out_refund_no=refund.out_refund_no,
                order_id=payment_order.third_trade_no,
            )

            # 保存工行响应
            refund.icbc_refund_response = icbc_response

            # 解析响应状态
            # 注意：工行查询响应可能在 response_biz_content 中
            biz_content = icbc_response.get("response_biz_content", icbc_response)
            pay_status = biz_content.get("pay_status")

            if pay_status == "0":
                # 退款成功
                refund.status = RefundStatus.refund_success
                refund.success_at = datetime.now()
                if not refund.real_refund_amount:
                    try:
                        refund.real_refund_amount = int(biz_content.get("real_reject_amt", refund.refund_amount))
                    except (ValueError, TypeError):
                        refund.real_refund_amount = refund.refund_amount
                logger.info(f"退款成功: {refund_id}")
            elif pay_status == "1":
                # 退款失败
                refund.status = RefundStatus.refund_failed
                refund.failed_at = datetime.now()
                logger.info(f"退款失败: {refund_id}")
            else:
                # 状态未知，继续处理中
                refund.status = RefundStatus.refund_processing
                logger.info(f"退款状态未知: {refund_id}")

            self.db.commit()
            self.db.refresh(refund)

            return refund

        except Exception as e:
            logger.error(f"查询退款状态失败: {e}")
            self.db.rollback()
            raise

    def get_refund_by_id(self, refund_id: str) -> Optional[PaymentRefundModel]:
        """
        根据ID获取退款订单

        Args:
            refund_id: 退款订单ID

        Returns:
            退款订单，不存在则返回 None
        """
        return self.db.query(PaymentRefundModel).filter(
            PaymentRefundModel.id == refund_id
        ).first()

    def list_refunds(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        out_trade_no: Optional[str] = None,
        out_refund_no: Optional[str] = None,
    ) -> tuple[list[PaymentRefundModel], int]:
        """
        获取退款订单列表

        Args:
            page: 页码
            page_size: 每页数量
            status: 状态筛选
            out_trade_no: 商户订单号筛选
            out_refund_no: 退款流水号筛选

        Returns:
            (退款订单列表, 总数)
        """
        query = self.db.query(PaymentRefundModel)

        # 关联支付订单进行筛选
        if out_trade_no:
            query = query.join(PaymentOrderModel).filter(
                PaymentOrderModel.out_trade_no.like(f"%{out_trade_no}%")
            )

        if out_refund_no:
            query = query.filter(
                PaymentRefundModel.out_refund_no.like(f"%{out_refund_no}%")
            )

        if status:
            query = query.filter(PaymentRefundModel.status == status)

        # 总数
        total = query.count()

        # 分页
        refunds = query.order_by(
            PaymentRefundModel.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return refunds, total

    def get_payment_order_refunds(self, payment_order_id: str) -> list[PaymentRefundModel]:
        """
        获取支付订单的所有退款记录

        Args:
            payment_order_id: 支付订单ID

        Returns:
            退款记录列表
        """
        return self.db.query(PaymentRefundModel).filter(
            PaymentRefundModel.payment_order_id == payment_order_id
        ).order_by(PaymentRefundModel.created_at.desc()).all()
