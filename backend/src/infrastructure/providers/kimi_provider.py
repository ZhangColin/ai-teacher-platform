# -*- coding: utf-8 -*-
"""
Kimi (Moonshot AI) Provider实现

提供 Kimi API 的实现，Kimi 兼容 OpenAI 协议
支持对话、文件上传、多模态能力
"""
import logging
from typing import List, AsyncGenerator, Optional

import httpx
from openai import AsyncOpenAI

from src.infrastructure.providers.base import AIProvider
from src.domain.entities.message import Message
from src.domain.value_objects.message_role import MessageRole

logger = logging.getLogger(__name__)


class KimiProvider(AIProvider):
    """
    Kimi (Moonshot AI) API 提供商实现

    支持能力：
    - 流式/非流式对话
    - 文件上传和文档问答
    - 多模态图片识别

    支持的模型：
    - moonshot-v1-8k
    - moonshot-v1-32k
    - moonshot-v1-128k
    """

    def __init__(self, api_key: str, base_url: str = "https://api.moonshot.cn"):
        """
        初始化 Kimi Provider

        Args:
            api_key: Kimi API 密钥
            base_url: API 基础 URL（默认为 Kimi 官方 API 地址）
        """
        self._api_key = api_key
        self._base_url = base_url
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self._http_client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        logger.info(f"Kimi Provider initialized with base_url: {base_url}")

    def get_supported_models(self) -> List[str]:
        """
        获取支持的模型列表

        Returns:
            List[str]: Kimi 模型列表
        """
        return ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]

    async def chat_stream(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式对话

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数（0-1）
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Yields:
            str: 流式返回的文本片段
        """
        try:
            # 转换消息格式
            kimi_messages = self._convert_messages(messages)

            # 调用 Kimi API (stream=True 返回 async generator)
            stream = self._client.chat.completions.create(
                model=model,
                messages=kimi_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            # 流式返回内容
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Kimi stream chat error: {e}")
            raise

    async def chat(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        非流式对话

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数（0-1）
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Returns:
            str: 完整的 AI 响应文本
        """
        try:
            # 转换消息格式
            kimi_messages = self._convert_messages(messages)

            # 调用 Kimi API
            response = await self._client.chat.completions.create(
                model=model,
                messages=kimi_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                **kwargs
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Kimi chat error: {e}")
            raise

    async def upload_file(
        self,
        file_path: str,
        filename: str
    ) -> Optional[str]:
        """
        上传文件到 Kimi 服务器

        Args:
            file_path: 本地文件路径
            filename: 文件名

        Returns:
            str: file_id，用于后续对话引用
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/octet-stream')}
                response = await self._http_client.post('/v1/files', files=files)

            response.raise_for_status()
            result = response.json()
            file_id = result.get('id')
            logger.info(f"Kimi file uploaded: {filename} -> {file_id}")
            return file_id

        except Exception as e:
            logger.error(f"Kimi file upload error: {e}")
            return None

    async def chat_with_file(
        self,
        messages: List[Message],
        file_ids: List[str],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        带文件的流式对话

        Args:
            messages: 消息列表
            file_ids: 通过 upload_file 获取的文件 ID 列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Yields:
            str: 流式返回的文本片段
        """
        try:
            kimi_messages = self._convert_messages(messages)

            # Kimi 文件引用格式 - 在第一条消息中添加文件引用
            if file_ids and kimi_messages:
                # 创建文件引用消息
                file_content = []
                for file_id in file_ids:
                    file_content.append({"type": "file", "file_id": file_id})

                # 将文件引用插入到第一条用户消息
                for msg in kimi_messages:
                    if msg.get("role") == "user":
                        if isinstance(msg.get("content"), str):
                            msg["content"] = [
                                {"type": "text", "text": msg["content"]},
                                *file_content
                            ]
                        break

            stream = self._client.chat.completions.create(
                model=model,
                messages=kimi_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Kimi chat with file error: {e}")
            raise

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        **kwargs
    ) -> str:
        """
        图片识别（Kimi 支持图片输入）

        实际使用时通过 chat 接口传入图片 URL 或 base64
        Kimi 不支持生成图片，只支持图片识别

        Args:
            prompt: 图片描述提示词（用于识别）
            size: 图片尺寸
            **kwargs: 其他参数

        Returns:
            str: 图片识别结果

        Raises:
            NotImplementedError: Kimi 不支持图片生成
        """
        raise NotImplementedError(
            "Kimi does not support image generation. "
            "Use chat with image_url content for image recognition."
        )

    async def generate_audio(
        self,
        text: str,
        voice: str = "alloy",
        **kwargs
    ) -> str:
        """
        生成音频

        Kimi 不支持音频生成

        Args:
            text: 要转换为音频的文本
            voice: 音色/声音
            **kwargs: 其他参数

        Returns:
            str: 音频文件 URL 或 base64 编码

        Raises:
            NotImplementedError: Kimi 不支持音频生成
        """
        raise NotImplementedError(
            "Kimi does not support audio generation."
        )

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """
        将 Message 对象列表转换为 Kimi API 格式

        Args:
            messages: Message 对象列表

        Returns:
            List[dict]: Kimi 格式的消息列表（与 OpenAI 格式相同）
        """
        kimi_messages = []

        for message in messages:
            msg_dict = {
                "role": self._convert_role(message.role),
                "content": message.content
            }
            kimi_messages.append(msg_dict)

        return kimi_messages

    def _convert_role(self, role: MessageRole) -> str:
        """
        转换消息角色

        Args:
            role: MessageRole 枚举

        Returns:
            str: Kimi 格式的角色字符串（与 OpenAI 格式相同）
        """
        if role.is_system_message():
            return "system"
        elif role.is_user_message():
            return "user"
        elif role.is_assistant_message():
            return "assistant"
        else:
            return "user"  # 默认为 user

    async def close(self):
        """关闭 HTTP 客户端"""
        await self._http_client.aclose()
