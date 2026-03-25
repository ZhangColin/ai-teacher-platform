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


class TestNewAPIProviderMessageConversion:
    """测试消息格式转换"""

    def setup_method(self):
        """每个测试前创建 provider 实例"""
        with patch("src.infrastructure.providers.newapi_provider.AsyncOpenAI"):
            self.provider = NewAPIProvider(
                api_key="test-key",
                base_url="https://newapi.example.com/v1"
            )

    def test_convert_user_message(self):
        """测试转换用户消息"""
        message = Message(
            id="1",
            session_id="session-1",
            role=MessageRole.USER,
            content="Hello, AI!",
            artifact=None,
            created_at=datetime.now()
        )

        result = self.provider._convert_messages([message])

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello, AI!"

    def test_convert_assistant_message(self):
        """测试转换助手消息"""
        message = Message(
            id="2",
            session_id="session-1",
            role=MessageRole.ASSISTANT,
            content="Hello, human!",
            artifact=None,
            created_at=datetime.now()
        )

        result = self.provider._convert_messages([message])

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "Hello, human!"

    def test_convert_system_message(self):
        """测试转换系统消息"""
        message = Message(
            id="3",
            session_id="session-1",
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant.",
            artifact=None,
            created_at=datetime.now()
        )

        result = self.provider._convert_messages([message])

        assert len(result) == 1
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are a helpful assistant."

    def test_convert_multiple_messages(self):
        """测试转换多条消息"""
        messages = [
            Message(
                id="1",
                session_id="session-1",
                role=MessageRole.SYSTEM,
                content="You are helpful.",
                artifact=None,
                created_at=datetime.now()
            ),
            Message(
                id="2",
                session_id="session-1",
                role=MessageRole.USER,
                content="Hello!",
                artifact=None,
                created_at=datetime.now()
            ),
            Message(
                id="3",
                session_id="session-1",
                role=MessageRole.ASSISTANT,
                content="Hi there!",
                artifact=None,
                created_at=datetime.now()
            ),
        ]

        result = self.provider._convert_messages(messages)

        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[2]["role"] == "assistant"

    def test_convert_role_user(self):
        """测试 role 转换 - user"""
        assert self.provider._convert_role(MessageRole.USER) == "user"

    def test_convert_role_assistant(self):
        """测试 role 转换 - assistant"""
        assert self.provider._convert_role(MessageRole.ASSISTANT) == "assistant"

    def test_convert_role_system(self):
        """测试 role 转换 - system"""
        assert self.provider._convert_role(MessageRole.SYSTEM) == "system"
