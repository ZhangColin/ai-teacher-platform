"""NewAPI 适配器

NewAPI 是一个 OpenAI API 代理/聚合服务。
由于 httpx 与 NewAPI 存在兼容性问题，此适配器使用 aiohttp 进行 HTTP 请求。
"""
import json
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple

import aiohttp

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class NewAPIAdapter(BaseLLMAdapter):
    """NewAPI 供应商适配器

    使用 aiohttp 替代 httpx/openai SDK，因为 NewAPI 与 httpx 存在兼容性问题。
    API 格式兼容 OpenAI。
    """

    # 某些模型有特殊的参数限制
    MODEL_SPECIFIC_CONFIG = {
        'kimi-k2.5': {'temperature': 1},
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timeout = kwargs.get('timeout', 120.0)
        # 流式响应无总时限，只限单次读阻塞，避免对长响应误判超时
        self._stream_timeout = aiohttp.ClientTimeout(
            total=None,
            sock_connect=15,
            sock_read=self.timeout,
        )
        self._normal_timeout = aiohttp.ClientTimeout(total=self.timeout)

    @property
    def provider_code(self) -> str:
        return 'newapi'

    def _get_temperature(self, model: str, user_temperature: float) -> float:
        config = self.MODEL_SPECIFIC_CONFIG.get(model, {})
        return config.get('temperature', user_temperature)

    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Tuple[str, Optional[Dict]]:
        messages = self._build_messages(messages, system_prompt)
        temperature = self._get_temperature(model, temperature)

        payload = {
            'model': model,
            'messages': messages,
            'stream': False,
            'temperature': temperature
        }

        url = f'{self.base_url}/chat/completions'
        headers = self._get_headers()

        logger.info(f"[NewAPI] 非流式调用: model={model}")

        async with aiohttp.ClientSession(
            timeout=self._normal_timeout
        ) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"[NewAPI] API 错误: {response.status} - {error_text}")
                    raise Exception(f"NewAPI 调用失败: HTTP {response.status} - {error_text}")

                response_data = await response.json()

                content = response_data['choices'][0]['message']['content']
                finish_reason = response_data['choices'][0].get('finish_reason', 'stop')

                api_usage = response_data.get('usage', {})
                usage = self._build_usage(
                    model,
                    prompt_tokens=api_usage.get('prompt_tokens', 0),
                    completion_tokens=api_usage.get('completion_tokens', 0),
                    finish_reason=finish_reason,
                )

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
        temperature = self._get_temperature(model, temperature)

        payload = {
            'model': model,
            'messages': messages,
            'stream': True,
            'temperature': temperature
        }

        url = f'{self.base_url}/chat/completions'
        headers = self._get_headers()

        logger.info(f"[NewAPI] 流式调用: model={model}")

        async with aiohttp.ClientSession(
            timeout=self._stream_timeout
        ) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"[NewAPI] 流式 API 错误: {response.status} - {error_text}")
                    raise Exception(f"NewAPI 流式调用失败: HTTP {response.status}")

                usage_info = None
                finish_reason = 'stop'

                while True:
                    line = await response.content.readline()
                    if not line:
                        break
                    line_text = line.decode('utf-8').strip()
                    if not line_text:
                        continue

                    if line_text.startswith('data: '):
                        line_text = line_text[6:]
                    elif line_text.startswith('data:'):
                        line_text = line_text[5:]

                    if line_text == '[DONE]':
                        break

                    try:
                        chunk_data = json.loads(line_text)

                        if 'usage' in chunk_data and chunk_data['usage']:
                            api_usage = chunk_data['usage']
                            usage_info = self._build_usage(
                                model,
                                prompt_tokens=api_usage.get('prompt_tokens', 0),
                                completion_tokens=api_usage.get('completion_tokens', 0),
                                finish_reason=finish_reason,
                            )

                        if 'choices' in chunk_data and chunk_data['choices']:
                            delta = chunk_data['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield content

                            chunk_finish = chunk_data['choices'][0].get('finish_reason')
                            if chunk_finish:
                                finish_reason = chunk_finish

                    except json.JSONDecodeError as e:
                        logger.warning(f"[NewAPI] JSON 解析失败: {e}")

                if usage_info:
                    usage_info['finish_reason'] = finish_reason
                    yield usage_info
                else:
                    yield self._build_usage(model, finish_reason=finish_reason)
