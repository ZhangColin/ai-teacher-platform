"""
NewAPI Provider实现

NewAPI 是一个 AI 聚合平台，兼容 OpenAI API 规范
"""
import base64
import logging
from typing import List, AsyncGenerator, Optional

from openai import AsyncOpenAI

from src.infrastructure.providers.base import AIProvider
from src.domain.entities.message import Message
from src.domain.value_objects.message_role import MessageRole

logger = logging.getLogger(__name__)


class NewAPIProvider(AIProvider):
    """NewAPI Provider 实现

    由于 NewAPI 兼容 OpenAI API 规范，直接使用 OpenAI SDK
    """

    def __init__(self, api_key: str, base_url: str):
        """
        初始化 NewAPI Provider

        Args:
            api_key: NewAPI API密钥
            base_url: NewAPI API基础URL（如 https://your-domain.com/v1）
        """
        self._api_key = api_key
        self._base_url = base_url
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        logger.info(f"NewAPI Provider initialized with base_url: {base_url}")

    def get_supported_models(self) -> List[str]:
        """
        获取支持的模型列表

        模型由数据库动态管理，此处返回空列表
        """
        return []

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
            max_tokens: 最大生成token数
            **kwargs: 其他参数

        Yields:
            str: 流式返回的文本片段
        """
        try:
            openai_messages = self._convert_messages(messages)
            stream = self._client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"NewAPI stream chat error: {e}")
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
            max_tokens: 最大生成token数
            **kwargs: 其他参数

        Returns:
            str: 完整的AI响应文本
        """
        try:
            openai_messages = self._convert_messages(messages)
            response = await self._client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"NewAPI chat error: {e}")
            raise

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        **kwargs
    ) -> str:
        """
        生成图片

        Args:
            prompt: 图片描述提示词
            size: 图片尺寸
            **kwargs: 其他参数

        Returns:
            str: 图片URL
        """
        try:
            response = await self._client.images.generate(
                model=kwargs.get("model", "dall-e-3"),
                prompt=prompt,
                size=size,
                **kwargs
            )
            return response.data[0].url
        except Exception as e:
            logger.error(f"NewAPI image generation error: {e}")
            raise

    async def generate_audio(
        self,
        text: str,
        voice: str = "alloy",
        **kwargs
    ) -> str:
        """
        生成音频

        Args:
            text: 要转换为音频的文本
            voice: 音色/声音
            **kwargs: 其他参数

        Returns:
            str: 音频文件的base64编码
        """
        try:
            response = await self._client.audio.speech.create(
                model=kwargs.get("model", "tts-1"),
                voice=voice,
                input=text,
                **kwargs
            )
            audio_content = response.content
            base64_audio = base64.b64encode(audio_content).decode("utf-8")
            return f"data:audio/mp3;base64,{base64_audio}"
        except Exception as e:
            logger.error(f"NewAPI audio generation error: {e}")
            raise

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """
        将 Message 对象列表转换为 OpenAI API 格式

        Args:
            messages: Message 对象列表

        Returns:
            List[dict]: OpenAI 格式的消息列表
        """
        openai_messages = []
        for message in messages:
            msg_dict = {
                "role": self._convert_role(message.role),
                "content": message.content
            }
            openai_messages.append(msg_dict)
        return openai_messages

    def _convert_role(self, role: MessageRole) -> str:
        """
        转换消息角色

        Args:
            role: MessageRole 枚举

        Returns:
            str: OpenAI 格式的角色字符串
        """
        if role.is_system_message():
            return "system"
        elif role.is_user_message():
            return "user"
        elif role.is_assistant_message():
            return "assistant"
        else:
            return "user"
