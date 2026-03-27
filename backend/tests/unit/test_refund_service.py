# -*- coding: utf-8 -*-
"""退款服务单元测试"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.services.refund_service import RefundService
from src.db_models import RefundStatus, PaymentOrderStatus


class TestRefundService:
    """退款服务测试"""

    @pytest.fixture
    def db(self):
        """模拟数据库会话"""
        return Mock()

    @pytest.fixture
    def icbc_client(self):
        """模拟工行客户端"""
        return Mock()

    @pytest.fixture
    def refund_service(self, db, icbc_client):
        """退款服务实例"""
        return RefundService(db, icbc_client)

    def test_generate_refund_no(self, refund_service):
        """测试退款流水号生成"""
        refund_no = refund_service._generate_refund_no()
        assert refund_no.startswith("REF")
        assert len(refund_no) == 25  # REF(3) + 时间戳(14) + 随机数(8)

    def test_can_refund_success(self, refund_service):
        """测试可以退款 - 成功场景"""
        payment_order = Mock()
        payment_order.status = PaymentOrderStatus.paid
        payment_order.amount = 10000  # 100元
        payment_order.refunded_amount = 3000  # 已退30元

        result = refund_service._can_refund(payment_order, 2000)  # 再退20元
        assert result is True

    def test_can_refund_wrong_status(self, refund_service):
        """测试可以退款 - 状态错误"""
        payment_order = Mock()
        payment_order.status = PaymentOrderStatus.created
        payment_order.amount = 10000
        payment_order.refunded_amount = 0

        result = refund_service._can_refund(payment_order, 1000)
        assert result is False

    def test_can_refund_exceeds_amount(self, refund_service):
        """测试可以退款 - 超过可退金额"""
        payment_order = Mock()
        payment_order.status = PaymentOrderStatus.paid
        payment_order.amount = 10000
        payment_order.refunded_amount = 8000  # 已退80元

        result = refund_service._can_refund(payment_order, 3000)  # 尝试退30元
        assert result is False

    def test_can_refund_exact_amount(self, refund_service):
        """测试可以退款 - 刚好全部退完"""
        payment_order = Mock()
        payment_order.status = PaymentOrderStatus.paid
        payment_order.amount = 10000
        payment_order.refunded_amount = 8000  # 已退80元

        result = refund_service._can_refund(payment_order, 2000)  # 再退20元
        assert result is True

    def test_can_refund_zero_amount(self, refund_service):
        """测试可以退款 - 退款金额为0"""
        payment_order = Mock()
        payment_order.status = PaymentOrderStatus.paid
        payment_order.amount = 10000
        payment_order.refunded_amount = 0

        result = refund_service._can_refund(payment_order, 0)
        assert result is True
