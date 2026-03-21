# -*- coding: utf-8 -*-
"""模型供应商配置服务单元测试"""
import pytest
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db_models import Base, ModelProviderModel, ModelConfigModel
from src.services.model_provider_service import ModelProviderService
from src.models import (
    CreateModelProviderRequest,
    UpdateModelProviderRequest,
    CreateModelConfigRequest,
    UpdateModelConfigRequest
)
from cryptography.fernet import Fernet


# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def set_encryption_key(monkeypatch):
    """设置测试用的加密密钥"""
    test_key = Fernet.generate_key().decode()
    monkeypatch.setenv("API_KEY_ENCRYPTION_KEY", test_key)


@pytest.fixture
def service(db_session):
    """创建服务实例"""
    return ModelProviderService(db_session)


class TestModelProviderService:
    """模型供应商配置服务测试类"""

    def test_create_provider(self, service):
        """测试创建供应商"""
        request = CreateModelProviderRequest(
            provider_code="openai",
            provider_name="OpenAI",
            api_key="sk-test-key-12345",
            base_url="https://api.openai.com/v1",
            is_enabled=True,
            order=1
        )

        provider = service.create_provider(request)

        assert provider.id is not None
        assert provider.provider_code == "openai"
        assert provider.provider_name == "OpenAI"
        assert provider.base_url == "https://api.openai.com/v1"
        assert provider.is_enabled is True
        assert provider.order == 1

    def test_create_duplicate_provider(self, service):
        """测试创建重复供应商（应该失败）"""
        request = CreateModelProviderRequest(
            provider_code="deepseek",
            provider_name="DeepSeek",
            api_key="sk-test-key-1"
        )

        service.create_provider(request)

        # 尝试创建相同代码的供应商
        with pytest.raises(ValueError, match="已存在"):
            service.create_provider(request)

    def test_get_all_providers(self, service):
        """测试获取所有供应商"""
        # 创建多个供应商
        providers_data = [
            ("openai", "OpenAI", "sk-key-1", 1),
            ("deepseek", "DeepSeek", "sk-key-2", 2),
            ("kimi", "Kimi", "sk-key-3", 3),
        ]

        for code, name, key, order in providers_data:
            request = CreateModelProviderRequest(
                provider_code=code,
                provider_name=name,
                api_key=key,
                order=order
            )
            service.create_provider(request)

        # 获取所有供应商
        providers = service.get_all_providers()

        assert len(providers) == 3
        assert providers[0].provider_code == "openai"
        assert providers[1].provider_code == "deepseek"
        assert providers[2].provider_code == "kimi"

    def test_get_all_providers_exclude_disabled(self, service):
        """测试获取供应商（排除已禁用）"""
        # 创建启用的供应商
        request1 = CreateModelProviderRequest(
            provider_code="openai",
            provider_name="OpenAI",
            api_key="sk-key-1",
            is_enabled=True
        )
        service.create_provider(request1)

        # 创建禁用的供应商
        request2 = CreateModelProviderRequest(
            provider_code="deepseek",
            provider_name="DeepSeek",
            api_key="sk-key-2",
            is_enabled=False
        )
        service.create_provider(request2)

        # 获取启用的供应商
        providers = service.get_all_providers(include_disabled=False)

        assert len(providers) == 1
        assert providers[0].provider_code == "openai"

        # 获取所有供应商
        all_providers = service.get_all_providers(include_disabled=True)

        assert len(all_providers) == 2

    def test_get_provider_by_id(self, service):
        """测试根据ID获取供应商"""
        request = CreateModelProviderRequest(
            provider_code="openai",
            provider_name="OpenAI",
            api_key="sk-test-key"
        )

        created = service.create_provider(request)
        found = service.get_provider_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.provider_code == "openai"

    def test_get_provider_by_code(self, service):
        """测试根据代码获取供应商"""
        request = CreateModelProviderRequest(
            provider_code="deepseek",
            provider_name="DeepSeek",
            api_key="sk-test-key"
        )

        service.create_provider(request)
        found = service.get_provider_by_code("deepseek")

        assert found is not None
        assert found.provider_code == "deepseek"
        assert found.provider_name == "DeepSeek"

    def test_get_default_provider(self, service):
        """测试获取默认供应商"""
        # 创建非默认供应商
        request1 = CreateModelProviderRequest(
            provider_code="openai",
            provider_name="OpenAI",
            api_key="sk-key-1",
            is_default=False
        )
        service.create_provider(request1)

        # 创建默认供应商
        request2 = CreateModelProviderRequest(
            provider_code="deepseek",
            provider_name="DeepSeek",
            api_key="sk-key-2",
            is_default=True
        )
        service.create_provider(request2)

        # 获取默认供应商
        default = service.get_default_provider()

        assert default is not None
        assert default.provider_code == "deepseek"
        assert default.is_default is True

    def test_update_provider(self, service):
        """测试更新供应商"""
        create_request = CreateModelProviderRequest(
            provider_code="openai",
            provider_name="OpenAI",
            api_key="sk-old-key",
            base_url="https://api.openai.com/v1"
        )

        created = service.create_provider(create_request)

        # 更新供应商
        update_request = UpdateModelProviderRequest(
            provider_name="OpenAI Updated",
            api_key="sk-new-key",
            base_url="https://new-api.openai.com/v1"
        )

        updated = service.update_provider(created.id, update_request)

        assert updated.provider_name == "OpenAI Updated"
        assert updated.base_url == "https://new-api.openai.com/v1"

    def test_set_default_provider(self, service):
        """测试设置默认供应商"""
        # 创建第一个默认供应商
        request1 = CreateModelProviderRequest(
            provider_code="openai",
            provider_name="OpenAI",
            api_key="sk-key-1",
            is_default=True
        )
        provider1 = service.create_provider(request1)

        # 创建第二个供应商并设置为默认
        request2 = CreateModelProviderRequest(
            provider_code="deepseek",
            provider_name="DeepSeek",
            api_key="sk-key-2",
            is_default=True
        )
        service.create_provider(request2)

        # 第一个供应商的默认标记应该被清除
        refreshed_provider1 = service.get_provider_by_id(provider1.id)
        assert refreshed_provider1.is_default is False

        # 新供应商应该是默认
        default = service.get_default_provider()
        assert default.provider_code == "deepseek"

    def test_delete_provider(self, service):
        """测试删除供应商"""
        request = CreateModelProviderRequest(
            provider_code="openai",
            provider_name="OpenAI",
            api_key="sk-test-key"
        )

        created = service.create_provider(request)
        provider_id = created.id

        # 删除供应商
        service.delete_provider(provider_id)

        # 验证已删除
        found = service.get_provider_by_id(provider_id)
        assert found is None

    def test_get_provider_api_key(self, service):
        """测试获取供应商 API Key（解密）"""
        request = CreateModelProviderRequest(
            provider_code="openai",
            provider_name="OpenAI",
            api_key="sk-secret-api-key-12345"
        )

        created = service.create_provider(request)
        api_key = service.get_provider_api_key(created.id)

        assert api_key == "sk-secret-api-key-12345"

    def test_create_model_config(self, service):
        """测试创建模型配置"""
        # 先创建供应商
        provider_request = CreateModelProviderRequest(
            provider_code="openai",
            provider_name="OpenAI",
            api_key="sk-test-key"
        )
        provider = service.create_provider(provider_request)

        # 创建模型配置
        model_request = CreateModelConfigRequest(
            provider_id=provider.id,
            model_code="gpt-4",
            model_name="GPT-4",
            capabilities="chat,code",
            is_enabled=True
        )

        model = service.create_model_config(model_request)

        assert model.id is not None
        assert model.provider_id == provider.id
        assert model.model_code == "gpt-4"
        assert model.model_name == "GPT-4"
        assert model.capabilities == ["chat", "code"]

    def test_create_model_config_invalid_provider(self, service):
        """测试创建模型配置（供应商不存在）"""
        request = CreateModelConfigRequest(
            provider_id="non-existent-id",
            model_code="gpt-4",
            model_name="GPT-4",
            capabilities="chat"
        )

        with pytest.raises(ValueError, match="不存在"):
            service.create_model_config(request)

    def test_get_all_models(self, service):
        """测试获取所有模型配置"""
        # 创建供应商
        provider_request = CreateModelProviderRequest(
            provider_code="openai",
            provider_name="OpenAI",
            api_key="sk-test-key"
        )
        provider = service.create_provider(provider_request)

        # 创建多个模型配置
        models_data = [
            ("gpt-4", "GPT-4", "chat"),
            ("gpt-3.5-turbo", "GPT-3.5 Turbo", "chat"),
            ("text-embedding-ada-002", "Ada Embedding", "embedding"),
        ]

        for code, name, caps in models_data:
            request = CreateModelConfigRequest(
                provider_id=provider.id,
                model_code=code,
                model_name=name,
                capabilities=caps
            )
            service.create_model_config(request)

        # 获取所有模型
        models = service.get_all_models()

        assert len(models) == 3
        model_codes = [m.model_code for m in models]
        assert "gpt-4" in model_codes
        assert "gpt-3.5-turbo" in model_codes
        assert "text-embedding-ada-002" in model_codes

    def test_get_models_by_provider(self, service):
        """测试根据供应商获取模型"""
        # 创建两个供应商
        provider1_request = CreateModelProviderRequest(
            provider_code="openai",
            provider_name="OpenAI",
            api_key="sk-key-1"
        )
        provider1 = service.create_provider(provider1_request)

        provider2_request = CreateModelProviderRequest(
            provider_code="deepseek",
            provider_name="DeepSeek",
            api_key="sk-key-2"
        )
        provider2 = service.create_provider(provider2_request)

        # 为第一个供应商创建模型
        model_request = CreateModelConfigRequest(
            provider_id=provider1.id,
            model_code="gpt-4",
            model_name="GPT-4",
            capabilities="chat"
        )
        service.create_model_config(model_request)

        # 获取第一个供应商的模型
        models = service.get_all_models(provider_id=provider1.id)

        assert len(models) == 1
        assert models[0].model_code == "gpt-4"

    def test_update_model_config(self, service):
        """测试更新模型配置"""
        # 创建供应商和模型
        provider_request = CreateModelProviderRequest(
            provider_code="openai",
            provider_name="OpenAI",
            api_key="sk-test-key"
        )
        provider = service.create_provider(provider_request)

        model_request = CreateModelConfigRequest(
            provider_id=provider.id,
            model_code="gpt-4",
            model_name="GPT-4",
            capabilities="chat"
        )
        created = service.create_model_config(model_request)

        # 更新模型配置
        update_request = UpdateModelConfigRequest(
            model_name="GPT-4 Turbo",
            capabilities="chat,code,image"
        )

        updated = service.update_model_config(created.id, update_request)

        assert updated.model_name == "GPT-4 Turbo"
        assert updated.capabilities == ["chat", "code", "image"]

    def test_delete_model_config(self, service):
        """测试删除模型配置"""
        # 创建供应商和模型
        provider_request = CreateModelProviderRequest(
            provider_code="openai",
            provider_name="OpenAI",
            api_key="sk-test-key"
        )
        provider = service.create_provider(provider_request)

        model_request = CreateModelConfigRequest(
            provider_id=provider.id,
            model_code="gpt-4",
            model_name="GPT-4",
            capabilities="chat"
        )
        created = service.create_model_config(model_request)
        model_id = created.id

        # 删除模型配置
        service.delete_model_config(model_id)

        # 验证已删除
        found = service.get_model_by_id(model_id)
        assert found is None

    def test_cascade_delete_provider(self, service):
        """测试级联删除供应商时同时删除模型配置"""
        # 创建供应商
        provider_request = CreateModelProviderRequest(
            provider_code="openai",
            provider_name="OpenAI",
            api_key="sk-test-key"
        )
        provider = service.create_provider(provider_request)

        # 创建模型配置
        model_request = CreateModelConfigRequest(
            provider_id=provider.id,
            model_code="gpt-4",
            model_name="GPT-4",
            capabilities="chat"
        )
        service.create_model_config(model_request)

        # 删除供应商（应该级联删除模型配置）
        service.delete_provider(provider.id)

        # 验证模型配置也被删除
        models = service.get_all_models(provider_id=provider.id)
        assert len(models) == 0
