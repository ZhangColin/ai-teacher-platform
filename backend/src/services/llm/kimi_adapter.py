"""Kimi (Moonshot AI) 专用适配器

Kimi 特殊要求：
1. K2 系列模型要求 temperature=1.0
2. 消息格式严格检查
"""
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple
from openai import AsyncOpenAI

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class KimiAdapter(BaseLLMAdapter):
    """Kimi (Moonshot AI) 专用适配器

    API 文档: https://platform.moonshot.cn/docs/intro
    """

    # K2 系列模型（要求 temperature=1.0）
    K2_MODELS = {
        'kimi-k2.5',
        'kimi-k2.5-thinking',
        'kimi-k2.5-vision',
    }

    def __init__(self, **kwargs):
        """
        初始化 Kimi 适配器

        Args:
            api_key: API 密钥
            base_url: API 基础 URL (默认 https://api.moonshot.cn/v1)
            timeout: 请求超时时间（默认 120 秒）
            max_retries: 最大重试次数（默认 2）
            **kwargs: 额外配置
        """
        super().__init__(**kwargs)
        timeout = kwargs.get('timeout', 120.0)
        max_retries = kwargs.get('max_retries', 2)

        # Kimi 默认 base_url
        if not self.base_url:
            self.base_url = 'https://api.moonshot.cn/v1'

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout,
            max_retries=max_retries
        )

    def _get_temperature(self, model: str, user_temperature: float) -> float:
        """获取适合的温度参数

        K2 系列模型只支持 temperature=1.0
        """
        if model in self.K2_MODELS:
            return 1.0
        return user_temperature

    def _validate_messages(self, messages: List[Dict]) -> List[Dict]:
        """验证和清理消息格式

        Kimi 对消息格式要求严格：
        1. role 必须是 system/user/assistant 之一
        2. content 不能为空
        3. 消息顺序必须正确
        """
        valid_roles = {'system', 'user', 'assistant'}
        validated = []

        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            # 跳过空内容
            if not content or not content.strip():
                continue

            # 确保角色有效
            if role not in valid_roles:
                role = 'user'

            validated.append({'role': role, 'content': content})

        return validated

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
        messages = self._validate_messages(messages)
        temperature = self._get_temperature(model, temperature)

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            **kwargs
        )

        content = response.choices[0].message.content
        usage = self._extract_usage(response, model, 'kimi')
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
        messages = self._validate_messages(messages)
        temperature = self._get_temperature(model, temperature)

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
                    'model_provider': 'kimi',
                    'model_name': model
                }

        if usage_info:
            yield usage_info
        else:
            yield self._extract_usage(None, model, 'kimi')

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
