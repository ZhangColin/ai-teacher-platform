"""内容完整性验证器

检测 LLM 生成的 HTML / 代码内容是否完整，用于判断是否需要续写。
"""
import re
import logging
from html.parser import HTMLParser
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """验证结果"""
    is_complete: bool
    missing_tags: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    html_end_pos: int = -1


class _TagTracker(HTMLParser):
    """基于 HTMLParser 的标签跟踪器，比简单计数更准确"""

    SELF_CLOSING = frozenset({
        'br', 'hr', 'img', 'input', 'meta', 'link', 'area',
        'base', 'col', 'embed', 'source', 'track', 'wbr',
    })

    def __init__(self):
        super().__init__()
        self.tag_stack: List[str] = []
        self.errors: List[str] = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower not in self.SELF_CLOSING:
            self.tag_stack.append(tag_lower)

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.SELF_CLOSING:
            return
        if self.tag_stack and self.tag_stack[-1] == tag_lower:
            self.tag_stack.pop()
        elif tag_lower in self.tag_stack:
            idx = len(self.tag_stack) - 1 - self.tag_stack[::-1].index(tag_lower)
            unclosed = self.tag_stack[idx + 1:]
            if unclosed:
                self.errors.append(f"闭合 </{tag_lower}> 前有未闭合标签: {unclosed}")
            self.tag_stack = self.tag_stack[:idx]


class ContentValidator:
    """内容完整性验证器"""

    @staticmethod
    def check_html(content: str) -> ValidationResult:
        """检查 HTML 内容的完整性

        使用 HTMLParser 进行结构化分析，比简单标签计数更可靠。
        """
        content_lower = content.lower()
        is_html = '<html' in content_lower or '<!doctype' in content_lower

        if not is_html:
            return ValidationResult(is_complete=True)

        issues = []
        missing_tags = []

        tracker = _TagTracker()
        try:
            tracker.feed(content)
        except Exception as e:
            issues.append(f"HTML 解析异常: {e}")

        issues.extend(tracker.errors)

        if tracker.tag_stack:
            for tag in reversed(tracker.tag_stack):
                missing_tags.append(f'</{tag}>')
            issues.append(f"未闭合标签栈: {tracker.tag_stack}")

        html_end_pos = ContentValidator._find_html_end(content)

        if html_end_pos > 0:
            after_html = content[html_end_pos:].strip()
            if len(after_html) < 50 or not any(c.isalnum() for c in after_html):
                return ValidationResult(
                    is_complete=True,
                    missing_tags=[],
                    issues=[],
                    html_end_pos=html_end_pos,
                )

        is_complete = len(missing_tags) == 0 and html_end_pos > 0

        return ValidationResult(
            is_complete=is_complete,
            missing_tags=missing_tags,
            issues=issues,
            html_end_pos=html_end_pos,
        )

    @staticmethod
    def check_brackets(content: str) -> ValidationResult:
        """检查代码括号匹配（大括号、圆括号、方括号）

        使用栈而非简单计数，能正确处理字符串内的括号。
        """
        issues = []
        stack = []
        in_string = None
        escape_next = False
        in_line_comment = False
        in_block_comment = False

        for i, ch in enumerate(content):
            if escape_next:
                escape_next = False
                continue

            if ch == '\\' and in_string:
                escape_next = True
                continue

            if in_line_comment:
                if ch == '\n':
                    in_line_comment = False
                continue

            if in_block_comment:
                if ch == '*' and i + 1 < len(content) and content[i + 1] == '/':
                    in_block_comment = False
                continue

            if not in_string:
                if ch == '/' and i + 1 < len(content):
                    if content[i + 1] == '/':
                        in_line_comment = True
                        continue
                    if content[i + 1] == '*':
                        in_block_comment = True
                        continue

            if ch in ('"', "'", '`'):
                if in_string == ch:
                    in_string = None
                elif not in_string:
                    in_string = ch
                continue

            if in_string:
                continue

            match_map = {'{': '}', '(': ')', '[': ']'}
            close_map = {'}': '{', ')': '(', ']': '['}

            if ch in match_map:
                stack.append(ch)
            elif ch in close_map:
                expected = close_map[ch]
                if stack and stack[-1] == expected:
                    stack.pop()
                else:
                    issues.append(f"括号不匹配: 位置 {i} 处的 '{ch}' 没有对应的开括号")

        if stack:
            close_for = {'{': '}', '(': ')', '[': ']'}
            missing = close_for.get(stack[-1], '?') if stack else ''
            issues.append(f"未闭合括号: {len(stack)} 个 (最后: '{stack[-1]}')")

        return ValidationResult(
            is_complete=len(stack) == 0 and len(issues) == 0,
            issues=issues,
        )

    @staticmethod
    def is_complete(content: str) -> bool:
        """综合判断内容是否完整"""
        content_lower = content.lower()
        is_html = '<html' in content_lower or '<!doctype' in content_lower

        if is_html:
            result = ContentValidator.check_html(content)
            return result.is_complete

        has_code = '<script' in content_lower or '```' in content
        if has_code:
            bracket_result = ContentValidator.check_brackets(content)
            return bracket_result.is_complete

        return True

    @staticmethod
    def clean_after_html_end(content: str) -> str:
        """如果内容在 </html> 之后还有多余内容，截断到 </html>"""
        pos = ContentValidator._find_html_end(content)
        if pos > 0:
            after = content[pos:].strip()
            if after:
                logger.info(f"截断 </html> 之后的 {len(after)} 字符多余内容")
                return content[:pos].rstrip()
        return content

    @staticmethod
    def repair_html(content: str) -> str:
        """尝试修复不完整的 HTML（补全缺失的闭合标签）"""
        result = ContentValidator.check_html(content)
        if result.is_complete:
            return content

        repaired = content.rstrip()
        for tag in result.missing_tags:
            repaired += f"\n{tag}"

        return repaired

    @staticmethod
    def _find_html_end(content: str) -> int:
        """找到最后一个 </html> 标签的结束位置，返回 -1 表示未找到"""
        pattern = re.compile(r'</html>', re.IGNORECASE)
        matches = list(pattern.finditer(content))
        if matches:
            return matches[-1].end()
        return -1
