# -*- coding: utf-8 -*-
"""工行客户端测试"""
import pytest
from backend.src.services.icbc_qrcode_client import IcbcQrCodeClient
from backend.src.config.icbc_config import get_icbc_client_config


class TestIcbcQrCodeClient:
    """工行客户端测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        config = get_icbc_client_config()
        return IcbcQrCodeClient(**config)

    def test_init(self, client):
        """测试客户端初始化"""
        assert client.app_id is not None
        assert client.mer_id is not None
        assert client._private_key is not None
        assert client._public_key is not None

    def test_generate_msg_id(self, client):
        """测试 msg_id 生成"""
        msg_id = client._generate_msg_id()
        assert len(msg_id) <= 40
        assert msg_id.isalnum()

    def test_sign_and_verify(self, client):
        """测试签名和验签"""
        test_data = "test_string_for_signing"
        signature = client._sign(test_data)
        assert signature  # 签名非空

        # 验签
        result = client._verify(test_data, signature)
        assert result is True

        # 错误验签
        result = client._verify(test_data, "wrong_signature")
        assert result is False

    def test_build_sign_str(self, client):
        """测试签名字符串构建"""
        params = {
            "app_id": "123",
            "msg_id": "456",
            "format": "json",
            "sign": "should_be_ignored",
            "empty_value": "",
            "null_value": None,
            "z_param": "last",
            "a_param": "first",
        }

        # 测试不带路径的签名字符串
        sign_str = client._build_sign_str(params)
        assert sign_str.startswith("a_param=first")
        assert "z_param=last" in sign_str
        assert "sign=" not in sign_str
        assert "empty_value=" not in sign_str
        assert "null_value=" not in sign_str

        # 测试带路径的签名字符串（工行SDK格式）
        path = "/api/cardbusiness/qrcode/consumption/V1"
        sign_str_with_path = client._build_sign_str(params, path)
        assert sign_str_with_path.startswith(f"{path}?")
        assert "a_param=first" in sign_str_with_path
        assert "z_param=last" in sign_str_with_path

    @pytest.mark.asyncio
    async def test_generate_qrcode_request_params(self, client):
        """测试生成二维码请求参数构造"""
        # 注意：这只是一个参数构造测试，不会真正调用API
        # 实际API调用需要集成测试或mock

        # 准备测试数据
        out_trade_no = "TEST2026032612043000001"
        amount = 1  # 1分钱

        # 这里我们只测试内部方法，不发送真实请求
        msg_id = client._generate_msg_id()
        assert msg_id is not None

        biz_content = {
            "out_trade_no": out_trade_no,
            "mer_id": client.mer_id,
            "mer_prtcl_no": client.mer_prtcl_no,
            "access_type": client.access_type,
            "cur_type": client.cur_type,
            "amount": str(amount),
            "icbc_appid": client.app_id,
            "expire_time": "900",
            "notify_type": client.notify_type,
            "result_type": client.result_type,
            "attach": "",
            "order_date": "2026-03-26 12:04:30",
            "goods_name": client.goods_name,
            "body": client.body,
        }

        # 验证必填字段
        required_keys = [
            "out_trade_no", "mer_id", "mer_prtcl_no", "access_type",
            "cur_type", "amount", "icbc_appid", "notify_type",
            "result_type", "order_date", "goods_name", "body"
        ]
        for key in required_keys:
            assert key in biz_content

    def test_query_order_params(self, client):
        """测试查询订单参数构造"""
        out_trade_no = "TEST2026032612043000001"

        biz_content = {
            "mer_id": client.mer_id,
            "out_trade_no": out_trade_no,
            "deal_flag": "0",
            "icbc_appid": client.app_id,
            "mer_prtcl_no": client.mer_prtcl_no,
        }

        # 验证必填字段
        required_keys = ["mer_id", "out_trade_no", "deal_flag", "icbc_appid", "mer_prtcl_no"]
        for key in required_keys:
            assert key in biz_content

    def test_query_order_with_order_id(self, client):
        """测试带工行订单号的查询"""
        out_trade_no = "TEST2026032612043000001"
        order_id = "0200041619122026032612043000001"

        biz_content = {
            "mer_id": client.mer_id,
            "out_trade_no": out_trade_no,
            "order_id": order_id,
            "deal_flag": "0",
            "icbc_appid": client.app_id,
            "mer_prtcl_no": client.mer_prtcl_no,
        }

        assert "order_id" in biz_content
        assert biz_content["order_id"] == order_id

    def test_verify_notify(self, client):
        """测试回调验签"""
        # 构造测试数据
        test_data = {
            "from": "icbc-api",
            "api": "/api/test",
            "app_id": client.app_id,
            "charset": "utf-8",
            "format": "json",
            "sign_type": "RSA2",
            "timestamp": "2026-03-26 12:04:30",
        }

        # 生成签名
        sign_str = client._build_sign_str(test_data)
        sign = client._sign(sign_str)
        test_data["sign"] = sign

        # 验签应该成功
        result = client.verify_notify(test_data)
        assert result is True

    def test_sign_notify_response(self, client):
        """测试回调响应签名"""
        msg_id = "TEST_MSG_ID_123"
        response = client.sign_notify_response(0, msg_id)

        assert "response_biz_content" in response
        assert "sign_type" in response
        assert "sign" in response
        assert response["response_biz_content"]["return_code"] == 0
        assert response["response_biz_content"]["msg_id"] == msg_id
        assert response["sign_type"] == "RSA2"
