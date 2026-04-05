"""DeepSeek 专用适配器

API 文档: https://platform.deepseek.com/api-docs/
"""
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple
from openai import AsyncOpenAI

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class DeepSeekAdapter(BaseLLMAdapter):
    """DeepSeek 专用适配器

    支持模型: deepseek-chat, deepseek-reasoner
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        timeout = kwargs.get('timeout', 120.0)
        max_retries = kwargs.get('max_retries', 2)

        if not self.base_url:
            self.base_url = 'https://api.deepseek.com'

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout,
            max_retries=max_retries,
            http_client=self._create_http_client(timeout),
        )

    @property
    def provider_code(self) -> str:
        return 'deepseek'

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Tuple[str, Optional[Dict]]:
        messages = self._build_messages(messages, system_prompt)

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            **kwargs
        )

        content = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason or 'stop'
        usage = self._extract_openai_usage(response, model, finish_reason)
        return content, usage

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str | Dict, None]:
        messages = self._build_messages(messages, system_prompt)

        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
            **kwargs
        )

        usage_info = None
        finish_reason = 'stop'

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

            if chunk.choices and chunk.choices[0].finish_reason:
                finish_reason = chunk.choices[0].finish_reason

            if hasattr(chunk, 'usage') and chunk.usage:
                usage_info = self._build_usage(
                    model,
                    prompt_tokens=chunk.usage.prompt_tokens,
                    completion_tokens=chunk.usage.completion_tokens,
                    finish_reason=finish_reason,
                )

        if usage_info:
            usage_info['finish_reason'] = finish_reason
            yield usage_info
        else:
            yield self._build_usage(model, finish_reason=finish_reason)

    def _extract_openai_usage(self, response, model: str, finish_reason: str = 'stop') -> Dict:
        if response and hasattr(response, 'usage') and response.usage:
            return self._build_usage(
                model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                finish_reason=finish_reason,
            )
        return self._build_usage(model, finish_reason=finish_reason)
