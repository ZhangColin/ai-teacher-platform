"""代码完整性验证器 - 验证代码块是否完整"""
import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool                    # 是否有效
    issues: List[str]              # 问题列表
    needs_continue: bool           # 是否需要续写

    def to_dict(self) -> dict:
        return {
            'valid': self.valid,
            'issues': self.issues,
            'needs_continue': self.needs_continue
        }


class CodeValidator:
    """代码验证器 - 验证代码完整性"""

    def __init__(self):
        pass

    def check_fence_blocks(self, content: str) -> List[str]:
        """检查Markdown代码块是否闭合"""
        issues = []

        # 统计```数量
        fence_count = content.count('```')

        if fence_count % 2 != 0:
            issues.append(f"代码块未闭合：```数量为奇数（{fence_count}个）")

        return issues

    def check_html_completeness(self, content: str) -> List[str]:
        """检查HTML完整性"""
        issues = []

        # 使用栈式检查HTML标签配对
        # 匹配开始标签（如 <div>）
        open_tags = re.findall(r'<(\w+)(?:\s[^>]*)?>', content)
        # 匹配结束标签（如 </div>）
        close_tags = re.findall(r'</(\w+)>', content)

        # 简单的栈式配对检查
        tag_stack = []
        for tag in open_tags:
            # 忽略自闭合标签
            if tag in ['br', 'hr', 'img', 'input', 'meta', 'link']:
                continue
            tag_stack.append(tag)

        for tag in close_tags:
            if tag_stack and tag_stack[-1] == tag:
                tag_stack.pop()
            else:
                issues.append(f"HTML标签不匹配: </{tag}>")

        # 检查未闭合的标签
        if tag_stack:
            issues.append(f"未闭合的HTML标签: {', '.join(tag_stack)}")

        return issues

    def check_brackets_balance(self, content: str) -> List[str]:
        """检查括号配对"""
        issues = []

        # 定义括号对
        bracket_pairs = {
            '(': ')',
            '{': '}',
            '[': ']'
        }

        # 检查每种括号
        for open_bracket, close_bracket in bracket_pairs.items():
            open_count = content.count(open_bracket)
            close_count = content.count(close_bracket)

            if open_count > close_count:
                issues.append(f"未闭合的括号 '{open_bracket}': {open_count - close_count}个")
            elif close_count > open_count:
                issues.append(f"多余的闭合括号 '{close_bracket}': {close_count - open_count}个")

        return issues

    def validate_content(self, content: str) -> ValidationResult:
        """
        验证内容完整性

        Args:
            content: 要验证的内容

        Returns:
            ValidationResult: 验证结果
        """
        issues = []

        # 1. 检查Markdown代码块是否闭合
        fence_issues = self.check_fence_blocks(content)
        if fence_issues:
            issues.extend(fence_issues)

        # 2. 检查HTML完整性
        if '<html' in content.lower() or '<div' in content.lower():
            html_issues = self.check_html_completeness(content)
            if html_issues:
                issues.extend(html_issues)

        # 3. 检查括号配对
        bracket_issues = self.check_brackets_balance(content)
        if bracket_issues:
            issues.extend(bracket_issues)

        valid = len(issues) == 0
        needs_continue = not valid  # 如果无效，需要续写

        result = ValidationResult(
            valid=valid,
            issues=issues,
            needs_continue=needs_continue
        )

        if not valid:
            logger.warning(f"内容验证失败: {issues}")
        else:
            logger.info("内容验证通过")

        return result
