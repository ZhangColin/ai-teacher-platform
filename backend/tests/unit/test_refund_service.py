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


class TestRefundStatusParsing:
    """测试退款状态解析逻辑"""

    @pytest.fixture
    def service(self):
        """退款服务实例"""
        db = Mock()
        mock_client = Mock()
        return RefundService(db, mock_client)

    def test_parse_query_response_success(self, service):
        """测试解析查询响应 - 成功"""
        query_response = {
            "response_biz_content": {
                "return_code": "0",
                "pay_status": "0",
                "real_reject_amt": "100"
            }
        }
        status, timestamp_field = service._parse_query_status(query_response)
        assert status == RefundStatus.refund_success
        assert timestamp_field == "success_at"

    def test_parse_query_response_failed(self, service):
        """测试解析查询响应 - 失败"""
        query_response = {
            "response_biz_content": {
                "return_code": "0",
                "pay_status": "1"
            }
        }
        status, timestamp_field = service._parse_query_status(query_response)
        assert status == RefundStatus.refund_failed
        assert timestamp_field == "failed_at"

    def test_parse_query_response_processing(self, service):
        """测试解析查询响应 - 处理中"""
        query_response = {
            "response_biz_content": {
                "return_code": "0",
                "pay_status": "2"
            }
        }
        status, timestamp_field = service._parse_query_status(query_response)
        assert status == RefundStatus.refund_processing
        assert timestamp_field is None

    def test_parse_query_response_missing_biz_content(self, service):
        """测试解析查询响应 - 缺少 response_biz_content"""
        query_response = {"return_code": "0"}
        status, timestamp_field = service._parse_query_status(query_response)
        assert status == RefundStatus.refund_processing  # 默认为处理中
        assert timestamp_field is None

    def test_parse_query_response_missing_pay_status(self, service):
        """测试解析查询响应 - 缺少 pay_status"""
        query_response = {
            "response_biz_content": {
                "return_code": "0"
            }
        }
        status, timestamp_field = service._parse_query_status(query_response)
        assert status == RefundStatus.refund_processing
        assert timestamp_field is None
