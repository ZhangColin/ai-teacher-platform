# -*- coding: utf-8 -*-
"""退款服务单元测试"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.services.refund_service import RefundService
from src.db_models import RefundStatus, PaymentOrderStatus, PaymentRefundModel


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


class TestRefundCreationWithQuery:
    """测试退款创建后的状态查询"""

    @pytest.fixture
    def service(self):
        """退款服务实例"""
        db = Mock()
        mock_client = Mock()
        return RefundService(db, mock_client)

    @pytest.fixture
    def payment_order(self):
        """模拟支付订单"""
        order = Mock()
        order.id = "test-order-id"
        order.user_id = "test-user-id"
        order.out_trade_no = "TEST20260330001"
        order.amount = 1000
        order.status = PaymentOrderStatus.paid
        order.pay_channel = "icbc_aggregate"
        order.third_trade_no = "icbc-order-123"
        order.refunded_amount = 0
        order.refund_count = 0
        return order

    @pytest.mark.asyncio
    async def test_create_refund_success_then_query_success(self, service, payment_order):
        """测试发起退款成功，查询返回成功"""
        # 模拟数据库
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = payment_order
        service.db = mock_db

        # 模拟退款接口返回成功
        service.icbc_client.refund_order = AsyncMock(return_value={
            "return_code": "0",
            "intrx_serial_no": "icbc-refund-no",
        })
        # 模拟查询接口返回成功
        service.icbc_client.query_refund = AsyncMock(return_value={
            "response_biz_content": {
                "return_code": "0",
                "pay_status": "0",  # 成功
                "real_reject_amt": "100"
            }
        })

        # 创建退款
        refund = await service.create_refund(
            payment_order_id=payment_order.id,
            refund_amount=100,
            operator_id="test-operator",
            operator_name="测试"
        )

        # 验证状态
        assert refund.status == RefundStatus.refund_success
        assert refund.icbc_refund_response is not None
        assert refund.icbc_query_response is not None

    @pytest.mark.asyncio
    async def test_create_refund_success_then_query_processing(self, service, payment_order):
        """测试发起退款成功，查询返回处理中"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = payment_order
        service.db = mock_db

        service.icbc_client.refund_order = AsyncMock(return_value={
            "return_code": "0"
        })
        service.icbc_client.query_refund = AsyncMock(return_value={
            "response_biz_content": {
                "return_code": "0",
                "pay_status": "2"  # 处理中
            }
        })

        refund = await service.create_refund(
            payment_order_id=payment_order.id,
            refund_amount=100,
            operator_id="test-operator"
        )

        assert refund.status == RefundStatus.refund_processing

    @pytest.mark.asyncio
    async def test_create_refund_initiate_failed(self, service, payment_order):
        """测试发起退款失败"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = payment_order
        service.db = mock_db

        service.icbc_client.refund_order = AsyncMock(return_value={
            "return_code": "400017",  # 签名验证失败
            "return_msg": "签名验证失败"
        })

        refund = await service.create_refund(
            payment_order_id=payment_order.id,
            refund_amount=100,
            operator_id="test-operator"
        )

        assert refund.status == RefundStatus.refund_failed
        assert refund.icbc_refund_response is not None
        # 发起失败时不会调用查询接口
        assert refund.icbc_query_response is None


class TestRefundQueryStatus:
    """测试退款状态查询"""

    @pytest.fixture
    def service(self):
        """退款服务实例"""
        db = Mock()
        mock_client = Mock()
        return RefundService(db, mock_client)

    @pytest.fixture
    def refund(self):
        """模拟退款记录"""
        r = Mock()
        r.id = "test-refund-id"
        r.out_refund_no = "TEST20260330001"
        r.payment_order_id = "test-order-id"
        r.status = RefundStatus.refund_processing
        r.real_refund_amount = None
        r.icbc_refund_response = {"old": "data"}
        r.icbc_query_response = None
        return r

    @pytest.fixture
    def payment_order(self):
        """模拟支付订单"""
        order = Mock()
        order.id = "test-order-id"
        order.out_trade_no = "TEST20260330001"
        order.third_trade_no = "icbc-order-123"
        return order

    @pytest.mark.asyncio
    async def test_query_refund_saves_to_correct_field(self, service, refund, payment_order):
        """测试查询响应保存到 icbc_query_response 而不是 icbc_refund_response"""
        # 设置 mock
        mock_db = Mock()

        # 第一次调用返回 refund，第二次调用返回 payment_order
        mock_query = Mock()
        mock_refund_result = Mock()
        mock_refund_result.first.return_value = refund
        mock_order_result = Mock()
        mock_order_result.first.return_value = payment_order

        # 模拟 query 返回不同结果
        def mock_query_side_effect(model):
            if model == PaymentRefundModel:
                return mock_refund_result
            else:
                return mock_order_result

        mock_db.query.side_effect = mock_query_side_effect
        service.db = mock_db

        # 模拟查询接口返回
        service.icbc_client.query_refund = AsyncMock(return_value={
            "response_biz_content": {
                "return_code": "0",
                "pay_status": "0"
            }
        })

        # 执行查询
        result = await service.query_refund_status(refund.id)

        # 验证：查询响应应该保存到 icbc_query_response
        assert result.icbc_query_response is not None
        assert result.icbc_query_response.get("response_biz_content", {}).get("pay_status") == "0"
