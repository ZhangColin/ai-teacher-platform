# 多 LLM 供应商适配器设计文档

**日期**: 2026-03-22
**作者**: Claude Opus 4.6
**状态**: 设计阶段

---

## 1. 概述

### 1.1 目标

为 AI 智能备课平台接入多个 LLM 供应商，支持统一的调用接口，确保所有供应商都支持流式输出。

### 1.2 范围

**接入供应商**:
- OpenAI (GPT-5.4 系列)
- DeepSeek (V3.2 系列)
- Kimi/Moonshot (K2.5 系列)
- GLM/智谱 (GLM-5 系列)
- **Claude** (通过 AWS Bedrock)
- **Google Gemini** (Gemini 3.1 系列)
- **豆包** (Seed 2.0 系列)

**关键要求**:
- 所有供应商必须支持流式输出
- 统一使用数据库配置，不使用环境变量
- 清晰的架构，易于扩展新供应商

---

## 2. 架构设计

### 2.1 目录结构

```
backend/src/services/llm/
├── __init__.py              # 模块导出
├── base_adapter.py          # 抽象基类
├── openai_adapter.py        # OpenAI 兼容适配器
├── bedrock_adapter.py       # AWS Bedrock 适配器 (Claude)
├── gemini_adapter.py        # Google Gemini 适配器
├── doubao_adapter.py        # 豆包适配器
└── factory.py               # 适配器工厂

backend/src/services/
└── ai_service.py            # 重构后的 AI 服务
```

### 2.2 类图

```
┌─────────────────────────────────────────────────────────────────┐
│                        AIService                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   _get_adapter()                            │ │
│  │    │                                                       │ │
│  │    ▼                                                       │ │
│  │  ┌─────────────┐     ┌─────────────────────────────────┐  │ │
│  │  │   Factory   │────▶│       ADAPTER_REGISTRY          │  │ │
│  │  └─────────────┘     │  provider -> AdapterClass       │  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    BaseLLMAdapter                          │ │
│  │  + chat(messages, model) -> (content, usage)              │ │
│  │  + chat_stream(messages, model) -> AsyncGenerator         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                  │
│          ┌───────────────────┼───────────────────┐              │
│          ▼                   ▼                   ▼              │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐    │
│  │ OpenAIAdapter │   │BedrockAdapter │   │GeminiAdapter  │    │
│  │ (OpenAI兼容)  │   │ (AWS Bedrock) │   │ (Google)      │    │
│  └───────────────┘   └───────────────┘   └───────────────┘    │
│                                                              │
│  ┌───────────────┐                                            │
│  │ DoubaoAdapter │                                            │
│  │ (豆包)        │                                            │
│  └───────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 接口定义

### 3.1 BaseLLMAdapter 抽象基类

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional, Tuple

class BaseLLMAdapter(ABC):
    """LLM 适配器抽象基类

    所有适配器必须实现此接口，确保统一的调用方式。
    """

    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
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

    def _extract_usage(self, response, model: str,
                       provider: str) -> Dict:
        """提取 token 使用信息（子类实现）"""
        return {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'model_provider': provider,
            'model_name': model
        }
```

### 3.2 工厂模式

```python
# factory.py
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
    """创建适配器实例"""
    adapter_class = ADAPTER_REGISTRY.get(provider_code.lower())
    if not adapter_class:
        raise ValueError(f"Unsupported provider: {provider_code}")
    return adapter_class(**kwargs)
```

---

## 4. 各供应商适配器实现

### 4.1 OpenAIAdapter (OpenAI 兼容)

**支持**: OpenAI, DeepSeek, Kimi, GLM

**依赖**: `openai` (已有)

**关键点**:
- 使用 AsyncOpenAI 客户端
- 流式输出使用 `stream=True`
- 消息格式标准 OpenAI 格式

### 4.2 BedrockAdapter (AWS Bedrock)

**支持**: Claude

**依赖**: `boto3` (新增)

**配置**:
- `api_key`: AWS Access Key ID
- `base_url`: AWS Region
- `aws_secret_access_key`: AWS Secret Access Key

**关键点**:
- 使用 Converse API (新版)
- 流式输出使用 `converse_stream`
- 消息格式需要转换

### 4.3 GeminiAdapter (Google Gemini)

**支持**: Google Gemini

**依赖**: `google-generativeai` (新增)

**配置**:
- `api_key`: Google API Key

**关键点**:
- 使用 `genai.GenerativeModel`
- 流式输出使用 `stream=True`
- 消息格式为 `contents` 而非 `messages`

### 4.4 DoubaoAdapter (豆包)

**支持**: 豆包/字节跳动

**依赖**: `volcengine-python-sdk` (新增)

**配置**:
- `api_key`: VolcEngine API Key
- `base_url`: Endpoint URL

**关键点**:
- 使用 MaasService
- 消息格式需要转换
- 流式输出处理

---

## 5. 数据库配置

### 5.1 model_providers 表扩展

在 `extra_config` 字段存储供应商特定配置:

```json
// Bedrock 示例
{
  "aws_secret_access_key": "xxxxx",
  "region": "us-east-1"
}

// 豆包示例
{
  "endpoint": "https://ark.cn-beijing.volces.com/api/v3"
}
```

### 5.2 API 密钥加密

所有 API 密钥使用 `EncryptionService` 加密存储。

---

## 6. 依赖更新

```txt
# requirements.txt 新增
boto3>=1.35.0
google-generativeai>=0.8.0
volcengine>=1.0.0
```

---

## 7. 迁移计划

### 阶段 1: 创建适配器架构
1. 创建 `llm/` 目录结构
2. 实现 `BaseLLMAdapter`
3. 实现工厂模式

### 阶段 2: 实现各适配器
1. `OpenAIAdapter` (重构现有代码)
2. `BedrockAdapter` (Claude)
3. `GeminiAdapter` (Google)
4. `DoubaoAdapter` (豆包)

### 阶段 3: 重构 AIService
1. 移除环境变量回退逻辑
2. 使用工厂模式获取适配器
3. 统一流式输出接口

### 阶段 4: 测试
1. 单元测试各适配器
2. 集成测试流式输出
3. 端到端测试

---

## 8. 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 豆包 SDK 包名不确定 | 先搜索确认，或使用 HTTP API 直接调用 |
| Bedrock 流式输出格式特殊 | 仔细阅读文档，处理特殊格式 |
| Gemini 消息格式差异 | 实现格式转换函数 |
| 不同供应商的 token 计算方式 | 统一 usage_info 格式，缺失字段填 0 |

---

## 9. 参考资料

- [AWS Bedrock Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-runtime_example_bedrock-runtime_Converse_AnthropicClaude_section.html)
- [Gemini API Quickstart](https://ai.google.dev/gemini-api/docs/quickstart)
- [火山引擎豆包 API](https://www.volcengine.com/docs/82379/1978533)
