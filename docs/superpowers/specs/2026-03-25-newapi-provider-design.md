# NewAPI Provider 集成设计

**日期**: 2026-03-25
**作者**: Claude
**状态**: 设计中

## 1. 概述

本文档描述如何将 NewAPI（AI 聚合平台）作为新的模型供应商集成到系统中。NewAPI 是一个自部署的 AI 聚合平台，统一兼容 OpenAI API 规范。

## 2. 目标

1. 添加 NewAPI 作为新的模型供应商
2. 通过管理后台动态添加/管理 NewAPI 下的模型
3. 不修改现有的 provider 架构
4. 延用现有的数据库驱动配置管理

## 3. 架构设计

### 3.1 数据模型（无需修改）

使用现有的数据模型：

```
ModelProviderModel (model_providers 表)
├── id: CHAR(36)
├── provider_code: "newapi" (唯一)
├── provider_name: "NewAPI"
├── base_url: "https://your-domain.com/v1" (用户配置)
├── api_key_encrypted: "..." (加密存储)
├── is_enabled: true
└── order: 排序

ModelConfigModel (model_configs 表)
├── id: CHAR(36)
├── provider_id: 关联到 newapi provider
├── model_code: "gpt-4o" (模型代码)
├── model_name: "GPT-4o" (显示名称)
├── capabilities: "chat,vision" (逗号分隔)
└── is_enabled: true
```

### 3.2 Provider 类层次

```
AIProvider (抽象基类)
    ├── OpenAIProvider
    ├── DeepSeekProvider
    ├── KimiProvider
    └── NewAPIProvider (新增)
        - 继承 AIProvider
        - 使用 OpenAI SDK（兼容性）
        - 实现所有抽象方法
```

### 3.3 组件交互

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ 管理后台    │────▶│ ModelProvider │     │ NewAPIProvider│
│ /admin      │     │   Service    │────▶│   (新建)     │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                      │
                           ▼                      ▼
                    ┌──────────────┐     ┌─────────────┐
                    │   Database   │     │  NewAPI     │
                    │ (MySQL)      │     │  Server     │
                    └──────────────┘     └─────────────┘
```

## 4. 实现方案

### 4.1 新建 NewAPIProvider

**文件**: `backend/src/infrastructure/providers/newapi_provider.py`

```python
"""
NewAPI Provider实现

NewAPI 是一个 AI 聚合平台，兼容 OpenAI API 规范
"""
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
        self._api_key = api_key
        self._base_url = base_url
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        logger.info(f"NewAPI Provider initialized with base_url: {base_url}")

    def get_supported_models(self) -> List[str]:
        # 模型由数据库动态管理，此处返回空列表
        return []

    async def chat_stream(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
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

    async def chat(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
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

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        **kwargs
    ) -> str:
        # 如果 NewAPI 配置的模型支持图片生成，调用对应接口
        # 否则返回默认实现
        response = await self._client.images.generate(
            model=kwargs.get("model", "dall-e-3"),
            prompt=prompt,
            size=size,
            **kwargs
        )
        return response.data[0].url

    async def generate_audio(
        self,
        text: str,
        voice: str = "alloy",
        **kwargs
    ) -> str:
        # 调用 TTS 接口（如果 NewAPI 支持）
        response = await self._client.audio.speech.create(
            model=kwargs.get("model", "tts-1"),
            voice=voice,
            input=text,
            **kwargs
        )
        import base64
        audio_content = response.content
        base64_audio = base64.b64encode(audio_content).decode("utf-8")
        return f"data:audio/mp3;base64,{base64_audio}"

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        openai_messages = []
        for message in messages:
            msg_dict = {
                "role": self._convert_role(message.role),
                "content": message.content
            }
            openai_messages.append(msg_dict)
        return openai_messages

    def _convert_role(self, role: MessageRole) -> str:
        if role.is_system_message():
            return "system"
        elif role.is_user_message():
            return "user"
        elif role.is_assistant_message():
            return "assistant"
        else:
            return "user"
```

### 4.2 注册到 ProviderFactory

**文件**: `backend/src/infrastructure/providers/factory.py`

```python
# 修改内容
from src.infrastructure.providers.newapi_provider import NewAPIProvider

class ProviderFactory:
    _providers: Dict[str, Type[AIProvider]] = {
        "openai": OpenAIProvider,
        "deepseek": DeepSeekProvider,
        "kimi": KimiProvider,
        "newapi": NewAPIProvider,  # 新增
    }
```

### 4.3 AIService 无需修改

AIService 已经通过数据库动态读取配置，当创建 OpenAI 客户端时使用配置的 base_url 和 api_key。由于 NewAPI 兼容 OpenAI 规范，无需修改任何代码。

## 5. 部署步骤

### 5.1 开发环境

1. 创建 `newapi_provider.py` 文件
2. 修改 `factory.py` 注册 provider
3. 运行测试验证

### 5.2 生产环境

1. 部署代码
2. 重启服务
3. 通过管理后台配置 NewAPI

## 6. 使用流程

### 6.1 管理员配置

1. **添加供应商**
   - 访问 `/admin/model-providers`
   - 新增供应商：
     - 代码: `newapi`
     - 名称: `NewAPI`
     - API 地址: `https://your-domain.com/v1`
     - API 密钥: `your-api-key`

2. **添加模型**
   - 访问 `/admin/model-configs`
   - 新增模型：
     - 供应商: 选择 NewAPI
     - 模型代码: `gpt-4o`
     - 模型名称: `GPT-4o`
     - 能力: `chat,vision`

### 6.2 用户使用

- 在聊天界面选择模型（如 `newapi:gpt-4o`）
- 系统通过 NewAPI 调用对应模型

## 7. 文件变更清单

| 文件 | 操作 | 行数估计 |
|------|------|----------|
| `backend/src/infrastructure/providers/newapi_provider.py` | 新建 | ~150 |
| `backend/src/infrastructure/providers/factory.py` | 修改 | +2 |

## 8. 测试计划

### 8.1 单元测试

- 测试 NewAPIProvider 初始化
- 测试消息格式转换
- 测试 role 转换

### 8.2 集成测试

- 测试通过 NewAPI 调用聊天接口
- 测试流式输出
- 测试错误处理

### 8.3 手动测试

1. 通过管理后台添加 NewAPI 供应商
2. 添加模型配置
3. 在聊天界面选择模型并测试

## 9. 风险与注意事项

1. **API 兼容性**: NewAPI 声称兼容 OpenAI 规范，但某些高级功能可能不完全兼容
2. **错误处理**: 需要妥善处理 NewAPI 返回的错误信息
3. **性能**: NewAPI 作为聚合层，可能增加额外延迟

## 10. 后续优化

1. 考虑添加 NewAPI 特有的配置项（如超时、重试策略）
2. 如果 NewAPI 支持批量获取模型列表，可以考虑同步功能
