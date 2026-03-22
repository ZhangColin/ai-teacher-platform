"""测试 Gemini 适配器"""
import pytest

from src.services.llm.gemini_adapter import GeminiAdapter


class TestGeminiAdapter:
    """测试 Gemini 适配器"""

    def test_init(self):
        """测试初始化"""
        adapter = GeminiAdapter(api_key="test-key")
        assert adapter.api_key == "test-key"
        assert adapter.client is not None

    def test_to_gemini_format(self):
        """测试消息格式转换"""
        adapter = GeminiAdapter(api_key="test-key")
        messages = [
            {"role": "user", "content": "hello"}
        ]
        result = adapter._to_gemini_format(messages, None)
        assert len(result) == 1
        assert result[0].role == "user"
        assert result[0].parts[0].text == "hello"

    def test_to_gemini_format_filters_system_messages(self):
        """测试过滤系统消息（Gemini 使用特殊方式处理系统提示词）"""
        adapter = GeminiAdapter(api_key="test-key")
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "hello"}
        ]
        result = adapter._to_gemini_format(messages, None)
        # 系统消息应该被过滤掉
        assert len(result) == 1
        assert result[0].role == "user"
        assert result[0].parts[0].text == "hello"

    def test_to_gemini_format_converts_assistant_to_model(self):
        """测试将 assistant 角色转换为 model"""
        adapter = GeminiAdapter(api_key="test-key")
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"}
        ]
        result = adapter._to_gemini_format(messages, None)
        assert len(result) == 2
        assert result[0].role == "user"
        assert result[1].role == "model"
        assert result[1].parts[0].text == "hi there"

    def test_extract_content_with_valid_response(self):
        """测试从有效响应提取内容"""
        adapter = GeminiAdapter(api_key="test-key")

        # Mock 响应
        class MockPart:
            text = "Hello world"

        class MockContent:
            parts = [MockPart()]

        class MockCandidate:
            content = MockContent()

        class MockResponse:
            candidates = [MockCandidate()]

        content = adapter._extract_content(MockResponse())
        assert content == "Hello world"

    def test_extract_content_with_none_response(self):
        """测试从 None 响应提取内容（返回空字符串）"""
        adapter = GeminiAdapter(api_key="test-key")
        content = adapter._extract_content(None)
        assert content == ""

    def test_extract_content_with_empty_candidates(self):
        """测试从空候选列表提取内容"""
        adapter = GeminiAdapter(api_key="test-key")

        class MockResponse:
            candidates = []

        content = adapter._extract_content(MockResponse())
        assert content == ""

    def test_extract_usage_with_valid_response(self):
        """测试从有效响应提取 usage"""
        adapter = GeminiAdapter(api_key="test-key")

        # Mock Gemini usage metadata
        class MockUsageMetadata:
            prompt_token_count = 10
            candidates_token_count = 20
            total_token_count = 30

        class MockResponse:
            usage_metadata = MockUsageMetadata()

        usage = adapter._extract_usage(MockResponse(), "gemini-2.0-flash")
        assert usage['prompt_tokens'] == 10
        assert usage['completion_tokens'] == 20
        assert usage['total_tokens'] == 30
        assert usage['model_provider'] == 'google'
        assert usage['model_name'] == 'gemini-2.0-flash'

    def test_extract_usage_with_partial_metadata(self):
        """测试从部分缺失的 metadata 提取 usage"""
        adapter = GeminiAdapter(api_key="test-key")

        # 只有部分字段的 metadata
        class MockPartialMetadata:
            prompt_token_count = 10
            # 缺少其他字段

        class MockResponse:
            usage_metadata = MockPartialMetadata()

        usage = adapter._extract_usage(MockResponse(), "gemini-pro")
        assert usage['prompt_tokens'] == 10
        assert usage['completion_tokens'] == 0
        assert usage['total_tokens'] == 0
        assert usage['model_provider'] == 'google'

    def test_extract_usage_with_none_response(self):
        """测试从 None 响应提取 usage（返回默认值）"""
        adapter = GeminiAdapter(api_key="test-key")

        usage = adapter._extract_usage(None, "gemini-pro")
        assert usage['prompt_tokens'] == 0
        assert usage['completion_tokens'] == 0
        assert usage['total_tokens'] == 0
        assert usage['model_provider'] == 'google'
        assert usage['model_name'] == 'gemini-pro'

    def test_extract_usage_with_response_without_metadata(self):
        """测试响应没有 usage_metadata 属性时返回默认值"""
        adapter = GeminiAdapter(api_key="test-key")

        # Mock response without usage_metadata
        class MockResponse:
            pass

        mock_response = MockResponse()
        usage = adapter._extract_usage(mock_response, "gemini-pro")
        assert usage['prompt_tokens'] == 0
        assert usage['model_provider'] == 'google'

    def test_extra_config_storage(self):
        """测试额外配置的存储"""
        adapter = GeminiAdapter(
            api_key="test-key",
            custom_param="value"
        )
        assert adapter.extra_config['custom_param'] == 'value'
