# -*- coding: utf-8 -*-
"""
HtmlFixerService单元测试
"""
import pytest
from src.infrastructure.html_fixer import HtmlFixerService, BS4_AVAILABLE


class TestHtmlFixerService:
    """HtmlFixerService测试类"""

    def test_fix_broken_tags_closes_unclosed_div(self):
        """测试修复未闭合的div标签"""
        broken = "<div><p>Hello</p>"
        fixed = HtmlFixerService.fix_broken_tags(broken)

        if BS4_AVAILABLE:
            assert "</div>" in fixed
            assert "<p>Hello</p>" in fixed

    def test_fix_broken_tags_handles_empty_string(self):
        """测试处理空字符串"""
        fixed = HtmlFixerService.fix_broken_tags("")
        assert fixed == ""

    def test_fix_broken_tags_handles_none(self):
        """测试处理None"""
        fixed = HtmlFixerService.fix_broken_tags(None)
        assert fixed == ""

    def test_extract_text_gets_text_content(self):
        """测试提取文本内容"""
        html = "<div><p>Hello <b>World</b></p></div>"
        text = HtmlFixerService.extract_text(html)

        if BS4_AVAILABLE:
            assert "Hello World" in text
        else:
            # 简单模式也应该工作
            assert "Hello" in text or "World" in text

    def test_fix_encoding_replaces_mojibake(self):
        """测试修复编码问题"""
        broken = "Helloâ€™s World"  # 乱码的撇号
        fixed = HtmlFixerService.fix_encoding(broken)

        assert "'" in fixed or "'s" in fixed
        assert "â€™" not in fixed

    def test_close_open_tags_fixes_self_closing_tags(self):
        """测试修复自闭合标签"""
        html = "<img src='test.jpg'>"
        fixed = HtmlFixerService.close_open_tags(html)

        # 正则替换应该工作
        assert "<img src='test.jpg' />" in fixed or "<img src=\"test.jpg\" />" in fixed

    def test_sanitize_scripts_removes_script_tags(self):
        """测试移除script标签"""
        html = "<div>Hello<script>alert('xss')</script></div>"
        cleaned = HtmlFixerService.sanitize_scripts(html)

        if BS4_AVAILABLE:
            assert "<script>" not in cleaned
            assert "Hello" in cleaned

    def test_sanitize_scripts_handles_empty_string(self):
        """测试处理空字符串"""
        cleaned = HtmlFixerService.sanitize_scripts("")
        assert cleaned == ""

    def test_wrap_html_wraps_with_div(self):
        """测试用div包装HTML"""
        html = "<p>Hello</p>"
        wrapped = HtmlFixerService.wrap_html(html, tag="div", class_="container")

        if BS4_AVAILABLE:
            assert wrapped.startswith("<div")
            assert 'class="container"' in wrapped
            assert "<p>Hello</p>" in wrapped
            assert "</div>" in wrapped
        else:
            # 简单模式
            assert "<div>" in wrapped
            assert "<p>Hello</p>" in wrapped

    def test_format_html_prettifies_output(self):
        """测试格式化HTML"""
        html = "<div><p>Hello</p></div>"
        formatted = HtmlFixerService.format_html(html)

        if BS4_AVAILABLE:
            # 格式化后应该有换行和缩进
            assert "\n" in formatted or formatted != html

    def test_fix_encoding_handles_empty_string(self):
        """测试编码修复处理空字符串"""
        fixed = HtmlFixerService.fix_encoding("")
        assert fixed == ""

    def test_extract_text_from_empty_html(self):
        """测试从空HTML提取文本"""
        text = HtmlFixerService.extract_text("")
        assert text == ""
