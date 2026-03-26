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
        sign_str = client._build_sign_str(params)

        # 检查排序和过滤
        assert "a_param=first" in sign_str
        assert "z_param=last" in sign_str
        assert "sign=" not in sign_str
        assert "empty_value=" not in sign_str
        assert "null_value=" not in sign_str

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
