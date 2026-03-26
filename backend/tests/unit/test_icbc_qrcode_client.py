# -*- coding: utf-8 -*-
"""工行二维码支付客户端测试"""
import pytest
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
