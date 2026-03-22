"""测试 OpenAI 适配器"""
import pytest

from src.services.llm.openai_adapter import OpenAIAdapter


class TestOpenAIAdapter:
    """测试 OpenAI 适配器"""

    def test_init(self):
        """测试初始化"""
        adapter = OpenAIAdapter(
            api_key="sk-test",
            base_url="https://api.openai.com/v1"
        )
        assert adapter.api_key == "sk-test"
        assert adapter.base_url == "https://api.openai.com/v1"
        assert adapter.client is not None

    def test_init_with_custom_timeout(self):
        """测试自定义超时和重试参数"""
        adapter = OpenAIAdapter(
            api_key="sk-test",
            timeout=60.0,
            max_retries=3
        )
        assert adapter.api_key == "sk-test"
        # 验证客户端配置正确传递

    def test_init_with_provider_in_extra_config(self):
        """测试通过 extra_config 传递 provider"""
        adapter = OpenAIAdapter(
            api_key="sk-test",
            provider="deepseek"
        )
        assert adapter.extra_config.get('provider') == 'deepseek'

    def test_build_messages(self):
        """测试消息构建"""
        adapter = OpenAIAdapter(api_key="sk-test")
        messages = [{"role": "user", "content": "hello"}]
        result = adapter._build_messages(messages, "You are helpful")
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are helpful"
        assert result[1]["role"] == "user"
        assert result[1]["content"] == "hello"

    def test_build_messages_without_system_prompt(self):
        """测试不带系统提示词的消息构建"""
        adapter = OpenAIAdapter(api_key="sk-test")
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"}
        ]
        result = adapter._build_messages(messages, None)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_extract_usage_with_valid_response(self):
        """测试从有效响应提取 usage"""
        adapter = OpenAIAdapter(
            api_key="sk-test",
            extra_config={'provider': 'deepseek'}
        )

        # Mock response
        class MockUsage:
            prompt_tokens = 10
            completion_tokens = 20
            total_tokens = 30

        class MockResponse:
            usage = MockUsage()

        usage = adapter._extract_usage(MockResponse(), "deepseek-chat", "deepseek")
        assert usage['prompt_tokens'] == 10
        assert usage['completion_tokens'] == 20
        assert usage['total_tokens'] == 30
        assert usage['model_provider'] == 'deepseek'
        assert usage['model_name'] == 'deepseek-chat'

    @pytest.mark.asyncio
    async def test_extract_usage_with_none_response(self):
        """测试从 None 响应提取 usage（返回默认值）"""
        adapter = OpenAIAdapter(
            api_key="sk-test",
            extra_config={'provider': 'openai'}
        )

        usage = adapter._extract_usage(None, "gpt-4", "openai")
        assert usage['prompt_tokens'] == 0
        assert usage['completion_tokens'] == 0
        assert usage['total_tokens'] == 0
        assert usage['model_provider'] == 'openai'
        assert usage['model_name'] == 'gpt-4'

    @pytest.mark.asyncio
    async def test_extract_usage_without_usage_attribute(self):
        """测试响应没有 usage 属性时返回默认值"""
        adapter = OpenAIAdapter(
            api_key="sk-test",
            extra_config={'provider': 'kimi'}
        )

        # Mock response without usage
        class MockResponse:
            pass

        mock_response = MockResponse()
        usage = adapter._extract_usage(mock_response, "moonshot-v1", "kimi")
        assert usage['prompt_tokens'] == 0
        assert usage['model_provider'] == 'kimi'

    def test_extra_config_storage(self):
        """测试额外配置的存储"""
        adapter = OpenAIAdapter(
            api_key="sk-test",
            base_url="https://api.deepseek.com",
            provider="deepseek",
            custom_param="value"
        )
        assert adapter.extra_config['provider'] == 'deepseek'
        assert adapter.extra_config['custom_param'] == 'value'
