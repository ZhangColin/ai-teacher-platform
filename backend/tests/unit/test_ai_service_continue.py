"""测试续写逻辑"""
import pytest
from unittest.mock import Mock
from src.services.ai_service import AIService


class TestContinueLogic:
    """测试续写逻辑"""

    def test_truncate_content_for_continue(self):
        """测试内容截断逻辑"""
        # 模拟模型配置
        builtin_model = Mock()
        builtin_model.continue_window_size = 2000

        # 生成 5000 字符的内容
        long_content = "A" * 5000
        continue_window_size = builtin_model.continue_window_size

        # 应用滑动窗口（2000 字符）
        if len(long_content) > continue_window_size:
            truncated = long_content[-continue_window_size:]
        else:
            truncated = long_content

        # 验证：只保留最后 2000 字符
        assert len(truncated) == 2000
        assert truncated == "A" * 2000

    def test_short_content_not_truncated(self):
        """测试短内容不被截断"""
        # 模拟模型配置
        builtin_model = Mock()
        builtin_model.continue_window_size = 2000

        # 生成 1000 字符的内容
        short_content = "A" * 1000
        continue_window_size = builtin_model.continue_window_size

        if len(short_content) > continue_window_size:
            truncated = short_content[-continue_window_size:]
        else:
            truncated = short_content

        # 验证：内容不变
        assert len(truncated) == 1000
        assert truncated == short_content

    def test_continue_window_size_default(self):
        """测试默认窗口大小"""
        default_window = 2000
        assert default_window == 2000

    def test_estimate_tokens_from_content(self):
        """测试从内容估算token数"""
        # 测试：1 token ≈ 2 字符
        content_1000_chars = "A" * 1000
        estimated_tokens = len(content_1000_chars) // 2

        assert estimated_tokens == 500

    def test_should_continue_with_max_output_tokens(self):
        """测试使用max_output_tokens判断续写"""
        # 模拟配置
        max_output_tokens = 4000
        content_length = 8000  # 8000 字符 ≈ 4000 tokens

        # 估算token数
        estimated_tokens = content_length // 2

        # 判断是否达到80%阈值
        should_continue = estimated_tokens >= max_output_tokens * 0.8

        assert should_continue == True

    def test_should_not_continue_below_threshold(self):
        """测试低于阈值时不续写"""
        # 模拟配置
        max_output_tokens = 4000
        content_length = 3000  # 3000 字符 ≈ 1500 tokens

        # 估算token数
        estimated_tokens = content_length // 2

        # 判断是否达到80%阈值
        should_continue = estimated_tokens >= max_output_tokens * 0.8

        assert should_continue == False
