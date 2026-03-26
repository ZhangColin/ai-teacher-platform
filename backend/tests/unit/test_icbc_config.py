# -*- coding: utf-8 -*-
"""工行支付配置模块测试"""
import os
import pytest
from pathlib import Path


def test_load_icbc_config():
    """测试工行配置加载"""
    from src.config.icbc_config import ICBC_PAYMENT_CONFIG, get_icbc_client_config

    # 验证必需的配置项存在
    assert "app_id" in ICBC_PAYMENT_CONFIG
    assert "mer_id" in ICBC_PAYMENT_CONFIG
    assert "private_key_path" in ICBC_PAYMENT_CONFIG
    assert "public_key_path" in ICBC_PAYMENT_CONFIG
    assert "notify_url" in ICBC_PAYMENT_CONFIG

    # 验证默认值
    assert ICBC_PAYMENT_CONFIG["app_id"] == "11000000000000079872"
    assert ICBC_PAYMENT_CONFIG["mer_id"] == "020004161912"

    # 验证密钥文件路径存在
    assert Path(ICBC_PAYMENT_CONFIG["private_key_path"]).exists()
    assert Path(ICBC_PAYMENT_CONFIG["public_key_path"]).exists()


def test_get_icbc_client_config():
    """测试获取客户端配置"""
    from src.config.icbc_config import get_icbc_client_config

    config = get_icbc_client_config()

    # 验证返回的配置包含必需字段
    assert "app_id" in config
    assert "mer_id" in config
    assert "private_key_pem" in config
    assert "public_key_pem" in config
    assert "notify_url" in config

    # 验证密钥已加载（非空字符串）
    assert len(config["private_key_pem"]) > 0
    assert len(config["public_key_pem"]) > 0
    assert config["private_key_pem"].startswith("-----BEGIN")
    assert config["public_key_pem"].startswith("-----BEGIN")


def test_load_key_content_with_raw_base64():
    """测试加载裸 Base64 格式的密钥"""
    from src.config.icbc_config import load_key_content, ICBC_PAYMENT_CONFIG

    # 测试私钥文件（裸 Base64）- 使用配置中的路径
    private_key_pem = load_key_content(ICBC_PAYMENT_CONFIG["private_key_path"])

    # 验证转换为 PEM 格式（工行密钥是 PKCS#8 格式）
    assert private_key_pem.startswith("-----BEGIN PRIVATE KEY-----")
    assert private_key_pem.endswith("-----END PRIVATE KEY-----")
    # 验证中间包含 Base64 内容
    assert "MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCcuLg1" in private_key_pem

    # 测试公钥文件（裸 Base64）- 使用配置中的路径
    public_key_pem = load_key_content(ICBC_PAYMENT_CONFIG["public_key_path"])

    # 验证转换为 PEM 格式
    assert public_key_pem.startswith("-----BEGIN PUBLIC KEY-----")
    assert public_key_pem.endswith("-----END PUBLIC KEY-----")
    # 验证中间包含 Base64 内容
    assert "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnLi4Nf" in public_key_pem


def test_load_key_content_with_pem_format():
    """测试加载已经是 PEM 格式的密钥"""
    from src.config.icbc_config import load_key_content
    import tempfile

    # 创建临时 PEM 格式文件
    pem_content = """-----BEGIN RSA PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCcuLg1/44hdfA
-----END RSA PRIVATE KEY-----"""

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as f:
        f.write(pem_content)
        temp_path = f.name

    try:
        result = load_key_content(temp_path)
        # 应该保持原样，不重复添加 BEGIN/END
        assert result.startswith("-----BEGIN RSA PRIVATE KEY-----")
        assert result.endswith("-----END RSA PRIVATE KEY-----")
    finally:
        os.unlink(temp_path)
