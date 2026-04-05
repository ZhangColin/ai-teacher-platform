"""自动续写管理器

当 LLM 输出因 token 上限被截断（finish_reason='length'）时，
自动发起续写请求并智能拼接，对外表现为连续的输出流。
"""
import re
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple

from .llm.base_adapter import BaseLLMAdapter
from .content_validator import ContentValidator

logger = logging.getLogger(__name__)

# 续写提示词（英文，模型遵从性更好）
CONTINUE_PROMPT = """The previous response was cut off due to length limits. Continue EXACTLY from where it stopped.
Rules:
1. Output ONLY the continuation content, no explanations or comments about continuing
2. Do NOT repeat any content already generated
3. Do NOT wrap output in markdown code fences (```)
4. The last 100 characters were:
---
{tail}
---
5. Continue from that exact point."""

# 短内容不需要续写的阈值
MIN_CONTENT_LENGTH_FOR_CONTINUATION = 500

# 判断是否包含代码/HTML 的特征
CODE_INDICATORS = ('```', '<html', '<!doctype', '<div', '<script', '<style')


class ContinuationManager:
    """自动续写管理器"""

    def __init__(self, max_continue: int = 3):
        self.max_continue = max_continue

    async def chat_with_continuation(
        self,
        adapter: BaseLLMAdapter,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Tuple[str, Optional[Dict]]:
        """非流式调用，自动续写直到内容完整

        Returns:
            (完整内容, 累加后的 usage 信息)
        """
        content, usage = await adapter.chat(
            messages, model, system_prompt, temperature, **kwargs
        )

        finish_reason = usage.get('finish_reason', 'stop') if usage else 'stop'
        total_usage = dict(usage) if usage else {}

        continue_count = 0
        while (
            finish_reason == 'length'
            and continue_count < self.max_continue
            and self._should_continue(content)
        ):
            continue_count += 1
            logger.info(
                f"续写第 {continue_count} 次，当前内容长度: {len(content)}"
            )

            if ContentValidator.is_complete(content):
                logger.info("内容完整性检查通过，停止续写")
                break

            continue_messages = messages + [
                {"role": "assistant", "content": content},
                {"role": "user", "content": self._build_continue_prompt(content)},
            ]

            try:
                continuation, cont_usage = await adapter.chat(
                    continue_messages, model, system_prompt, temperature, **kwargs
                )
            except Exception as e:
                logger.warning(f"续写第 {continue_count} 次失败: {e}，返回已生成内容")
                break

            cleaned = self._clean_continuation(continuation)
            overlap = self._find_overlap(content, cleaned)
            new_content = cleaned[overlap:]

            if not new_content.strip():
                logger.info("续写返回空内容，停止")
                break

            content += new_content
            finish_reason = cont_usage.get('finish_reason', 'stop') if cont_usage else 'stop'
            total_usage = self._merge_usage(total_usage, cont_usage or {})

        is_html = '<html' in content.lower() or '<!doctype' in content.lower()
        if is_html:
            content = ContentValidator.clean_after_html_end(content)

        if continue_count > 0:
            total_usage['continuation_count'] = continue_count
            logger.info(
                f"续写完成，共 {continue_count} 次，最终长度: {len(content)}"
            )

        return content, total_usage

    async def chat_stream_with_continuation(
        self,
        adapter: BaseLLMAdapter,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str | Dict, None]:
        """流式调用，自动续写直到内容完整

        Yields:
            str: 内容片段
            Dict: 最终的累加 usage 信息
        """
        accumulated = ""
        finish_reason = 'stop'
        total_usage = {}

        async for chunk in adapter.chat_stream(
            messages, model, system_prompt, temperature, **kwargs
        ):
            if isinstance(chunk, dict):
                finish_reason = chunk.get('finish_reason', 'stop')
                total_usage = self._merge_usage(total_usage, chunk)
            else:
                accumulated += chunk
                yield chunk

        continue_count = 0
        while (
            finish_reason == 'length'
            and continue_count < self.max_continue
            and self._should_continue(accumulated)
        ):
            if ContentValidator.is_complete(accumulated):
                logger.info("内容完整性检查通过，停止续写")
                break

            continue_count += 1
            logger.info(
                f"流式续写第 {continue_count} 次，当前长度: {len(accumulated)}"
            )

            continue_messages = messages + [
                {"role": "assistant", "content": accumulated},
                {"role": "user", "content": self._build_continue_prompt(accumulated)},
            ]

            try:
                continuation = ""
                cont_finish_reason = 'stop'

                async for chunk in adapter.chat_stream(
                    continue_messages, model, system_prompt, temperature, **kwargs
                ):
                    if isinstance(chunk, dict):
                        cont_finish_reason = chunk.get('finish_reason', 'stop')
                        total_usage = self._merge_usage(total_usage, chunk)
                    else:
                        continuation += chunk

            except Exception as e:
                logger.warning(
                    f"流式续写第 {continue_count} 次失败: {e}，返回已有内容"
                )
                break

            cleaned = self._clean_continuation(continuation)
            overlap = self._find_overlap(accumulated, cleaned)
            new_content = cleaned[overlap:]

            if not new_content.strip():
                logger.info("流式续写返回空内容，停止")
                break

            accumulated += new_content
            yield new_content

            finish_reason = cont_finish_reason

        if continue_count > 0:
            total_usage['continuation_count'] = continue_count
            logger.info(
                f"流式续写完成，共 {continue_count} 次，最终长度: {len(accumulated)}"
            )

        if total_usage:
            yield total_usage

    def _should_continue(self, content: str) -> bool:
        """判断是否应该触发续写

        条件：内容足够长 且 包含代码/HTML 特征 且 不以问号结尾
        """
        if len(content) < MIN_CONTENT_LENGTH_FOR_CONTINUATION:
            return False

        content_lower = content.lower()
        has_code = any(indicator in content_lower for indicator in CODE_INDICATORS)
        if not has_code:
            return False

        stripped = content.rstrip()
        if stripped.endswith(('?', '?')):
            return False

        return True

    def _build_continue_prompt(self, content: str) -> str:
        """构造续写提示词"""
        tail = content[-100:] if len(content) > 100 else content
        return CONTINUE_PROMPT.format(tail=tail)

    def _clean_continuation(self, text: str) -> str:
        """清理续写内容

        处理：
        1. 开头的 markdown 代码块标记
        2. 开头的对话性文本
        3. 结尾的 markdown 闭合标记
        """
        result = text.strip()
        if not result:
            return result

        fence_match = re.match(r'^```\w*\s*\n', result)
        if fence_match:
            result = result[fence_match.end():]
            logger.info("清理续写内容开头的代码块标记")

        skip_patterns = [
            r'^(?:Sure|Certainly|Of course|Here)[,.].*?\n',
            r'^(?:当然|好的|以下是|这里是|继续)[,，。].*?\n',
        ]
        for pattern in skip_patterns:
            match = re.match(pattern, result, re.IGNORECASE)
            if match:
                result = result[match.end():]
                logger.info(f"清理续写内容开头的对话文本: {match.group()[:50]}")
                break

        result = re.sub(r'\n```\s*$', '', result)

        return result.strip()

    def _find_overlap(self, original: str, continuation: str) -> int:
        """找到续写内容中与原内容重叠的部分，返回应跳过的字符数

        使用"锚点匹配"：取原内容尾部子串，在续写内容开头搜索匹配。
        """
        if not continuation or len(continuation) < 30:
            return 0

        tail = original[-200:] if len(original) > 200 else original

        for length in range(min(len(tail), 200), 20, -1):
            anchor = tail[-length:]
            pos = continuation[:500].find(anchor)
            if pos != -1:
                skip = pos + length
                logger.info(f"检测到重叠: 锚点长度={length}, 跳过={skip} 字符")
                return skip

        cont_start = continuation[:200].strip()
        if cont_start and cont_start in original:
            pos = original.rfind(cont_start)
            if pos >= 0:
                logger.info(f"检测到续写内容在原内容中完全出现，跳过 {len(cont_start)} 字符")
                return len(cont_start)

        return 0

    @staticmethod
    def _merge_usage(total: Dict, new: Dict) -> Dict:
        """累加多次 API 调用的 usage 信息"""
        if not new:
            return total
        if not total:
            return dict(new)

        merged = dict(total)
        merged['prompt_tokens'] = total.get('prompt_tokens', 0) + new.get('prompt_tokens', 0)
        merged['completion_tokens'] = total.get('completion_tokens', 0) + new.get('completion_tokens', 0)
        merged['total_tokens'] = total.get('total_tokens', 0) + new.get('total_tokens', 0)
        merged['model_provider'] = new.get('model_provider', total.get('model_provider'))
        merged['model_name'] = new.get('model_name', total.get('model_name'))
        merged['finish_reason'] = new.get('finish_reason', total.get('finish_reason', 'stop'))
        merged['type'] = 'usage'
        return merged
