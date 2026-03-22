"""OpenAI 兼容 API 适配器

支持: OpenAI, DeepSeek, Kimi, GLM
"""
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple
from openai import AsyncOpenAI

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI 兼容 API 适配器

    支持所有兼容 OpenAI API 格式的供应商：
    - OpenAI (https://api.openai.com/v1)
    - DeepSeek (https://api.deepseek.com)
    - Kimi (https://api.moonshot.cn/v1)
    - GLM (https://open.bigmodel.cn/api/paas/v4)
    """

    def __init__(self, **kwargs):
        """
        初始化 OpenAI 适配器

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            timeout: 请求超时时间（默认 120 秒）
            max_retries: 最大重试次数（默认 2）
            **kwargs: 额外配置，可包含 provider 字段标识供应商
        """
        super().__init__(**kwargs)
        timeout = kwargs.get('timeout', 120.0)
        max_retries = kwargs.get('max_retries', 2)

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
        """非流式对话

        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            model: 模型名称
            system_prompt: 系统提示词
            temperature: 温度参数
            **kwargs: 额外参数（如 max_tokens, top_p 等）

        Returns:
            (response_content, usage_info)
        """
        messages = self._build_messages(messages, system_prompt)

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            **kwargs
        )

        content = response.choices[0].message.content
        provider = self.extra_config.get('provider', 'openai')
        usage = self._extract_usage(response, model, provider)
        return content, usage

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str | Dict, None]:
        """流式对话

        Args:
            messages: 消息列表
            model: 模型名称
            system_prompt: 系统提示词
            temperature: 温度参数
            **kwargs: 额外参数

        Yields:
            内容片段 (str)
            最后一次 yield usage_info (Dict)
        """
        messages = self._build_messages(messages, system_prompt)

        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
            **kwargs
        )

        provider = self.extra_config.get('provider', 'openai')
        usage_info = None

        async for chunk in stream:
            # 流式输出内容
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

            # OpenAI 会在最后一个 chunk 中包含 usage 信息
            if hasattr(chunk, 'usage') and chunk.usage:
                usage_info = {
                    'prompt_tokens': chunk.usage.prompt_tokens,
                    'completion_tokens': chunk.usage.completion_tokens,
                    'total_tokens': chunk.usage.total_tokens,
                    'model_provider': provider,
                    'model_name': model
                }

        # 确保发送 usage_info
        if usage_info:
            yield usage_info
        else:
            # 如果没有获取到 usage，返回默认值
            yield self._extract_usage(None, model, provider)

    def _extract_usage(self, response, model: str, provider: str) -> Dict:
        """提取 token 使用信息

        Args:
            response: OpenAI 响应对象
            model: 模型名称
            provider: 供应商名称

        Returns:
            usage_info 字典
        """
        if response and hasattr(response, 'usage') and response.usage:
            return {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
                'model_provider': provider,
                'model_name': model
            }
        return super()._extract_usage(response, model, provider)
