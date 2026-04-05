"""LLM 适配器抽象基类

所有供应商适配器继承此基类，提供统一的 chat/chat_stream 接口。

Usage 信息约定（chat_stream 最后 yield 的 dict）：
{
    'type': 'usage',
    'prompt_tokens': int,
    'completion_tokens': int,
    'total_tokens': int,
    'model_provider': str,
    'model_name': str,
    'finish_reason': 'stop' | 'length' | 'content_filter' | ...
}

finish_reason 语义：
- 'stop'：模型正常结束
- 'length'：因 token 上限被截断，续写管理器会据此决定是否自动续写
- 'content_filter'：内容被安全过滤
- 其他值：各供应商特有，视为正常结束
"""
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional, Tuple

import httpx

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

    @staticmethod
    def _create_http_client(timeout: float = 120.0) -> httpx.AsyncClient:
        """创建不走系统代理的 httpx 客户端，避免本地代理导致 TLS 握手失败"""
        return httpx.AsyncClient(trust_env=False, timeout=timeout)

    @property
    @abstractmethod
    def provider_code(self) -> str:
        """返回供应商代码（如 'openai'、'deepseek'），用于日志和 usage 信息"""
        pass

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
            usage_info 必须包含 'finish_reason' 字段
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
            str: 内容片段
            Dict: 最后 yield 一个 usage_info dict（必须包含 'type': 'usage' 和 'finish_reason'）
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

    def _build_usage(self, model: str, prompt_tokens: int = 0,
                     completion_tokens: int = 0, finish_reason: str = 'stop') -> Dict:
        """构建标准 usage 信息"""
        return {
            'type': 'usage',
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': prompt_tokens + completion_tokens,
            'model_provider': self.provider_code,
            'model_name': model,
            'finish_reason': finish_reason,
        }

    def _extract_usage(self, response, model: str, provider: str) -> Dict:
        """提取 token 使用信息（子类可覆盖，保留向后兼容）"""
        return {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'model_provider': provider,
            'model_name': model,
            'finish_reason': 'stop',
        }
