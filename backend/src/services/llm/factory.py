"""LLM 适配器工厂"""
from typing import Dict, Type

from .base_adapter import BaseLLMAdapter
from .openai_adapter import OpenAIAdapter
from .bedrock_adapter import BedrockAdapter
from .gemini_adapter import GeminiAdapter
from .doubao_adapter import DoubaoAdapter

# 供应商代码到适配器类的映射
ADAPTER_REGISTRY: Dict[str, Type[BaseLLMAdapter]] = {
    # OpenAI 兼容
    "openai": OpenAIAdapter,
    "deepseek": OpenAIAdapter,
    "kimi": OpenAIAdapter,
    "moonshot": OpenAIAdapter,
    "glm": OpenAIAdapter,
    "zhipu": OpenAIAdapter,
    # AWS Bedrock
    "claude": BedrockAdapter,
    "anthropic": BedrockAdapter,
    # Google
    "google": GeminiAdapter,
    "gemini": GeminiAdapter,
    # 豆包
    "doubao": DoubaoAdapter,
    "bytedance": DoubaoAdapter,
}


def create_adapter(provider_code: str, **kwargs) -> BaseLLMAdapter:
    """创建适配器实例

    Args:
        provider_code: 供应商代码 (如 'openai', 'claude', 'google')
        **kwargs: 传递给适配器的参数

    Returns:
        适配器实例

    Raises:
        ValueError: 不支持的供应商
    """
    adapter_class = ADAPTER_REGISTRY.get(provider_code.lower())
    if not adapter_class:
        raise ValueError(f"不支持的供应商: {provider_code}")
    return adapter_class(**kwargs)


def get_supported_providers() -> list:
    """获取支持的供应商列表"""
    return list(set(ADAPTER_REGISTRY.keys()))
