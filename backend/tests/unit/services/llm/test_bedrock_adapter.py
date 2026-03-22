"""测试 Bedrock 适配器"""
import pytest

from src.services.llm.bedrock_adapter import BedrockAdapter


class TestBedrockAdapter:
    """测试 Bedrock 适配器"""

    def test_init(self):
        """测试初始化"""
        adapter = BedrockAdapter(
            api_key="AKIAIOSFODNN7EXAMPLE",
            base_url="us-east-1",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        )
        assert adapter.region == "us-east-1"
        assert adapter.api_key == "AKIAIOSFODNN7EXAMPLE"
        assert adapter.aws_secret_key == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

    def test_init_with_default_region(self):
        """测试使用默认区域初始化"""
        adapter = BedrockAdapter(
            api_key="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        )
        assert adapter.region == "us-east-1"

    def test_to_bedrock_format(self):
        """测试消息格式转换"""
        adapter = BedrockAdapter(
            api_key="test",
            aws_secret_access_key="test"
        )
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"}
        ]
        result = adapter._to_bedrock_format(messages)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
        assert result[0]["content"] == [{"text": "hello"}]
        assert result[1]["content"] == [{"text": "hi there"}]

    def test_to_bedrock_format_filters_system_messages(self):
        """测试过滤系统消息（Bedrock 使用独立的 system 字段）"""
        adapter = BedrockAdapter(
            api_key="test",
            aws_secret_access_key="test"
        )
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "hello"}
        ]
        result = adapter._to_bedrock_format(messages)
        # 系统消息应该被过滤掉
        assert len(result) == 1
        assert result[0]["role"] == "user"

    def test_extract_usage_with_valid_response(self):
        """测试从有效响应提取 usage"""
        adapter = BedrockAdapter(
            api_key="test",
            aws_secret_access_key="test"
        )

        # Mock Bedrock usage 响应
        response = {
            "usage": {
                "inputTokens": 10,
                "outputTokens": 20,
                "totalTokens": 30
            }
        }

        usage = adapter._extract_usage(response, "anthropic.claude-3-sonnet")
        assert usage['prompt_tokens'] == 10
        assert usage['completion_tokens'] == 20
        assert usage['total_tokens'] == 30
        assert usage['model_provider'] == 'bedrock'
        assert usage['model_name'] == 'anthropic.claude-3-sonnet'

    def test_extract_usage_with_missing_fields(self):
        """测试从缺少字段的响应提取 usage"""
        adapter = BedrockAdapter(
            api_key="test",
            aws_secret_access_key="test"
        )

        # 部分缺失的 usage
        response = {
            "usage": {
                "inputTokens": 10
            }
        }

        usage = adapter._extract_usage(response, "anthropic.claude-3-haiku")
        assert usage['prompt_tokens'] == 10
        assert usage['completion_tokens'] == 0
        assert usage['total_tokens'] == 0
        assert usage['model_provider'] == 'bedrock'

    def test_extract_usage_with_invalid_response(self):
        """测试从无效响应提取 usage（返回默认值）"""
        adapter = BedrockAdapter(
            api_key="test",
            aws_secret_access_key="test"
        )

        usage = adapter._extract_usage(None, "anthropic.claude-3-opus")
        assert usage['prompt_tokens'] == 0
        assert usage['completion_tokens'] == 0
        assert usage['total_tokens'] == 0
        assert usage['model_provider'] == 'bedrock'

    def test_extra_config_storage(self):
        """测试额外配置的存储"""
        adapter = BedrockAdapter(
            api_key="AKIAIOSFODNN7EXAMPLE",
            base_url="eu-west-1",
            aws_secret_access_key="secret",
            custom_param="value"
        )
        assert adapter.extra_config['aws_secret_access_key'] == 'secret'
        assert adapter.extra_config['custom_param'] == 'value'
