# -*- coding: utf-8 -*-
"""TitleGenerator 单元测试"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from sqlalchemy.orm import Session
from src.services.title_generator import TitleGenerator


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def mock_model_provider_service():
    """模拟 ModelProviderService"""
    with patch("src.services.title_generator.ModelProviderService") as mock:
        yield mock


class TestTitleGenerator:
    """TitleGenerator 测试类"""

    def test_init_with_db(self, mock_db, mock_model_provider_service):
        """测试初始化 - 带数据库会话"""
        generator = TitleGenerator(mock_db)
        assert generator.db == mock_db
        mock_model_provider_service.assert_called_once_with(mock_db)

    def test_get_ai_client_success(self, mock_db, mock_model_provider_service):
        """测试获取 AI 客户端 - 成功"""
        # 模拟供应商配置
        mock_provider = MagicMock()
        mock_provider.id = 1
        mock_provider.is_enabled = True
        mock_provider.base_url = "https://api.test.com"

        mock_model_provider_service.return_value.get_provider_by_code.return_value = mock_provider
        mock_model_provider_service.return_value.get_provider_api_key.return_value = "sk-test123"

        with patch("src.services.title_generator.OpenAI") as mock_openai:
            generator = TitleGenerator(mock_db)
            client = generator._get_ai_client("test_provider", "test_model")

            mock_openai.assert_called_once()
            assert client is not None

    def test_get_ai_client_provider_not_found(self, mock_db, mock_model_provider_service):
        """测试获取 AI 客户端 - 供应商不存在"""
        mock_model_provider_service.return_value.get_provider_by_code.return_value = None

        generator = TitleGenerator(mock_db)
        client = generator._get_ai_client("unknown_provider", "test_model")

        assert client is None

    def test_get_ai_client_provider_disabled(self, mock_db, mock_model_provider_service):
        """测试获取 AI 客户端 - 供应商已禁用"""
        mock_provider = MagicMock()
        mock_provider.is_enabled = False

        mock_model_provider_service.return_value.get_provider_by_code.return_value = mock_provider

        generator = TitleGenerator(mock_db)
        client = generator._get_ai_client("test_provider", "test_model")

        assert client is None

    def test_get_ai_client_exception(self, mock_db, mock_model_provider_service):
        """测试获取 AI 客户端 - 异常情况"""
        mock_model_provider_service.return_value.get_provider_by_code.side_effect = Exception("DB Error")

        generator = TitleGenerator(mock_db)
        client = generator._get_ai_client("test_provider", "test_model")

        assert client is None

    @pytest.mark.asyncio
    async def test_generate_title_empty_user_message(self, mock_db, mock_model_provider_service):
        """测试生成标题 - 空用户消息"""
        generator = TitleGenerator(mock_db)
        title = await generator.generate_title("")
        assert title == "新对话"

    @pytest.mark.asyncio
    async def test_generate_title_no_model_specified(self, mock_db, mock_model_provider_service):
        """测试生成标题 - 未指定模型"""
        generator = TitleGenerator(mock_db)
        title = await generator.generate_title("测试消息")
        assert title == "测试消息"  # 使用降级方案

    @pytest.mark.asyncio
    async def test_generate_title_client_not_available(self, mock_db, mock_model_provider_service):
        """测试生成标题 - 客户端不可用"""
        mock_model_provider_service.return_value.get_provider_by_code.return_value = None

        generator = TitleGenerator(mock_db)
        title = await generator.generate_title(
            user_message="测试消息",
            model_provider="test_provider",
            model_name="test_model"
        )
        assert title == "测试消息"  # 使用降级方案

    @pytest.mark.asyncio
    async def test_generate_title_short_message_with_ai_response(self, mock_db, mock_model_provider_service):
        """测试生成标题 - 短消息+AI回复"""
        # 模拟供应商配置
        mock_provider = MagicMock()
        mock_provider.id = 1
        mock_provider.is_enabled = True
        mock_provider.base_url = "https://api.test.com"

        mock_model_provider_service.return_value.get_provider_by_code.return_value = mock_provider
        mock_model_provider_service.return_value.get_provider_api_key.return_value = "sk-test123"

        # 模拟 OpenAI 客户端响应
        with patch("src.services.title_generator.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content.strip.return_value = "生成的标题"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            generator = TitleGenerator(mock_db)
            title = await generator.generate_title(
                user_message="短",
                ai_response="这是AI的回复内容" * 100,
                model_provider="test_provider",
                model_name="test_model"
            )

            assert title == "生成的标题"
            # 验证调用了AI
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args
            assert "短" in call_args[1]["messages"][0]["content"]
            assert "这是AI的回复内容" in call_args[1]["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_generate_title_long_message(self, mock_db, mock_model_provider_service):
        """测试生成标题 - 长消息"""
        # 模拟供应商配置
        mock_provider = MagicMock()
        mock_provider.id = 1
        mock_provider.is_enabled = True
        mock_provider.base_url = "https://api.test.com"

        mock_model_provider_service.return_value.get_provider_by_code.return_value = mock_provider
        mock_model_provider_service.return_value.get_provider_api_key.return_value = "sk-test123"

        # 模拟 OpenAI 客户端响应
        with patch("src.services.title_generator.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content.strip.return_value = "长消息标题"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            generator = TitleGenerator(mock_db)
            long_msg = "这是一个很长的用户消息" * 100
            title = await generator.generate_title(
                user_message=long_msg,
                model_provider="test_provider",
                model_name="test_model"
            )

            assert title == "长消息标题"
            # 验证消息被截断到500字符
            call_args = mock_client.chat.completions.create.call_args
            prompt = call_args[1]["messages"][0]["content"]
            # 验证prompt包含用户消息（但被截断）
            assert "这是一个很长的用户消息" in prompt

    @pytest.mark.asyncio
    async def test_generate_title_ai_failure(self, mock_db, mock_model_provider_service):
        """测试生成标题 - AI调用失败"""
        # 模拟供应商配置
        mock_provider = MagicMock()
        mock_provider.id = 1
        mock_provider.is_enabled = True
        mock_provider.base_url = "https://api.test.com"

        mock_model_provider_service.return_value.get_provider_by_code.return_value = mock_provider
        mock_model_provider_service.return_value.get_provider_api_key.return_value = "sk-test123"

        # 模拟 OpenAI 客户端抛出异常
        with patch("src.services.title_generator.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("AI错误")
            mock_openai.return_value = mock_client

            generator = TitleGenerator(mock_db)
            title = await generator.generate_title(
                user_message="测试消息",
                model_provider="test_provider",
                model_name="test_model"
            )

            # 应该降级到简单截取
            assert title == "测试消息"

    @pytest.mark.asyncio
    async def test_generate_title_empty_ai_response(self, mock_db, mock_model_provider_service):
        """测试生成标题 - AI返回空内容"""
        # 模拟供应商配置
        mock_provider = MagicMock()
        mock_provider.id = 1
        mock_provider.is_enabled = True
        mock_provider.base_url = "https://api.test.com"

        mock_model_provider_service.return_value.get_provider_by_code.return_value = mock_provider
        mock_model_provider_service.return_value.get_provider_api_key.return_value = "sk-test123"

        # 模拟 OpenAI 客户端返回空内容
        with patch("src.services.title_generator.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content.strip.return_value = ""
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            generator = TitleGenerator(mock_db)
            title = await generator.generate_title(
                user_message="测试",
                model_provider="test_provider",
                model_name="test_model"
            )

            assert title == "新对话"

    @pytest.mark.asyncio
    async def test_generate_title_too_long(self, mock_db, mock_model_provider_service):
        """测试生成标题 - AI返回过长的标题"""
        # 模拟供应商配置
        mock_provider = MagicMock()
        mock_provider.id = 1
        mock_provider.is_enabled = True
        mock_provider.base_url = "https://api.test.com"

        mock_model_provider_service.return_value.get_provider_by_code.return_value = mock_provider
        mock_model_provider_service.return_value.get_provider_api_key.return_value = "sk-test123"

        # 模拟 OpenAI 客户端返回超长标题
        with patch("src.services.title_generator.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            # 返回超过30字符的标题
            long_title = "这是一个非常非常非常非常非常非常长的标题超过了三十个字符的限制"
            mock_message.content.strip.return_value = long_title
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            generator = TitleGenerator(mock_db)
            title = await generator.generate_title(
                user_message="测试",
                model_provider="test_provider",
                model_name="test_model"
            )

            # 应该被截断到30字符
            assert len(title) == 30
            assert title == "这是一个非常非常非常非常非常非常长的标题超过了三十个字符的限"

    @pytest.mark.asyncio
    async def test_generate_title_no_ai_response(self, mock_db, mock_model_provider_service):
        """测试生成标题 - 没有AI回复（短消息）"""
        # 模拟供应商配置
        mock_provider = MagicMock()
        mock_provider.id = 1
        mock_provider.is_enabled = True
        mock_provider.base_url = "https://api.test.com"

        mock_model_provider_service.return_value.get_provider_by_code.return_value = mock_provider
        mock_model_provider_service.return_value.get_provider_api_key.return_value = "sk-test123"

        # 模拟 OpenAI 客户端响应
        with patch("src.services.title_generator.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content.strip.return_value = "测试标题"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            generator = TitleGenerator(mock_db)
            title = await generator.generate_title(
                user_message="短",
                ai_response=None,
                model_provider="test_provider",
                model_name="test_model"
            )

            assert title == "测试标题"

    def test_clean_title_removes_punctuation(self, mock_db, mock_model_provider_service):
        """测试清理标题 - 移除标点符号"""
        generator = TitleGenerator(mock_db)
        title = generator._clean_title('测试"标题"，包含【标点】符号！')
        assert '"' not in title
        assert '，' not in title
        assert '【' not in title
        assert '】' not in title
        assert '！' not in title
        assert title == "测试标题包含标点符号"

    def test_clean_title_empty(self, mock_db, mock_model_provider_service):
        """测试清理标题 - 空字符串"""
        generator = TitleGenerator(mock_db)
        title = generator._clean_title("")
        assert title == ""

    def test_fallback_title_empty_message(self, mock_db, mock_model_provider_service):
        """测试降级标题生成 - 空消息"""
        generator = TitleGenerator(mock_db)
        title = generator._fallback_title("")
        assert title == "新对话"

    def test_fallback_title_short_message(self, mock_db, mock_model_provider_service):
        """测试降级标题生成 - 短消息"""
        generator = TitleGenerator(mock_db)
        title = generator._fallback_title("测试标题")
        assert title == "测试标题"

    def test_fallback_title_long_message(self, mock_db, mock_model_provider_service):
        """测试降级标题生成 - 长消息"""
        generator = TitleGenerator(mock_db)
        long_msg = "这是一个很长的消息内容" * 10  # 超过30字符
        title = generator._fallback_title(long_msg)
        assert len(title) == 30
        assert title == long_msg[:30]

    def test_fallback_title_with_newlines(self, mock_db, mock_model_provider_service):
        """测试降级标题生成 - 包含换行符"""
        generator = TitleGenerator(mock_db)
        title = generator._fallback_title("第一行\n第二行\r第三行")
        assert "\n" not in title
        assert "\r" not in title
        assert " " in title
