# -*- coding: utf-8 -*-
"""退款流程集成测试"""
import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest.mark.asyncio
class TestRefundFlow:
    """退款流程集成测试"""

    async def test_create_refund_unauthorized(self):
        """测试未授权创建退款"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/admin/payment/refunds/create", json={
                "payment_order_id": "test-id",
                "refund_amount": 100
            })
            assert response.status_code == 401

    async def test_list_refunds_unauthorized(self):
        """测试未授权获取退款列表"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/payment/refunds")
            assert response.status_code == 401

    async def test_get_refund_detail_unauthorized(self):
        """测试未授权获取退款详情"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/admin/payment/refunds/test-id")
            assert response.status_code == 401

    # 注意：其他集成测试需要有效的认证token和测试数据
    # 建议在实际环境中手动测试
