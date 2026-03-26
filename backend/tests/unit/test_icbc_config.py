# -*- coding: utf-8 -*-
"""工行配置测试"""
import pytest
from backend.src.config.icbc_config import (
    ICBC_PAYMENT_CONFIG,
    load_key_content,
    get_icbc_client_config
)


class TestIcbcConfig:
    """工行配置测试"""

    def test_config_structure(self):
        """测试配置结构完整"""
        required_keys = [
            "app_id", "mer_id", "mer_prtcl_no",
            "access_type", "cur_type", "goods_name", "body",
            "notify_type", "result_type", "notify_url",
            "private_key_path", "public_key_path"
        ]
        for key in required_keys:
            assert key in ICBC_PAYMENT_CONFIG

    def test_mer_prtcl_no_format(self):
        """测试协议编号格式 = mer_id + 0201"""
        assert ICBC_PAYMENT_CONFIG["mer_prtcl_no"] == ICBC_PAYMENT_CONFIG["mer_id"] + "0201"

    def test_access_type_is_pc(self):
        """测试接入方式为PC"""
        assert ICBC_PAYMENT_CONFIG["access_type"] == "6"

    def test_cur_type_is_rmb(self):
        """测试币种为人民币"""
        assert ICBC_PAYMENT_CONFIG["cur_type"] == "001"

    def test_load_private_key_pem_format(self):
        """测试私钥转换为PEM格式"""
        pem = load_key_content(ICBC_PAYMENT_CONFIG["private_key_path"])
        assert pem.startswith("-----BEGIN PRIVATE KEY-----")
        assert pem.endswith("-----END PRIVATE KEY-----")

    def test_load_public_key_pem_format(self):
        """测试公钥转换为PEM格式"""
        pem = load_key_content(ICBC_PAYMENT_CONFIG["public_key_path"])
        assert pem.startswith("-----BEGIN PUBLIC KEY-----")
        assert pem.endswith("-----END PUBLIC KEY-----")

    def test_get_client_config(self):
        """测试获取客户端配置"""
        config = get_icbc_client_config()
        assert "private_key_pem" in config
        assert "public_key_pem" in config
        assert config["app_id"] == ICBC_PAYMENT_CONFIG["app_id"]
