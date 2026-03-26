# -*- coding: utf-8 -*-
"""支付服务"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db_models import (
    PaymentOrderModel, PaymentOrderStatus, UserModel, EnterpriseModel,
    SystemConfigModel, PointTransactionType, PointSourceType
)
from .icbc_qrcode_client import IcbcQrCodeClient
from .point_service import PointService

logger = logging.getLogger(__name__)


class PaymentService:
    """支付服务"""

    def __init__(self, db: Session, icbc_client: IcbcQrCodeClient, point_service: PointService):
        """
        初始化支付服务

        Args:
            db: 数据库会话
            icbc_client: 工行客户端
            point_service: 积分服务
        """
        self.db = db
        self.icbc_client = icbc_client
        self.point_service = point_service

    def _generate_out_trade_no(self) -> str:
        """
        生成商户订单号

        格式: yyyyMMddHHmmss + 8位随机数
        """
        now = datetime.now()
        time_str = now.strftime("%Y%m%d%H%M%S")
        random_str = uuid.uuid4().hex[:8].upper()
        return f"{time_str}{random_str}"

    def _get_user_enterprise(self, user_id: str) -> Optional[EnterpriseModel]:
        """
        获取用户所属企业

        Args:
            user_id: 用户ID

        Returns:
            企业对象，不存在则返回 None
        """
        user = self.db.query(UserModel).filter(
            UserModel.user_id == user_id
        ).first()

        if not user or not user.enterprise_id:
            return None

        return self.db.query(EnterpriseModel).filter(
            EnterpriseModel.id == user.enterprise_id
        ).first()

    async def create_payment_order(
        self,
        user_id: str,
        amount: int,
        body: str = "积分充值",
        expire_time: int = 900
    ) -> dict:
        """
        创建支付订单

        Args:
            user_id: 用户ID
            amount: 金额（分）
            body: 商品描述
            expire_time: 过期时间（秒）

        Returns:
            订单信息，包含支付 URL
        """
        # 1. 验证用户
        enterprise = self._get_user_enterprise(user_id)
        if not enterprise:
            raise ValueError("用户未关联企业")

        # 2. 生成订单号
        out_trade_no = self._generate_out_trade_no()

        # 3. 计算过期时间
        expire_at = datetime.now() + timedelta(seconds=expire_time)

        # 4. 创建订单记录
        order = PaymentOrderModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            out_trade_no=out_trade_no,
            amount=amount,
            status=PaymentOrderStatus.created,
            business_type="recharge",
            expire_at=expire_at,
            goods_name=self.icbc_client.goods_name,  # 新增：商品名称
            attach=body[:127] if len(body) > 127 else body,  # 新增：附加数据
        )
        self.db.add(order)
        self.db.flush()

        # 5. 调用工行二维码生成接口（真实调用）
        # 注意：新接口不再需要 trade_date 和 trade_time 参数
        try:
            icbc_response = await self.icbc_client.generate_qrcode(
                out_trade_no=out_trade_no,
                amount=amount,
                expire_seconds=expire_time,
                attach=body[:127] if len(body) > 127 else body,  # 工行限制127字符
            )

            # 6. 更新订单状态
            order.status = PaymentOrderStatus.processing
            order.submitted_at = datetime.now()
            order.icbc_response = icbc_response
            order.msg_id = icbc_response.get("msg_id", "")  # 保存 msg_id

            # 7. 解析工行响应
            if icbc_response.get("return_code") == "0":  # 成功
                order.qr_code_data = icbc_response.get("codeUrl")  # 新接口字段名：codeUrl
                order.third_trade_no = icbc_response.get("order_id")
                order.support_app_type = icbc_response.get("supportAppType")  # 新增字段
            else:
                # 下单失败
                order.status = PaymentOrderStatus.failed
                error_msg = icbc_response.get("return_msg", "未知错误")
                raise ValueError(f"工行下单失败: {error_msg}")

            self.db.commit()

            logger.info(f"支付订单创建成功 - 订单号:{out_trade_no}, 用户:{user_id}, 金额:{amount}")

            return {
                "order_id": order.id,
                "out_trade_no": out_trade_no,
                "amount": amount,
                "status": order.status.value,
                "pay_url": order.pay_url,
                "qr_code_data": order.qr_code_data,
                "expire_at": expire_at.isoformat() if expire_at else None
            }

        except Exception as e:
            order.status = PaymentOrderStatus.failed
            self.db.commit()
            logger.error(f"支付订单创建失败 - 订单号:{out_trade_no}, 错误:{e}", exc_info=True)
            raise

    async def query_payment_status(self, order_id: str) -> dict:
        """
        查询支付状态

        Args:
            order_id: 订单ID

        Returns:
            订单状态信息
        """
        order = self.db.query(PaymentOrderModel).filter(
            PaymentOrderModel.id == order_id
        ).first()

        if not order:
            raise ValueError("订单不存在")

        # 如果订单未完成，主动查询工行
        if order.status in [PaymentOrderStatus.created, PaymentOrderStatus.processing]:
            try:
                icbc_response = await self.icbc_client.query_order(order.out_trade_no)

                order.icbc_response = icbc_response

                # 解析支付状态
                # 工行查询响应在 response_biz_content 中
                biz_content = icbc_response.get("response_biz_content", {})
                if biz_content.get("return_code") == "0" or icbc_response.get("return_code") == "0":
                    pay_status = biz_content.get("pay_status")
                    if pay_status == "0":  # 0=成功（注意：工行查询接口0表示成功）
                        await self._handle_payment_success(order, biz_content)
                    elif pay_status == "1":  # 1=失败
                        order.status = PaymentOrderStatus.failed

                self.db.commit()

            except Exception as e:
                logger.error(f"查询支付状态失败 - 订单ID:{order_id}, 错误:{e}", exc_info=True)

        return {
            "order_id": order.id,
            "out_trade_no": order.out_trade_no,
            "amount": order.amount,
            "status": order.status.value,
            "third_trade_no": order.third_trade_no,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        }

    async def handle_notify(self, notify_data: dict) -> bool:
        """
        处理工行支付回调

        Args:
            notify_data: 回调数据

        Returns:
            处理是否成功
        """
        # 1. 验签
        if not self.icbc_client.verify_notify(notify_data):
            logger.error(f"支付回调验签失败: {notify_data}")
            return False

        # 2. 解析订单号
        out_trade_no = notify_data.get("out_trade_no")
        if not out_trade_no:
            logger.error(f"支付回调缺少订单号: {notify_data}")
            return False

        # 3. 查找订单
        order = self.db.query(PaymentOrderModel).filter(
            PaymentOrderModel.out_trade_no == out_trade_no
        ).first()

        if not order:
            logger.error(f"支付回调订单不存在: {out_trade_no}")
            return False

        # 4. 防止重复处理
        if order.status == PaymentOrderStatus.paid:
            logger.info(f"支付回调订单已处理: {out_trade_no}")
            return True

        # 5. 记录回调信息
        order.notify_data = notify_data
        order.notify_verify_result = True
        order.notified_at = datetime.now()
        order.icbc_response = notify_data

        # 6. 判断支付状态
        # 工行回调：return_code=0 表示成功
        if notify_data.get("return_code") == "0":  # 支付成功
            await self._handle_payment_success(order, notify_data)
            self.db.commit()
            return True
        else:
            order.status = PaymentOrderStatus.failed
            self.db.commit()
            logger.warning(f"支付回调状态异常 - 订单:{out_trade_no}, 状态:{notify_data.get('return_code')}")
            return False

    async def _handle_payment_success(self, order: PaymentOrderModel, icbc_response: dict) -> None:
        """
        处理支付成功

        Args:
            order: 订单对象
            icbc_response: 工行响应
        """
        # 1. 更新订单状态
        order.status = PaymentOrderStatus.paid
        order.paid_at = datetime.now()

        # 新接口：工行订单号直接在响应根节点（不是 biz_content）
        order.third_trade_no = icbc_response.get("order_id")

        # 2. 计算积分
        points = self._calculate_points(order.amount)

        # 3. 增加积分（传入支付订单ID和充值金额）
        enterprise = self._get_user_enterprise(order.user_id)
        self.point_service.add_points(
            enterprise_id=enterprise.id,
            amount=points,
            source_type=PointSourceType.online_payment,
            operator_id=None,
            remark=f"在线充值 - 订单号:{order.out_trade_no}",
            payment_id=order.id,
            payment_amount=order.amount
        )

        logger.info(
            f"支付成功 - 订单:{order.out_trade_no}, 用户:{order.user_id}, "
            f"金额:{order.amount}分, 积分:{points}"
        )

    def _calculate_points(self, amount: int) -> int:
        """
        计算充值金额对应的积分

        Args:
            amount: 金额（分）

        Returns:
            积分数量
        """
        points_per_yuan = self._get_points_per_yuan()
        # 金额（分）转换为元，再乘以汇率
        return (amount // 100) * points_per_yuan

    def _get_points_per_yuan(self) -> int:
        """
        获取每元对应的积分数量

        从系统配置中读取，默认 100 积分/元
        """
        config = self.db.query(SystemConfigModel).filter(
            SystemConfigModel.key == "points_per_yuan"
        ).first()

        if config:
            try:
                return int(config.value)
            except ValueError:
                pass

        return 100  # 默认 100 积分/元

    def mark_order_timeout(self, order_id: str) -> bool:
        """
        标记订单超时

        Args:
            order_id: 订单ID

        Returns:
            是否标记成功
        """
        order = self.db.query(PaymentOrderModel).filter(
            PaymentOrderModel.id == order_id
        ).first()

        if not order:
            return False

        # 只有未支付的订单才能标记为超时
        if order.status in [PaymentOrderStatus.created, PaymentOrderStatus.processing]:
            order.status = PaymentOrderStatus.timeout
            self.db.commit()
            logger.info(f"订单标记为超时 - 订单ID:{order_id}")
            return True

        return False

    def get_recharge_records(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[list, int]:
        """
        获取用户充值记录

        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量

        Returns:
            (订单列表, 总数)
        """
        query = self.db.query(PaymentOrderModel).filter(
            PaymentOrderModel.user_id == user_id,
            PaymentOrderModel.business_type == "recharge"
        )

        total = query.count()

        orders = query.order_by(
            PaymentOrderModel.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return orders, total
