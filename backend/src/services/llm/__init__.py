"""LLM 适配器模块

提供统一的接口调用多个 LLM 供应商。
"""

from .base_adapter import BaseLLMAdapter
# from .factory import create_adapter, ADAPTER_REGISTRY  # Task 7 创建

__all__ = [
    "BaseLLMAdapter",
    # "create_adapter",
    # "ADAPTER_REGISTRY",
]
