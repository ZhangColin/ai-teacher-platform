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
        'kimi-k2-0905-preview',
        'kimi-k2-turbo-preview',
        'kimi-k2-thinking',
        'kimi-k2-thinking-turbo',
    }

    def __init__(self, **kwargs):
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
            max_retries=max_retries,
            http_client=self._create_http_client(timeout),
        )

    @property
    def provider_code(self) -> str:
        return 'kimi'

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
