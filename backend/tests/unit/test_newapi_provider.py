"""
NewAPIProvider 单元测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.infrastructure.providers.newapi_provider import NewAPIProvider
from src.domain.entities.message import Message
from src.domain.value_objects.message_role import MessageRole
from datetime import datetime


class TestNewAPIProviderInit:
    """测试 NewAPIProvider 初始化"""

    @patch("src.infrastructure.providers.newapi_provider.AsyncOpenAI")
    def test_init_with_base_url(self, mock_openai):
        """测试使用 base_url 初始化"""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        provider = NewAPIProvider(
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

        assert provider._api_key == "test-key"
        assert provider._base_url == "https://newapi.example.com/v1"
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

    @patch("src.infrastructure.providers.newapi_provider.AsyncOpenAI")
    def test_init_creates_client(self, mock_openai):
        """测试初始化时创建 OpenAI 客户端"""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        provider = NewAPIProvider(
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

        assert provider._client == mock_client

    @patch("src.infrastructure.providers.newapi_provider.AsyncOpenAI")
    def test_get_supported_models_returns_empty_list(self, mock_openai):
        """测试 get_supported_models 返回空列表（模型由数据库管理）"""
        mock_openai.return_value = Mock()

        provider = NewAPIProvider(
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

        assert provider.get_supported_models() == []
