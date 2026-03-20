import pytest
from src.services.builtin_models import (
    get_builtin_providers,
    get_builtin_models,
    validate_provider_code,
    validate_model_code,
    BUILTIN_PROVIDERS,
    ALL_CAPABILITIES
)


def test_get_builtin_providers():
    """测试获取内置供应商列表"""
    providers = get_builtin_providers()
    assert len(providers) == 4
    assert any(p["code"] == "deepseek" for p in providers)
    assert any(p["code"] == "openai" for p in providers)


def test_get_builtin_models_all():
    """测试获取所有内置模型"""
    models = get_builtin_models()
    assert len(models) > 0
    assert any(m["code"] == "deepseek-chat" for m in models)


def test_get_builtin_models_by_provider():
    """测试按供应商获取模型"""
    models = get_builtin_models("deepseek")
    assert len(models) == 2
    assert any(m["code"] == "deepseek-chat" for m in models)


def test_validate_provider_code():
    """测试供应商代码验证"""
    assert validate_provider_code("deepseek") is True
    assert validate_provider_code("invalid") is False


def test_validate_model_code():
    """测试模型代码验证"""
    assert validate_model_code("deepseek", "deepseek-chat") is True
    assert validate_model_code("deepseek", "invalid") is False
    assert validate_model_code("invalid", "deepseek-chat") is False


def test_all_capabilities():
    """测试能力列表"""
    assert "chat" in ALL_CAPABILITIES
    assert "image" in ALL_CAPABILITIES
    assert "audio" in ALL_CAPABILITIES
    assert "video" in ALL_CAPABILITIES