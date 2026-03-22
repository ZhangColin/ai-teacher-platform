"""LLM 适配器抽象基类"""
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class BaseLLMAdapter(ABC):
    """LLM 适配器抽象基类

    所有适配器必须实现此接口，确保统一的调用方式。
    """

    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        """
        初始化适配器

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            **kwargs: 额外配置参数
        """
        self.api_key = api_key
        self.base_url = base_url
        self.extra_config = kwargs

    @abstractmethod
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
            **kwargs: 额外参数

        Returns:
            (response_content, usage_info)
            usage_info 格式: {
                'prompt_tokens': int,
                'completion_tokens': int,
                'total_tokens': int,
                'model_provider': str,
                'model_name': str
            }
        """
        pass

    @abstractmethod
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
        pass

    def _build_messages(self, messages: List[Dict[str, str]],
                       system_prompt: Optional[str]) -> List[Dict]:
        """构建标准消息列表"""
        result = []
        if system_prompt:
            result.append({"role": "system", "content": system_prompt})
        result.extend(messages)
        return result

    def _extract_usage(self, response, model: str, provider: str) -> Dict:
        """提取 token 使用信息（子类可覆盖）"""
        return {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'model_provider': provider,
            'model_name': model
        }
