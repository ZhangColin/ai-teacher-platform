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


class TestProviderFactoryRegistration:
    """测试 ProviderFactory 注册"""

    def test_newapi_is_registered(self):
        """测试 newapi 已注册到 ProviderFactory"""
        from src.infrastructure.providers.factory import ProviderFactory

        assert "newapi" in ProviderFactory.get_registered_providers()

    def test_is_provider_registered_returns_true(self):
        """测试 is_provider_registered 对 newapi 返回 True"""
        from src.infrastructure.providers.factory import ProviderFactory

        assert ProviderFactory.is_provider_registered("newapi") is True
        assert ProviderFactory.is_provider_registered("NewAPI") is True  # 大小写不敏感

    def test_create_newapi_provider(self):
        """测试通过工厂创建 NewAPIProvider"""
        from src.infrastructure.providers.factory import ProviderFactory

        provider = ProviderFactory.create(
            provider_name="newapi",
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

        assert isinstance(provider, NewAPIProvider)
        assert provider._api_key == "test-key"
        assert provider._base_url == "https://newapi.example.com/v1"

    def test_create_newapi_provider_case_insensitive(self):
        """测试创建 provider 时名称大小写不敏感"""
        from src.infrastructure.providers.factory import ProviderFactory

        provider1 = ProviderFactory.create(
            provider_name="newapi",
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )
        provider2 = ProviderFactory.create(
            provider_name="NewAPI",
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )
        provider3 = ProviderFactory.create(
            provider_name="NEWAPI",
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

        assert isinstance(provider1, NewAPIProvider)
        assert isinstance(provider2, NewAPIProvider)
        assert isinstance(provider3, NewAPIProvider)


class TestNewAPIProviderChatStream:
    """测试流式对话"""

    def setup_method(self):
        """每个测试前创建 provider 实例"""
        self.patcher = patch("src.infrastructure.providers.newapi_provider.AsyncOpenAI")
        self.mock_openai = self.patcher.start()
        self.provider = NewAPIProvider(
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

    def teardown_method(self):
        """每个测试后清理"""
        self.patcher.stop()

    @pytest.mark.asyncio
    async def test_chat_stream_yields_content(self):
        """测试流式对话返回内容"""
        # 创建 mock 流式响应
        async def mock_stream_generator():
            mock_chunk = Mock()
            mock_chunk.choices = [Mock()]
            mock_chunk.choices[0].delta.content = "Hello"
            yield mock_chunk

        mock_completion = Mock()
        mock_completion.create = Mock(return_value=mock_stream_generator())

        self.provider._client.chat.completions = mock_completion

        messages = [
            Message(
                id="1",
                session_id="session-1",
                role=MessageRole.USER,
                content="Hello",
                artifact=None,
                created_at=datetime.now()
            )
        ]

        result = []
        async for chunk in self.provider.chat_stream(messages, model="gpt-4"):
            result.append(chunk)

        assert result == ["Hello"]
        mock_completion.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            max_tokens=None,
            stream=True
        )

    @pytest.mark.asyncio
    async def test_chat_stream_with_temperature_and_max_tokens(self):
        """测试流式对话带温度和最大token参数"""
        async def mock_stream_generator():
            mock_chunk = Mock()
            mock_chunk.choices = [Mock()]
            mock_chunk.choices[0].delta.content = "Response"
            yield mock_chunk

        mock_completion = Mock()
        mock_completion.create = Mock(return_value=mock_stream_generator())

        self.provider._client.chat.completions = mock_completion

        messages = [
            Message(
                id="1",
                session_id="session-1",
                role=MessageRole.USER,
                content="Test",
                artifact=None,
                created_at=datetime.now()
            )
        ]

        async for _ in self.provider.chat_stream(
            messages,
            model="gpt-4",
            temperature=0.5,
            max_tokens=1000
        ):
            pass

        mock_completion.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "Test"}],
            temperature=0.5,
            max_tokens=1000,
            stream=True
        )

    @pytest.mark.asyncio
    async def test_chat_stream_handles_empty_chunks(self):
        """测试流式对话处理空内容块"""
        async def mock_stream_generator():
            # 空内容块
            mock_chunk_empty = Mock()
            mock_chunk_empty.choices = [Mock()]
            mock_chunk_empty.choices[0].delta.content = None
            yield mock_chunk_empty

            # 有内容块
            mock_chunk_content = Mock()
            mock_chunk_content.choices = [Mock()]
            mock_chunk_content.choices[0].delta.content = "Hello"
            yield mock_chunk_content

        mock_completion = Mock()
        mock_completion.create = Mock(return_value=mock_stream_generator())

        self.provider._client.chat.completions = mock_completion

        messages = [
            Message(
                id="1",
                session_id="session-1",
                role=MessageRole.USER,
                content="Test",
                artifact=None,
                created_at=datetime.now()
            )
        ]

        result = []
        async for chunk in self.provider.chat_stream(messages, model="gpt-4"):
            result.append(chunk)

        assert result == ["Hello"]

    @pytest.mark.asyncio
    async def test_chat_stream_handles_exception(self):
        """测试流式对话处理异常"""
        mock_completion = Mock()
        mock_completion.create = Mock(side_effect=Exception("API Error"))
        self.provider._client.chat.completions = mock_completion

        messages = [
            Message(
                id="1",
                session_id="session-1",
                role=MessageRole.USER,
                content="Test",
                artifact=None,
                created_at=datetime.now()
            )
        ]

        with pytest.raises(Exception, match="API Error"):
            async for _ in self.provider.chat_stream(messages, model="gpt-4"):
                pass


class TestNewAPIProviderChat:
    """测试非流式对话"""

    def setup_method(self):
        """每个测试前创建 provider 实例"""
        self.patcher = patch("src.infrastructure.providers.newapi_provider.AsyncOpenAI")
        self.patcher.start()
        self.provider = NewAPIProvider(
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

    def teardown_method(self):
        """每个测试后清理"""
        self.patcher.stop()

    @pytest.mark.asyncio
    async def test_chat_returns_response_content(self):
        """测试非流式对话返回响应内容"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello, human!"

        mock_completion = AsyncMock()
        mock_completion.create = AsyncMock(return_value=mock_response)
        self.provider._client.chat.completions = mock_completion

        messages = [
            Message(
                id="1",
                session_id="session-1",
                role=MessageRole.USER,
                content="Hello",
                artifact=None,
                created_at=datetime.now()
            )
        ]

        result = await self.provider.chat(messages, model="gpt-4")

        assert result == "Hello, human!"
        mock_completion.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            max_tokens=None,
            stream=False
        )

    @pytest.mark.asyncio
    async def test_chat_with_parameters(self):
        """测试非流式对话带参数"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response"

        mock_completion = AsyncMock()
        mock_completion.create = AsyncMock(return_value=mock_response)
        self.provider._client.chat.completions = mock_completion

        messages = [
            Message(
                id="1",
                session_id="session-1",
                role=MessageRole.USER,
                content="Test",
                artifact=None,
                created_at=datetime.now()
            )
        ]

        result = await self.provider.chat(
            messages,
            model="gpt-4",
            temperature=0.3,
            max_tokens=500
        )

        assert result == "Response"
        mock_completion.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "Test"}],
            temperature=0.3,
            max_tokens=500,
            stream=False
        )

    @pytest.mark.asyncio
    async def test_chat_handles_exception(self):
        """测试非流式对话处理异常"""
        mock_completion = AsyncMock()
        mock_completion.create = AsyncMock(side_effect=Exception("API Error"))
        self.provider._client.chat.completions = mock_completion

        messages = [
            Message(
                id="1",
                session_id="session-1",
                role=MessageRole.USER,
                content="Test",
                artifact=None,
                created_at=datetime.now()
            )
        ]

        with pytest.raises(Exception, match="API Error"):
            await self.provider.chat(messages, model="gpt-4")


class TestNewAPIProviderImageGeneration:
    """测试图片生成"""

    def setup_method(self):
        """每个测试前创建 provider 实例"""
        self.patcher = patch("src.infrastructure.providers.newapi_provider.AsyncOpenAI")
        self.patcher.start()
        self.provider = NewAPIProvider(
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

    def teardown_method(self):
        """每个测试后清理"""
        self.patcher.stop()

    @pytest.mark.asyncio
    async def test_generate_image_returns_url(self):
        """测试图片生成返回URL"""
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].url = "https://example.com/image.png"

        mock_images = AsyncMock()
        mock_images.generate = AsyncMock(return_value=mock_response)
        self.provider._client.images = mock_images

        result = await self.provider.generate_image(
            prompt="A beautiful sunset",
            size="1024x1024"
        )

        assert result == "https://example.com/image.png"
        mock_images.generate.assert_called_once_with(
            model="dall-e-3",
            prompt="A beautiful sunset",
            size="1024x1024"
        )

    @pytest.mark.asyncio
    async def test_generate_image_with_custom_size(self):
        """测试图片生成带自定义尺寸"""
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].url = "https://example.com/image.png"

        mock_images = AsyncMock()
        mock_images.generate = AsyncMock(return_value=mock_response)
        self.provider._client.images = mock_images

        result = await self.provider.generate_image(
            prompt="A cat",
            size="512x512"
        )

        assert result == "https://example.com/image.png"
        mock_images.generate.assert_called_once_with(
            model="dall-e-3",
            prompt="A cat",
            size="512x512"
        )

    @pytest.mark.asyncio
    async def test_generate_image_handles_exception(self):
        """测试图片生成处理异常"""
        mock_images = AsyncMock()
        mock_images.generate = AsyncMock(side_effect=Exception("Image API Error"))
        self.provider._client.images = mock_images

        with pytest.raises(Exception, match="Image API Error"):
            await self.provider.generate_image(prompt="Test image")


class TestNewAPIProviderAudioGeneration:
    """测试音频生成"""

    def setup_method(self):
        """每个测试前创建 provider 实例"""
        self.patcher = patch("src.infrastructure.providers.newapi_provider.AsyncOpenAI")
        self.patcher.start()
        self.provider = NewAPIProvider(
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

    def teardown_method(self):
        """每个测试后清理"""
        self.patcher.stop()

    @pytest.mark.asyncio
    async def test_generate_audio_returns_base64(self):
        """测试音频生成返回base64编码"""
        # 模拟音频内容
        audio_bytes = b"fake audio content"

        mock_response = Mock()
        mock_response.content = audio_bytes

        mock_audio = AsyncMock()
        mock_audio.speech = Mock()
        mock_audio.speech.create = AsyncMock(return_value=mock_response)
        self.provider._client.audio = mock_audio

        result = await self.provider.generate_audio(
            text="Hello, world!",
            voice="alloy"
        )

        assert result.startswith("data:audio/mp3;base64,")
        # 验证base64编码正确
        import base64
        expected_prefix = "data:audio/mp3;base64,"
        assert result.startswith(expected_prefix)
        base64_part = result[len(expected_prefix):]
        decoded = base64.b64decode(base64_part)
        assert decoded == audio_bytes

        mock_audio.speech.create.assert_called_once_with(
            model="tts-1",
            voice="alloy",
            input="Hello, world!"
        )

    @pytest.mark.asyncio
    async def test_generate_audio_with_custom_voice(self):
        """测试音频生成带自定义音色"""
        audio_bytes = b"audio data"

        mock_response = Mock()
        mock_response.content = audio_bytes

        mock_audio = AsyncMock()
        mock_audio.speech = Mock()
        mock_audio.speech.create = AsyncMock(return_value=mock_response)
        self.provider._client.audio = mock_audio

        result = await self.provider.generate_audio(
            text="Test",
            voice="echo"
        )

        assert result.startswith("data:audio/mp3;base64,")
        mock_audio.speech.create.assert_called_once_with(
            model="tts-1",
            voice="echo",
            input="Test"
        )

    @pytest.mark.asyncio
    async def test_generate_audio_handles_exception(self):
        """测试音频生成处理异常"""
        mock_audio = AsyncMock()
        mock_audio.speech = Mock()
        mock_audio.speech.create = AsyncMock(side_effect=Exception("Audio API Error"))
        self.provider._client.audio = mock_audio

        with pytest.raises(Exception, match="Audio API Error"):
            await self.provider.generate_audio(text="Test")


class TestNewAPIProviderRoleConversion:
    """测试角色转换边缘情况"""

    def setup_method(self):
        """每个测试前创建 provider 实例"""
        with patch("src.infrastructure.providers.newapi_provider.AsyncOpenAI"):
            self.provider = NewAPIProvider(
                api_key="test-key",
                base_url="https://newapi.example.com/v1"
            )

    def test_convert_role_unknown_fallback_to_user(self):
        """测试未知角色回退到user"""
        # 创建一个非标准角色的 Mock
        class UnknownRole:
            def is_system_message(self):
                return False
            def is_user_message(self):
                return False
            def is_assistant_message(self):
                return False

        unknown_role = UnknownRole()
        result = self.provider._convert_role(unknown_role)

        # 根据代码逻辑，未知角色应回退到 "user"
        assert result == "user"
