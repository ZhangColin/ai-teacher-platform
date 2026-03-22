"""Google Gemini 适配器

配置要求:
- api_key: Google API Key
"""
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple
import google.genai as genai

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini 适配器

    使用新的 google.genai SDK (替代已弃用的 google.generativeai)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = genai.Client(api_key=self.api_key)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Tuple[str, Optional[Dict]]:
        contents = self._to_gemini_format(messages, system_prompt)

        config = genai.types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=kwargs.get("max_tokens", 4096),
            system_instruction=system_prompt,
        )

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        content = self._extract_content(response)
        usage = self._extract_usage(response, model)
        return content, usage

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str | Dict, None]:
        contents = self._to_gemini_format(messages, system_prompt)

        config = genai.types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=kwargs.get("max_tokens", 4096),
            system_instruction=system_prompt,
        )

        response = await self.client.aio.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config,
        )

        usage_info = None

        async for chunk in response:
            content = self._extract_content(chunk)
            if content:
                yield content
            # 提取 usage 信息
            usage_info = self._extract_usage(chunk, model)

        yield usage_info or self._extract_usage(None, model)

    def _to_gemini_format(self, messages: List[Dict[str, str]],
                          system_prompt: Optional[str]) -> List[genai.types.Content]:
        """转换为 Gemini contents 格式"""
        contents = []

        # 转换消息
        for msg in messages:
            role = msg["role"]
            if role == "system":
                continue  # 系统提示词通过 config 传递
            gemini_role = "user" if role == "user" else "model"
            contents.append(genai.types.Content(
                role=gemini_role,
                parts=[genai.types.Part(text=msg["content"])]
            ))

        return contents

    def _extract_content(self, response) -> str:
        """从响应中提取文本内容"""
        if not response:
            return ""
        # 处理新的 google.genai 响应格式
        if hasattr(response, 'candidates') and response.candidates:
            if response.candidates[0].content and response.candidates[0].content.parts:
                parts = response.candidates[0].content.parts
                text_parts = [p.text for p in parts if hasattr(p, 'text') and p.text]
                return ''.join(text_parts)
        return ""

    def _extract_usage(self, response, model: str) -> Dict:
        """提取 token 使用信息"""
        if response and hasattr(response, 'usage_metadata'):
            metadata = response.usage_metadata
            return {
                'prompt_tokens': getattr(metadata, 'prompt_token_count', 0),
                'completion_tokens': getattr(metadata, 'candidates_token_count', 0),
                'total_tokens': getattr(metadata, 'total_token_count', 0),
                'model_provider': 'google',
                'model_name': model
            }
        return super()._extract_usage(response, model, 'google')
