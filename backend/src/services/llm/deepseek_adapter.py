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

    支持模型:
    - deepseek-chat: DeepSeek-V3.2 通用模型
    - deepseek-reasoner: DeepSeek-V3.2 推理模型
    """

    def __init__(self, **kwargs):
        """
        初始化 DeepSeek 适配器

        Args:
            api_key: API 密钥
            base_url: API 基础 URL (默认 https://api.deepseek.com)
            timeout: 请求超时时间（默认 120 秒）
            max_retries: 最大重试次数（默认 2）
            **kwargs: 额外配置
        """
        super().__init__(**kwargs)
        timeout = kwargs.get('timeout', 120.0)
        max_retries = kwargs.get('max_retries', 2)

        # DeepSeek 默认 base_url
        if not self.base_url:
            self.base_url = 'https://api.deepseek.com'

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout,
            max_retries=max_retries
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Tuple[str, Optional[Dict]]:
        """非流式对话"""
        messages = self._build_messages(messages, system_prompt)

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            **kwargs
        )

        content = response.choices[0].message.content
        usage = self._extract_usage(response, model, 'deepseek')
        return content, usage

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str | Dict, None]:
        """流式对话"""
        messages = self._build_messages(messages, system_prompt)

        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
            **kwargs
        )

        usage_info = None

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

            if hasattr(chunk, 'usage') and chunk.usage:
                usage_info = {
                    'prompt_tokens': chunk.usage.prompt_tokens,
                    'completion_tokens': chunk.usage.completion_tokens,
                    'total_tokens': chunk.usage.total_tokens,
                    'model_provider': 'deepseek',
                    'model_name': model
                }

        if usage_info:
            yield usage_info
        else:
            yield self._extract_usage(None, model, 'deepseek')

    def _extract_usage(self, response, model: str, provider: str) -> Dict:
        """提取 token 使用信息"""
        if response and hasattr(response, 'usage') and response.usage:
            return {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
                'model_provider': provider,
                'model_name': model
            }
        return super()._extract_usage(response, model, provider)
