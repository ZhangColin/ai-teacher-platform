"""测试豆包适配器"""
import pytest

from src.services.llm.doubao_adapter import DoubaoAdapter


class TestDoubaoAdapter:
    """测试豆包适配器"""

    def test_init_with_api_key_only(self):
        """测试只使用 api_key 初始化"""
        adapter = DoubaoAdapter(api_key="test-key")
        assert adapter.api_key == "test-key"
        assert adapter.base_url == DoubaoAdapter.DEFAULT_BASE_URL
        assert adapter.client is not None

    def test_init_with_custom_base_url(self):
        """测试使用自定义 base_url 初始化"""
        adapter = DoubaoAdapter(
            api_key="test-key",
            base_url="https://custom.endpoint.com/api/v3"
        )
        assert adapter.api_key == "test-key"
        assert adapter.base_url == "https://custom.endpoint.com/api/v3"

    def test_init_with_custom_timeout(self):
        """测试自定义超时参数"""
        adapter = DoubaoAdapter(
            api_key="test-key",
            timeout=60.0
        )
        assert adapter.api_key == "test-key"
        # 验证客户端配置正确传递

    def test_build_request_body_basic(self):
        """测试基本请求体构建"""
        adapter = DoubaoAdapter(api_key="test-key")
        messages = [{"role": "user", "content": "hello"}]

        req = adapter._build_request_body(
            model="doubao-pro-4k",
            messages=messages,
            system_prompt=None,
            temperature=0.7,
            extra_kwargs={},
            stream=False
        )

        assert req["model"] == "doubao-pro-4k"
        assert req["temperature"] == 0.7
        assert req["stream"] is False
        assert len(req["messages"]) == 1
        assert req["messages"][0]["role"] == "user"
        assert req["messages"][0]["content"] == "hello"

    def test_build_request_body_with_system_prompt(self):
        """测试带系统提示词的请求体构建"""
        adapter = DoubaoAdapter(api_key="test-key")
        messages = [{"role": "user", "content": "hello"}]

        req = adapter._build_request_body(
            model="doubao-pro-4k",
            messages=messages,
            system_prompt="You are helpful",
            temperature=0.7,
            extra_kwargs={},
            stream=False
        )

        assert len(req["messages"]) == 2
        assert req["messages"][0]["role"] == "system"
        assert req["messages"][0]["content"] == "You are helpful"
        assert req["messages"][1]["role"] == "user"

    def test_build_request_body_with_multiple_messages(self):
        """测试多条消息的请求体构建"""
        adapter = DoubaoAdapter(api_key="test-key")
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
            {"role": "user", "content": "how are you?"}
        ]

        req = adapter._build_request_body(
            model="doubao-pro-4k",
            messages=messages,
            system_prompt=None,
            temperature=0.7,
            extra_kwargs={},
            stream=False
        )

        assert len(req["messages"]) == 3
        assert req["messages"][0]["role"] == "user"
        assert req["messages"][1]["role"] == "assistant"
        assert req["messages"][2]["role"] == "user"

    def test_build_request_body_with_max_tokens(self):
        """测试带 max_tokens 的请求体构建"""
        adapter = DoubaoAdapter(api_key="test-key")
        messages = [{"role": "user", "content": "hello"}]

        req = adapter._build_request_body(
            model="doubao-pro-4k",
            messages=messages,
            system_prompt=None,
            temperature=0.7,
            extra_kwargs={"max_tokens": 2048},
            stream=False
        )

        assert req["max_tokens"] == 2048

    def test_build_request_body_with_top_p(self):
        """测试带 top_p 的请求体构建"""
        adapter = DoubaoAdapter(api_key="test-key")
        messages = [{"role": "user", "content": "hello"}]

        req = adapter._build_request_body(
            model="doubao-pro-4k",
            messages=messages,
            system_prompt=None,
            temperature=0.7,
            extra_kwargs={"top_p": 0.9},
            stream=False
        )

        assert req["top_p"] == 0.9

    def test_build_request_body_stream_mode(self):
        """测试流式模式请求体构建"""
        adapter = DoubaoAdapter(api_key="test-key")
        messages = [{"role": "user", "content": "hello"}]

        req = adapter._build_request_body(
            model="doubao-pro-4k",
            messages=messages,
            system_prompt=None,
            temperature=0.7,
            extra_kwargs={},
            stream=True
        )

        assert req["stream"] is True

    def test_extract_usage_with_valid_response(self):
        """测试从有效响应提取 usage"""
        adapter = DoubaoAdapter(api_key="test-key")

        response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }

        usage = adapter._extract_usage(response, "doubao-pro-4k")
        assert usage['prompt_tokens'] == 10
        assert usage['completion_tokens'] == 20
        assert usage['total_tokens'] == 30
        assert usage['model_provider'] == 'doubao'
        assert usage['model_name'] == 'doubao-pro-4k'

    def test_extract_usage_with_none_response(self):
        """测试从 None 响应提取 usage（返回默认值）"""
        adapter = DoubaoAdapter(api_key="test-key")

        usage = adapter._extract_usage(None, "doubao-pro-4k")
        assert usage['prompt_tokens'] == 0
        assert usage['completion_tokens'] == 0
        assert usage['total_tokens'] == 0
        assert usage['model_provider'] == 'doubao'
        assert usage['model_name'] == 'doubao-pro-4k'

    def test_extract_usage_with_partial_usage(self):
        """测试从部分 usage 响应提取 usage"""
        adapter = DoubaoAdapter(api_key="test-key")

        response = {
            "usage": {
                "prompt_tokens": 10,
                # 缺少 completion_tokens 和 total_tokens
            }
        }

        usage = adapter._extract_usage(response, "doubao-pro-4k")
        assert usage['prompt_tokens'] == 10
        assert usage['completion_tokens'] == 0
        assert usage['total_tokens'] == 0

    def test_default_base_url(self):
        """测试默认 base_url"""
        assert DoubaoAdapter.DEFAULT_BASE_URL == "https://ark.cn-beijing.volces.com/api/v3"

    def test_extra_config_storage(self):
        """测试额外配置的存储"""
        adapter = DoubaoAdapter(
            api_key="test-key",
            custom_param="value"
        )
        assert adapter.extra_config['custom_param'] == 'value'
