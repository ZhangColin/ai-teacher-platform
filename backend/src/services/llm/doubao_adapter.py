"""豆包 VolcEngine 适配器

配置要求:
- api_key: VolcEngine API Key
- base_url: Endpoint URL (可选，默认为 https://ark.cn-beijing.volces.com/api/v3)

豆包 API 使用 OpenAI 兼容格式，可以直接使用 httpx 调用。
"""
import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple

import httpx

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class DoubaoAdapter(BaseLLMAdapter):
    """豆包 VolcEngine 适配器

    豆包 API 使用 OpenAI 兼容格式，支持流式和非流式调用。
    API 文档: https://www.volcengine.com/docs/82379
    """

    DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 如果没有提供 base_url，使用默认的豆包端点
        if not self.base_url:
            self.base_url = self.DEFAULT_BASE_URL

        # 创建 httpx 客户端
        timeout = kwargs.get('timeout', 120.0)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
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
            model: 模型名称（如 "ep-20241115153230-wjggg" 或 "doubao-pro-4k"）
            system_prompt: 系统提示词
            temperature: 温度参数
            **kwargs: 额外参数（如 max_tokens, top_p 等）

        Returns:
            (response_content, usage_info)
        """
        # 构建请求体
        request_body = self._build_request_body(
            model, messages, system_prompt, temperature, kwargs, stream=False
        )

        try:
            response = await self.client.post(
                "/chat/completions",
                json=request_body,
            )
            response.raise_for_status()

            data = response.json()

            # 提取内容
            content = data["choices"][0]["message"]["content"]

            # 提取 usage
            usage = self._extract_usage(data, model)

            return content, usage

        except httpx.HTTPStatusError as e:
            logger.error(f"豆包 API 调用失败: {e.response.status_code} - {e.response.text}")
            raise
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"豆包 API 响应解析失败: {e}")
            raise
        except Exception as e:
            logger.error(f"豆包 API 调用失败: {e}")
            raise

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
        # 构建请求体
        request_body = self._build_request_body(
            model, messages, system_prompt, temperature, kwargs, stream=True
        )

        try:
            async with self.client.stream(
                "POST",
                "/chat/completions",
                json=request_body,
            ) as response:
                response.raise_for_status()

                usage_info = None

                # 解析 SSE 流
                async for line in response.aiter_lines():
                    if not line or not line.strip():
                        continue

                    # SSE 格式: "data: {...}"
                    if line.startswith("data: "):
                        data_str = line[6:]  # 移除 "data: " 前缀

                        # 检查是否为结束标记
                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)

                            # 提取内容
                            if data.get("choices") and data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content

                            # 提取 usage（通常在最后一个 chunk 中）
                            if "usage" in data:
                                usage_info = self._extract_usage(data, model)

                        except json.JSONDecodeError:
                            logger.warning(f"无法解析豆包流式响应: {data_str}")
                            continue

                # 确保发送 usage_info
                if usage_info:
                    yield usage_info
                else:
                    yield self._extract_usage(None, model)

        except httpx.HTTPStatusError as e:
            logger.error(f"豆包流式 API 调用失败: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"豆包流式 API 调用失败: {e}")
            raise

    def _build_request_body(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        temperature: float,
        extra_kwargs: Dict,
        stream: bool
    ) -> Dict:
        """构建豆包 API 请求体

        豆包 API 使用 OpenAI 兼容格式。
        """
        # 构建消息列表
        request_messages = []

        # 添加系统提示词
        if system_prompt:
            request_messages.append({
                "role": "system",
                "content": system_prompt
            })

        # 添加对话消息
        for msg in messages:
            # 豆包支持 role: user, assistant, system
            role = msg["role"]
            if role in ("user", "assistant", "system"):
                request_messages.append({
                    "role": role,
                    "content": msg["content"]
                })

        # 构建请求体
        request_body = {
            "model": model,
            "messages": request_messages,
            "temperature": temperature,
            "stream": stream,
        }

        # 添加可选参数
        if "max_tokens" in extra_kwargs:
            request_body["max_tokens"] = extra_kwargs["max_tokens"]
        if "top_p" in extra_kwargs:
            request_body["top_p"] = extra_kwargs["top_p"]

        return request_body

    def _extract_usage(self, response: Dict, model: str) -> Dict:
        """提取 token 使用信息

        Args:
            response: API 响应字典
            model: 模型名称

        Returns:
            usage_info 字典
        """
        if response and "usage" in response:
            usage = response["usage"]
            return {
                'prompt_tokens': usage.get("prompt_tokens", 0),
                'completion_tokens': usage.get("completion_tokens", 0),
                'total_tokens': usage.get("total_tokens", 0),
                'model_provider': 'doubao',
                'model_name': model
            }
        return super()._extract_usage(response, model, 'doubao')

    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
