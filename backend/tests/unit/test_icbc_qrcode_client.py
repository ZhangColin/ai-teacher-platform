# -*- coding: utf-8 -*-
"""工行二维码支付客户端测试"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from src.services.icbc_qrcode_client import IcbcQrCodeClient


@pytest.fixture
def icbc_client():
    """创建测试用的工行客户端"""
    # 使用真实密钥文件进行测试
    from src.config.icbc_config import get_icbc_client_config
    config = get_icbc_client_config()
    return IcbcQrCodeClient(
        app_id=config["app_id"],
        mer_id=config["mer_id"],
        private_key_pem=config["private_key_pem"],
        public_key_pem=config["public_key_pem"],
        notify_url="",
    )


def test_client_initialization(icbc_client):
    """测试客户端初始化"""
    assert icbc_client.app_id == "11000000000000079872"
    assert icbc_client.mer_id == "020004161912"
    assert icbc_client._private_key is not None
    assert icbc_client._public_key is not None


def test_sign(icbc_client):
    """测试 RSA2 签名"""
    data = "app_id=11000000000000079872&charset=UTF-8&format=json"
    signature = icbc_client._sign(data)

    # 验证签名是 Base64 编码的字符串
    assert isinstance(signature, str)
    assert len(signature) > 0
    # Base64 编码的签名只包含特定字符
    import base64
    try:
        base64.b64decode(signature)
        assert True
    except Exception:
        assert False, "签名不是有效的 Base64 编码"


def test_verify(icbc_client):
    """测试 RSA2 验签"""
    data = "app_id=11000000000000079872&charset=UTF-8&format=json"
    signature = icbc_client._sign(data)

    # 验证自己的签名应该成功
    assert icbc_client._verify(data, signature) is True

    # 错误的签名应该验证失败
    assert icbc_client._verify(data, "wrong_signature") is False


def test_build_sign_str(icbc_client):
    """测试构建签名字符串"""
    params = {
        "app_id": "11000000000000079872",
        "charset": "UTF-8",
        "format": "json",
        "sign": "should_be_ignored",
        "empty_value": "",
        "none_value": None,
    }

    sign_str = icbc_client._build_sign_str(params)

    # 验证参数按字典序排序
    assert sign_str == "app_id=11000000000000079872&charset=UTF-8&format=json"

    # 验证空值和 None 被排除
    assert "empty_value" not in sign_str
    assert "none_value" not in sign_str
    assert "sign" not in sign_str


@pytest.mark.asyncio
async def test_generate_qrcode_success(icbc_client):
    """测试生成二维码成功（mock 工行接口）"""
    mock_response_data = {
        "return_code": "0",
        "return_msg": "成功",
        "qrcode": "TEST_QR_CODE_DATA_STRING",
        "order_id": "ICBC_TEST_ORDER_123",
    }

    # 创建 mock 响应对象（httpx.Response.json() 是同步方法）
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value=mock_response_data)
    mock_response.raise_for_status = MagicMock()

    # 创建 mock 客户端
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    # 创建异步上下文管理器 mock
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_async_client():
        yield mock_client

    with patch('httpx.AsyncClient', return_value=mock_async_client()):
        result = await icbc_client.generate_qrcode(
            out_trade_no="TEST2026032612345678",
            amount=1,  # 1分钱
            trade_date="20260326",
            trade_time="123456",
            expire_seconds=900,
        )

        assert result["return_code"] == "0"
        assert result["qrcode"] == "TEST_QR_CODE_DATA_STRING"
        assert result["order_id"] == "ICBC_TEST_ORDER_123"


@pytest.mark.asyncio
async def test_generate_qrcode_builds_correct_request(icbc_client):
    """测试生成二维码时构建正确的请求"""
    # 创建 mock 响应对象（httpx.Response.json() 是同步方法）
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value={"return_code": "0", "qrcode": "test"})
    mock_response.raise_for_status = MagicMock()

    # 创建 mock 客户端
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    # 创建异步上下文管理器 mock
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_async_client():
        yield mock_client

    with patch('httpx.AsyncClient', return_value=mock_async_client()):
        await icbc_client.generate_qrcode(
            out_trade_no="TEST2026032612345678",
            amount=1,
            trade_date="20260326",
            trade_time="123456",
        )

        # 验证调用了正确的端点
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert icbc_client.API_GENERATE_QRCODE in str(call_args)

        # 验证请求体包含必需参数
        request_json = call_args[1]["json"]
        assert request_json["app_id"] == "11000000000000079872"
        assert request_json["sign_type"] == "RSA2"
        assert "sign" in request_json

        # 验证 biz_content
        biz_content = json.loads(request_json["biz_content"])
        assert biz_content["merId"] == "020004161912"
        assert biz_content["outTradeNo"] == "TEST2026032612345678"
        assert biz_content["orderAmt"] == "1"


@pytest.mark.asyncio
async def test_query_order_success(icbc_client):
    """测试查询订单成功（mock 工行接口）"""
    mock_response_data = {
        "return_code": "0",
        "return_msg": "成功",
        "payStatus": "1",  # 1=支付成功
        "order_id": "ICBC_TEST_ORDER_123",
    }

    # 创建 mock 响应对象
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value=mock_response_data)
    mock_response.raise_for_status = MagicMock()

    # 创建 mock 客户端
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    # 创建异步上下文管理器 mock
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_async_client():
        yield mock_client

    with patch('httpx.AsyncClient', return_value=mock_async_client()):
        result = await icbc_client.query_order(
            out_trade_no="TEST2026032612345678",
        )

        assert result["return_code"] == "0"
        assert result["payStatus"] == "1"


@pytest.mark.asyncio
async def test_query_order_with_order_id(icbc_client):
    """测试使用工行订单号查询"""
    # 创建 mock 响应对象
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value={"return_code": "0"})
    mock_response.raise_for_status = MagicMock()

    # 创建 mock 客户端
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    # 创建异步上下文管理器 mock
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_async_client():
        yield mock_client

    with patch('httpx.AsyncClient', return_value=mock_async_client()):
        await icbc_client.query_order(
            out_trade_no="TEST2026032612345678",
            order_id="ICBC_ORDER_123",
        )

        # 验证请求中包含 order_id
        call_args = mock_client.post.call_args
        request_json = call_args[1]["json"]
        biz_content = json.loads(request_json["biz_content"])
        assert biz_content["orderId"] == "ICBC_ORDER_123"


def test_verify_notify_success(icbc_client):
    """测试回调验签成功"""
    # 构造测试数据
    test_data = {
        "app_id": "11000000000000079872",
        "return_code": "0",
        "out_trade_no": "TEST123",
    }

    # 生成签名
    sign_str = icbc_client._build_sign_str(test_data)
    signature = icbc_client._sign(sign_str)
    test_data["sign"] = signature

    # 验签应该成功
    assert icbc_client.verify_notify(test_data) is True


def test_verify_notify_missing_sign(icbc_client):
    """测试回调验签 - 缺少签名"""
    test_data = {
        "app_id": "11000000000000079872",
        "return_code": "0",
    }

    assert icbc_client.verify_notify(test_data) is False


def test_verify_notify_wrong_sign(icbc_client):
    """测试回调验签 - 错误签名"""
    test_data = {
        "app_id": "11000000000000079872",
        "return_code": "0",
        "sign": "wrong_signature",
    }

    assert icbc_client.verify_notify(test_data) is False
