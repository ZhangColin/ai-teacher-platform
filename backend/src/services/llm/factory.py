"""LLM 适配器工厂"""
from typing import Dict, Type

from .base_adapter import BaseLLMAdapter
from .openai_adapter import OpenAIAdapter
from .deepseek_adapter import DeepSeekAdapter
from .kimi_adapter import KimiAdapter
from .glm_adapter import GLMAdapter
from .bedrock_adapter import BedrockAdapter
from .gemini_adapter import GeminiAdapter
from .doubao_adapter import DoubaoAdapter

# 供应商代码到适配器类的映射
ADAPTER_REGISTRY: Dict[str, Type[BaseLLMAdapter]] = {
    # OpenAI（已测试通过 - 不要动）
    "openai": OpenAIAdapter,
    # DeepSeek 独立适配器
    "deepseek": DeepSeekAdapter,
    # Kimi 独立适配器（处理 temperature=1.0 等特殊需求）
    "kimi": KimiAdapter,
    "moonshot": KimiAdapter,
    # GLM 独立适配器
    "glm": GLMAdapter,
    "zhipu": GLMAdapter,
    # AWS Bedrock (供应商代码: bedrock)
    "bedrock": BedrockAdapter,
    # Anthropic 直接 API (如果需要的话，目前使用 Bedrock)
    # "claude": AnthropicAdapter,  # 待实现
    # "anthropic": AnthropicAdapter,  # 待实现
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
