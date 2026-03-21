# -*- coding: utf-8 -*-
"""Kimi Provider 测试"""
import pytest
from src.infrastructure.providers.kimi_provider import KimiProvider


@pytest.fixture
def kimi_provider():
    """创建 Kimi Provider 测试实例"""
    return KimiProvider(api_key="test_key")


def test_supported_models(kimi_provider):
    """测试支持的模型列表"""
    models = kimi_provider.get_supported_models()
    assert "moonshot-v1-8k" in models
    assert "moonshot-v1-32k" in models
    assert "moonshot-v1-128k" in models


def test_provider_initialization(kimi_provider):
    """测试 Provider 初始化"""
    assert kimi_provider._base_url == "https://api.moonshot.cn"
    assert kimi_provider._api_key == "test_key"
