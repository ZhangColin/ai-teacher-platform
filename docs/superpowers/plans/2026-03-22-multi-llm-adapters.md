# 多 LLM 供应商适配器实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 AI 智能备课平台接入 Claude (AWS Bedrock)、Google Gemini、豆包三个新供应商，同时重构现有架构为适配器模式。

**架构:** 抽象层 + 多适配器模式。创建 BaseLLMAdapter 抽象基类，每个供应商实现独立适配器，通过工厂模式统一管理。

**Tech Stack:** Python 3.10+, FastAPI, SQLAlchemy, OpenAI SDK, boto3, google-generativeai, volcengine-python-sdk

---

## 文件结构

```
backend/src/services/llm/
├── __init__.py              # 模块导出
├── base_adapter.py          # 抽象基类 (新建)
├── openai_adapter.py        # OpenAI 兼容适配器 (新建)
├── bedrock_adapter.py       # AWS Bedrock 适配器 (新建)
├── gemini_adapter.py        # Google Gemini 适配器 (新建)
├── doubao_adapter.py        # 豆包适配器 (新建)
└── factory.py               # 适配器工厂 (新建)

backend/src/services/
├── ai_service.py            # 重构 AI 服务 (修改)
└── builtin_models.py        # 更新模型定义 (已完成)

backend/tests/unit/services/llm/
├── __init__.py
├── test_base_adapter.py
├── test_openai_adapter.py
├── test_bedrock_adapter.py
├── test_gemini_adapter.py
└── test_doubao_adapter.py

backend/requirements.txt     # 添加新依赖 (修改)
```

---

## Task 1: 添加依赖包

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 添加新依赖**

在 `requirements.txt` 末尾添加：

```txt
boto3>=1.35.0
google-generativeai>=0.8.0
volcengine-python-sdk>=1.0.0
```

- [ ] **Step 2: 安装依赖验证**

```bash
cd backend
pip install -r requirements.txt
```

预期：无错误

- [ ] **Step 3: 提交**

```bash
git add requirements.txt
git commit -m "deps: 添加 Claude/Gemini/豆包 SDK 依赖

- boto3: AWS Bedrock (Claude)
- google-generativeai: Google Gemini
- volcengine-python-sdk: 豆包

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: 创建 LLM 适配器模块结构

**Files:**
- Create: `backend/src/services/llm/__init__.py`
- Create: `backend/src/services/llm/base_adapter.py`

- [ ] **Step 1: 创建模块导出文件**

创建 `backend/src/services/llm/__init__.py`:

```python
"""LLM 适配器模块

提供统一的接口调用多个 LLM 供应商。
"""

from .base_adapter import BaseLLMAdapter
from .factory import create_adapter, ADAPTER_REGISTRY

__all__ = [
    "BaseLLMAdapter",
    "create_adapter",
    "ADAPTER_REGISTRY",
]
```

- [ ] **Step 2: 创建抽象基类**

创建 `backend/src/services/llm/base_adapter.py`:

```python
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
```

- [ ] **Step 3: 创建测试目录**

```bash
mkdir -p backend/tests/unit/services/llm
touch backend/tests/unit/services/llm/__init__.py
```

- [ ] **Step 4: 提交**

```bash
git add backend/src/services/llm/ backend/tests/unit/services/llm/
git commit -m "feat: 创建 LLM 适配器模块结构和抽象基类

- 定义 BaseLLMAdapter 抽象接口
- 统一 chat 和 chat_stream 方法签名
- 支持 usage_info 标准格式

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: 实现 OpenAI 适配器

**Files:**
- Create: `backend/src/services/llm/openai_adapter.py`
- Create: `backend/tests/unit/services/llm/test_openai_adapter.py`

- [ ] **Step 1: 实现 OpenAI 适配器**

创建 `backend/src/services/llm/openai_adapter.py`:

```python
"""OpenAI 兼容 API 适配器

支持: OpenAI, DeepSeek, Kimi, GLM
"""
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple
from openai import AsyncOpenAI

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI 兼容 API 适配器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=120.0,
            max_retries=2
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Tuple[str, Optional[Dict]]:
        messages = self._build_messages(messages, system_prompt)

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            **kwargs
        )

        content = response.choices[0].message.content
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
        messages = self._build_messages(messages, system_prompt)

        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
            **kwargs
        )

        usage_info = None

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

            if chunk.usage:
                usage_info = {
                    'prompt_tokens': chunk.usage.prompt_tokens,
                    'completion_tokens': chunk.usage.completion_tokens,
                    'total_tokens': chunk.usage.total_tokens,
                    'model_provider': 'openai',
                    'model_name': model
                }

        # 确保 usage_info 被发送
        if usage_info:
            yield usage_info

    def _extract_usage(self, response, model: str) -> Dict:
        provider = self.extra_config.get('provider', 'openai')
        if hasattr(response, 'usage') and response.usage:
            return {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
                'model_provider': provider,
                'model_name': model
            }
        return super()._extract_usage(response, model, provider)
```

- [ ] **Step 2: 编写基础测试**

创建 `backend/tests/unit/services/llm/test_openai_adapter.py`:

```python
"""测试 OpenAI 适配器"""
import pytest

from src.services.llm.openai_adapter import OpenAIAdapter


class TestOpenAIAdapter:
    """测试 OpenAI 适配器"""

    def test_init(self):
        """测试初始化"""
        adapter = OpenAIAdapter(
            api_key="sk-test",
            base_url="https://api.openai.com/v1"
        )
        assert adapter.api_key == "sk-test"
        assert adapter.base_url == "https://api.openai.com/v1"

    def test_build_messages(self):
        """测试消息构建"""
        adapter = OpenAIAdapter(api_key="sk-test")
        messages = [{"role": "user", "content": "hello"}]
        result = adapter._build_messages(messages, "You are helpful")
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_extract_usage(self):
        """测试 usage 提取"""
        adapter = OpenAIAdapter(
            api_key="sk-test",
            extra_config={'provider': 'deepseek'}
        )
        # Mock response
        class MockUsage:
            prompt_tokens = 10
            completion_tokens = 20
            total_tokens = 30

        class MockResponse:
            usage = MockUsage()

        usage = adapter._extract_usage(MockResponse(), "deepseek-chat")
        assert usage['prompt_tokens'] == 10
        assert usage['model_provider'] == 'deepseek'
```

- [ ] **Step 3: 运行测试验证**

```bash
cd backend
pytest tests/unit/services/llm/test_openai_adapter.py -v
```

预期：通过

- [ ] **Step 4: 提交**

```bash
git add backend/src/services/llm/openai_adapter.py
git add backend/tests/unit/services/llm/test_openai_adapter.py
git commit -m "feat: 实现 OpenAI 兼容适配器

- 支持 OpenAI/DeepSeek/Kimi/GLM 等兼容接口
- 实现 chat 和 chat_stream 方法
- 添加单元测试

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: 实现 Bedrock 适配器 (Claude)

**Files:**
- Create: `backend/src/services/llm/bedrock_adapter.py`
- Create: `backend/tests/unit/services/llm/test_bedrock_adapter.py`

- [ ] **Step 1: 实现 Bedrock 适配器**

创建 `backend/src/services/llm/bedrock_adapter.py`:

```python
"""AWS Bedrock 适配器 (Claude)

配置要求 (从数据库读取):
- api_key: AWS Access Key ID
- base_url: AWS Region (如 us-east-1)
- extra_config.aws_secret_access_key: AWS Secret Access Key
"""
import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class BedrockAdapter(BaseLLMAdapter):
    """AWS Bedrock 适配器 (Claude)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.region = self.base_url or "us-east-1"
        self.aws_secret_key = self.extra_config.get("aws_secret_access_key")

        self.client = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            aws_access_key_id=self.api_key,
            aws_secret_access_key=self.aws_secret_key
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Tuple[str, Optional[Dict]]:
        # 转换消息格式
        bedrock_messages = self._to_bedrock_format(messages)

        # 构建请求参数
        request_params = {
            "modelId": model,
            "messages": bedrock_messages,
            "inferenceConfig": {
                "temperature": temperature,
                "maxTokens": kwargs.get("max_tokens", 4096),
            }
        }

        if system_prompt:
            request_params["system"] = [{"text": system_prompt}]

        # 在线程池中执行同步调用
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.converse(**request_params)
            )

            content = response["output"]["message"]["content"][0]["text"]
            usage = self._extract_usage(response, model)
            return content, usage

        except ClientError as e:
            logger.error(f"Bedrock API 调用失败: {e}")
            raise

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str | Dict, None]:
        bedrock_messages = self._to_bedrock_format(messages)

        request_params = {
            "modelId": model,
            "messages": bedrock_messages,
            "inferenceConfig": {
                "temperature": temperature,
                "maxTokens": kwargs.get("max_tokens", 4096),
            }
        }

        if system_prompt:
            request_params["system"] = [{"text": system_prompt}]

        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.converse_stream(**request_params)
            )

            usage_info = None

            for chunk in response["stream"]:
                if "contentBlockDelta" in chunk:
                    yield chunk["contentBlockDelta"]["delta"]["text"]
                elif "metadata" in chunk:
                    usage_info = self._extract_usage(chunk["metadata"], model)

            if usage_info:
                yield usage_info

        except ClientError as e:
            logger.error(f"Bedrock 流式 API 调用失败: {e}")
            raise

    def _to_bedrock_format(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """转换为 Bedrock 消息格式"""
        bedrock_messages = []
        for msg in messages:
            role = msg["role"]
            if role == "system":
                continue  # Bedrock 使用 system 字段，不在 messages 中
            bedrock_role = "user" if role == "user" else "assistant"
            bedrock_messages.append({
                "role": bedrock_role,
                "content": [{"text": msg["content"]}]
            })
        return bedrock_messages

    def _extract_usage(self, response, model: str) -> Dict:
        if isinstance(response, dict) and "usage" in response:
            usage = response["usage"]
            return {
                'prompt_tokens': usage.get("inputTokens", 0),
                'completion_tokens': usage.get("outputTokens", 0),
                'total_tokens': usage.get("totalTokens", 0),
                'model_provider': 'bedrock',
                'model_name': model
            }
        return super()._extract_usage(response, model, 'bedrock')
```

- [ ] **Step 2: 编写测试**

创建 `backend/tests/unit/services/llm/test_bedrock_adapter.py`:

```python
"""测试 Bedrock 适配器"""
import pytest

from src.services.llm.bedrock_adapter import BedrockAdapter


class TestBedrockAdapter:
    """测试 Bedrock 适配器"""

    def test_init(self):
        """测试初始化"""
        adapter = BedrockAdapter(
            api_key="AKIAIOSFODNN7EXAMPLE",
            base_url="us-east-1",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        )
        assert adapter.region == "us-east-1"

    def test_to_bedrock_format(self):
        """测试消息格式转换"""
        adapter = BedrockAdapter(
            api_key="test",
            aws_secret_access_key="test"
        )
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"}
        ]
        result = adapter._to_bedrock_format(messages)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
```

- [ ] **Step 3: 运行测试**

```bash
cd backend
pytest tests/unit/services/llm/test_bedrock_adapter.py -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/src/services/llm/bedrock_adapter.py
git add backend/tests/unit/services/llm/test_bedrock_adapter.py
git commit -m "feat: 实现 AWS Bedrock 适配器 (Claude)

- 使用 boto3 Converse API
- 支持 chat 和 chat_stream 方法
- 消息格式转换

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: 实现 Gemini 适配器

**Files:**
- Create: `backend/src/services/llm/gemini_adapter.py`
- Create: `backend/tests/unit/services/llm/test_gemini_adapter.py`

- [ ] **Step 1: 实现 Gemini 适配器**

创建 `backend/src/services/llm/gemini_adapter.py`:

```python
"""Google Gemini 适配器

配置要求:
- api_key: Google API Key
"""
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple
import google.generativeai as genai

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini 适配器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        genai.configure(api_key=self.api_key)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Tuple[str, Optional[Dict]]:
        contents = self._to_gemini_format(messages, system_prompt)

        gemini_model = genai.GenerativeModel(model)

        response = await gemini_model.generate_content_async(
            contents,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=kwargs.get("max_tokens", 4096),
            )
        )

        content = response.text
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

        gemini_model = genai.GenerativeModel(model)

        response = await gemini_model.generate_content_async(
            contents,
            stream=True,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=kwargs.get("max_tokens", 4096),
            )
        )

        usage_info = None

        async for chunk in response:
            if chunk.text:
                yield chunk.text
            # Gemini 流式响应可能不包含 usage，需要特殊处理
            if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                usage_info = self._extract_usage(chunk, model)

        yield usage_info or self._extract_usage(None, model)

    def _to_gemini_format(self, messages: List[Dict[str, str]],
                          system_prompt: Optional[str]) -> List:
        """转换为 Gemini contents 格式"""
        contents = []

        # 添加系统提示词
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": system_prompt}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "OK, I understand."}]
            })

        # 转换消息
        for msg in messages:
            role = msg["role"]
            if role == "system":
                continue  # 系统提示词已处理
            gemini_role = "user" if role == "user" else "model"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": msg["content"]}]
            })

        return contents

    def _extract_usage(self, response, model: str) -> Dict:
        if response and hasattr(response, 'usage_metadata'):
            metadata = response.usage_metadata
            return {
                'prompt_tokens': metadata.prompt_token_count if hasattr(metadata, 'prompt_token_count') else 0,
                'completion_tokens': metadata.candidates_token_count if hasattr(metadata, 'candidates_token_count') else 0,
                'total_tokens': metadata.total_token_count if hasattr(metadata, 'total_token_count') else 0,
                'model_provider': 'google',
                'model_name': model
            }
        return super()._extract_usage(response, model, 'google')
```

- [ ] **Step 2: 编写测试**

创建 `backend/tests/unit/services/llm/test_gemini_adapter.py`:

```python
"""测试 Gemini 适配器"""
import pytest

from src.services.llm.gemini_adapter import GeminiAdapter


class TestGeminiAdapter:
    """测试 Gemini 适配器"""

    def test_init(self):
        """测试初始化"""
        adapter = GeminiAdapter(api_key="test-key")
        assert adapter.api_key == "test-key"

    def test_to_gemini_format(self):
        """测试消息格式转换"""
        adapter = GeminiAdapter(api_key="test-key")
        messages = [
            {"role": "user", "content": "hello"}
        ]
        result = adapter._to_gemini_format(messages, None)
        assert len(result) == 1
        assert result[0]["role"] == "user"
```

- [ ] **Step 3: 运行测试**

```bash
cd backend
pytest tests/unit/services/llm/test_gemini_adapter.py -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/src/services/llm/gemini_adapter.py
git add backend/tests/unit/services/llm/test_gemini_adapter.py
git commit -m "feat: 实现 Google Gemini 适配器

- 使用 google-generativeai SDK
- 支持 chat 和 chat_stream 方法
- Gemini contents 格式转换

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: 实现豆包适配器

**Files:**
- Create: `backend/src/services/llm/doubao_adapter.py`
- Create: `backend/tests/unit/services/llm/test_doubao_adapter.py`

- [ ] **Step 1: 实现豆包适配器**

创建 `backend/src/services/llm/doubao_adapter.py`:

```python
"""豆包 VolcEngine 适配器

配置要求:
- api_key: VolcEngine API Key
- base_url: Endpoint URL (可选)

依赖: volcengine-python-sdk
"""
import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)

try:
    from volcengine.maas import MaasService, ChatRole
except ImportError:
    MaasService = None
    ChatRole = None
    logger.warning("volcengine-python-sdk 未安装")


class DoubaoAdapter(BaseLLMAdapter):
    """豆包 VolcEngine 适配器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if MaasService is None:
            raise ImportError("请安装 volcengine-python-sdk: pip install volcengine-python-sdk")

        self.client = MaasService(
            api_key=self.api_key,
            endpoint=self.base_url
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Tuple[str, Optional[Dict]]:
        req = self._build_request(model, messages, system_prompt, temperature, kwargs)

        loop = asyncio.get_event_loop()
        try:
            resp = await loop.run_in_executor(
                None,
                lambda: self.client.chat(req)
            )

            content = resp["choices"][0]["message"]["content"]
            usage = self._extract_usage(resp, model)
            return content, usage

        except Exception as e:
            logger.error(f"豆包 API 调用失败: {e}")
            raise

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str | Dict, None]:
        req = self._build_request(model, messages, system_prompt, temperature, kwargs)
        req["stream"] = True

        loop = asyncio.get_event_loop()
        try:
            # 豆包流式实现
            resp = await loop.run_in_executor(
                None,
                lambda: self.client.chat(req)
            )

            # 处理流式响应
            for chunk in resp:
                if "choices" in chunk and chunk["choices"]:
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content

                if "usage" in chunk:
                    yield self._extract_usage(chunk, model)

        except Exception as e:
            logger.error(f"豆包流式 API 调用失败: {e}")
            raise

    def _build_request(self, model: str, messages: List[Dict[str, str]],
                      system_prompt: Optional[str], temperature: float,
                      extra_kwargs: Dict) -> Dict:
        """构建豆包 API 请求"""
        doubao_messages = []

        # 添加系统提示词
        if system_prompt:
            doubao_messages.append({
                "role": ChatRole.SYSTEM,
                "content": system_prompt
            })

        # 转换消息
        for msg in messages:
            role = msg["role"]
            if role == "user":
                doubao_messages.append({
                    "role": ChatRole.USER,
                    "content": msg["content"]
                })
            elif role == "assistant":
                doubao_messages.append({
                    "role": ChatRole.ASSISTANT,
                    "content": msg["content"]
                })

        return {
            "model": {
                "name": model
            },
            "messages": doubao_messages,
            "parameters": {
                "temperature": temperature,
                "max_tokens": extra_kwargs.get("max_tokens", 4096),
            }
        }

    def _extract_usage(self, response, model: str) -> Dict:
        if isinstance(response, dict) and "usage" in response:
            usage = response["usage"]
            return {
                'prompt_tokens': usage.get("prompt_tokens", 0),
                'completion_tokens': usage.get("completion_tokens", 0),
                'total_tokens': usage.get("total_tokens", 0),
                'model_provider': 'doubao',
                'model_name': model
            }
        return super()._extract_usage(response, model, 'doubao')
```

- [ ] **Step 2: 编写测试**

创建 `backend/tests/unit/services/llm/test_doubao_adapter.py`:

```python
"""测试豆包适配器"""
import pytest

from src.services.llm.doubao_adapter import DoubaoAdapter


class TestDoubaoAdapter:
    """测试豆包适配器"""

    def test_init_without_sdk(self, monkeypatch):
        """测试没有 SDK 时初始化"""
        # 模拟 SDK 未安装
        import src.services.llm.doubao_adapter as m
        monkeypatch.setattr(m, "MaasService", None)

        with pytest.raises(ImportError):
            DoubaoAdapter(api_key="test")

    def test_build_request(self):
        """测试请求构建"""
        adapter = DoubaoAdapter(api_key="test-key")
        messages = [{"role": "user", "content": "hello"}]

        req = adapter._build_request("seed-2.0-pro", messages, None, 0.7, {})

        assert req["model"]["name"] == "seed-2.0-pro"
        assert "messages" in req
        assert "parameters" in req
```

- [ ] **Step 3: 运行测试**

```bash
cd backend
pytest tests/unit/services/llm/test_doubao_adapter.py -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/src/services/llm/doubao_adapter.py
git add backend/tests/unit/services/llm/test_doubao_adapter.py
git commit -m "feat: 实现豆包适配器

- 使用 volcengine-python-sdk
- 支持 chat 和 chat_stream 方法
- 豆包消息格式转换

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: 实现适配器工厂

**Files:**
- Create: `backend/src/services/llm/factory.py`

- [ ] **Step 1: 实现工厂**

创建 `backend/src/services/llm/factory.py`:

```python
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
```

- [ ] **Step 2: 测试工厂**

```bash
cd backend
python3 -c "
from src.services.llm.factory import create_adapter, ADAPTER_REGISTRY, get_supported_providers

print('支持的供应商:', get_supported_providers())
print('供应商数量:', len(get_supported_providers()))

# 测试创建适配器
adapter = create_adapter('openai', api_key='sk-test', base_url='https://api.openai.com/v1')
print('OpenAI 适配器类型:', type(adapter).__name__)
"
```

预期：输出所有支持的供应商

- [ ] **Step 3: 提交**

```bash
git add backend/src/services/llm/factory.py
git commit -m "feat: 实现 LLM 适配器工厂

- 供应商代码到适配器类的映射
- create_adapter 工厂函数
- get_supported_providers 辅助函数

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: 更新数据库模型支持额外配置

**Files:**
- Modify: `backend/src/db_models.py`

- [ ] **Step 1: 检查现有模型**

确认 `ModelProviderModel` 是否有 `extra_config` 字段或类似字段用于存储额外配置：

```bash
cd backend
python3 -c "
from src.db_models import ModelProviderModel
import inspect
columns = [c.name for c in ModelProviderModel.__table__.columns]
print('ModelProviderModel 字段:', columns)
"
```

如果没有额外配置字段，需要添加。

- [ ] **Step 2: 添加额外配置字段（如需要）**

如果需要，在 `ModelProviderModel` 中添加：

```python
# 在 ModelProviderModel 类中添加
extra_config = Column(Text, nullable=True, comment="额外配置 JSON")
```

- [ ] **Step 3: 创建迁移**

```bash
cd backend
alembic revision --autogenerate -m "add_extra_config_to_model_provider"
alembic upgrade head
```

- [ ] **Step 4: 提交**

```bash
git add backend/src/db_models.py backend/alembic/versions/
git commit -m "feat: 添加 model_providers extra_config 字段

支持存储供应商特定配置（如 AWS Secret Key、Region 等）

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: 重构 AIService 使用适配器

**Files:**
- Modify: `backend/src/services/ai_service.py`

- [ ] **Step 1: 备份现有文件**

```bash
cp backend/src/services/ai_service.py backend/src/services/ai_service.py.backup
```

- [ ] **Step 2: 重构 AIService**

修改 `backend/src/services/ai_service.py`：

```python
"""AI 服务：调用 LLM API（使用适配器模式）"""
import os
import logging
import asyncio
import httpx
import json
import base64
import uuid
from pathlib import Path
from typing import Optional, Tuple, List, Dict, AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


class AIService:
    """AI 服务客户端（使用适配器模式）"""

    def __init__(self, db: Optional[Session] = None):
        """
        初始化 AI 服务

        Args:
            db: 数据库会话（必需，用于读取配置）
        """
        self.db = db
        if not self.db:
            raise ValueError("数据库会话是必需的")

        self.default_adapter, self.default_model = self._get_adapter()

    def _get_adapter(self, model_config: Optional[str] = None) -> Tuple:
        """
        获取适配器和模型名称

        Args:
            model_config: 模型配置字符串，格式：provider:model_name

        Returns:
            (adapter, model_name) 元组
        """
        from src.services.model_provider_service import ModelProviderService
        from src.services.encryption_service import EncryptionService
        from src.db_models import ModelProviderModel
        from .llm.factory import create_adapter

        provider_service = ModelProviderService(self.db)
        encryption = EncryptionService()

        # 解析 model_config
        provider_code = None
        model_code = None

        if model_config and ":" in model_config:
            provider_code, model_code = model_config.split(":", 1)
            provider_code = provider_code.lower()
            logger.info(f"使用工具指定的模型配置: {provider_code}:{model_code}")
        else:
            # 使用默认供应商
            provider_info = provider_service.get_default_provider()
            if provider_info:
                provider_code = provider_info.provider_code

                # 获取默认模型
                models = provider_service.get_all_models(
                    provider_id=provider_info.id,
                    include_disabled=False
                )
                if models:
                    model_code = models[0].model_code
                else:
                    model_code = "default"
            else:
                raise ValueError("未配置默认供应商")

        # 从数据库获取供应商配置
        provider_info = provider_service.get_provider_by_code(provider_code)
        if not provider_info:
            raise ValueError(f"供应商 '{provider_code}' 未配置")

        provider_model = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.id == provider_info.id
        ).first()

        if not provider_model:
            raise ValueError(f"供应商 '{provider_code}' 配置不完整")

        # 解密 API Key
        api_key = encryption.decrypt(provider_model.api_key_encrypted)

        # 解析额外配置
        extra_config = {}
        if hasattr(provider_model, 'extra_config') and provider_model.extra_config:
            try:
                import json
                extra_config = json.loads(provider_model.extra_config)
            except json.JSONDecodeError:
                logger.warning(f"额外配置解析失败: {provider_model.extra_config}")

        # 创建适配器
        adapter = create_adapter(
            provider_code=provider_code,
            api_key=api_key,
            base_url=provider_info.base_url,
            **extra_config
        )

        return adapter, model_code

    async def generate_welcome_message(self, system_prompt: str, model_config: Optional[str] = None) -> str:
        """生成欢迎消息"""
        adapter, model = self._get_adapter(model_config)

        try:
            content, _ = await adapter.chat(
                messages=[{"role": "user", "content": "请用一句话介绍你自己，并询问用户需要什么帮助。"}],
                model=model,
                system_prompt=system_prompt
            )
            return content
        except Exception as e:
            logger.error(f"生成欢迎消息失败: {e}")
            return "你好！我是你的 AI 助手。请告诉我你需要什么帮助。"

    async def chat(self, system_prompt: str, history: List[Dict[str, str]],
                   user_message: str, model_config: Optional[str] = None) -> tuple:
        """非流式对话"""
        adapter, model = self._get_adapter(model_config)

        messages = history + [{"role": "user", "content": user_message}]

        return await adapter.chat(messages, model, system_prompt)

    async def chat_stream(self, system_prompt: str, history: List[Dict[str, str]],
                         user_message: str, model_config: Optional[str] = None) -> AsyncGenerator:
        """流式对话"""
        adapter, model = self._get_adapter(model_config)

        messages = history + [{"role": "user", "content": user_message}]

        async for chunk in adapter.chat_stream(messages, model, system_prompt):
            yield chunk
```

- [ ] **Step 3: 运行测试验证**

```bash
cd backend
pytest tests/unit/services/test_ai_service.py -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/src/services/ai_service.py
git commit -m "refactor: 重构 AIService 使用适配器模式

- 移除环境变量回退逻辑
- 使用工厂模式获取适配器
- 统一数据库配置
- 简化流式/非流式接口

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: 更新内置模型定义

**Files:**
- Modify: `backend/src/services/builtin_models.py`

- [ ] **Step 1: 更新模型定义**

确保 `builtin_models.py` 包含所有 7 家供应商的最新模型（已在之前完成）。

- [ ] **Step 2: 提交**

```bash
git add backend/src/services/builtin_models.py
git commit -m "feat: 更新内置模型定义到 2026年3月

支持 7 家供应商共 67 个模型：
- OpenAI: GPT-5.4 系列
- DeepSeek: V3.2 系列
- Kimi: K2.5 系列
- GLM: GLM-5 系列
- 豆包: Seed 2.0 系列
- Claude: Opus 4.6 系列 (AWS Bedrock)
- Google: Gemini 3.1 系列

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 11: 更新前端 API 密钥链接

**Files:**
- Modify: `frontend/src/views/admin/AdminModelProvidersPage.vue`

- [ ] **Step 1: 更新 API 密钥 URL 映射**

在 `getApiKeyUrl` 函数中添加新供应商：

```typescript
const getApiKeyUrl = (providerCode: string): string => {
  const urlMap: Record<string, string> = {
    'deepseek': 'https://platform.deepseek.com/api_keys',
    'kimi': 'https://platform.moonshot.cn/console/api-keys',
    'moonshot': 'https://platform.moonshot.cn/console/api-keys',
    'openai': 'https://platform.openai.com/api-keys',
    'zhipu': 'https://open.bigmodel.cn/usercenter/apikeys',
    'glm': 'https://open.bigmodel.cn/usercenter/apikeys',
    'doubao': 'https://console.volcengine.com/ark',
    'bytedance': 'https://console.volcengine.com/ark',
    'claude': 'https://console.anthropic.com/settings/keys',
    'anthropic': 'https://console.anthropic.com/settings/keys',
    'google': 'https://aistudio.google.com/app/apikey',
    'gemini': 'https://aistudio.google.com/app/apikey'
  }
  return urlMap[providerCode] || ''
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/admin/AdminModelProvidersPage.vue
git commit -m "feat: 更新管理后台 API 密钥获取链接

添加新供应商：
- 豆包: console.volcengine.com/ark
- Claude: console.anthropic.com/settings/keys
- Google: aistudio.google.com/app/apikey

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 12: 集成测试

**Files:**
- Create: `backend/tests/integration/test_llm_adapters.py`

- [ ] **Step 1: 编写集成测试**

创建 `backend/tests/integration/test_llm_adapters.py`:

```python
"""LLM 适配器集成测试"""
import pytest
from src.services.llm.factory import create_adapter, get_supported_providers


class TestLLMAdaptersIntegration:
    """测试 LLM 适配器集成"""

    def test_all_adapters_can_be_created(self):
        """测试所有适配器都可以被创建"""
        providers = get_supported_providers()

        for provider in providers:
            # 测试工厂能创建适配器
            # 注意：这里使用测试密钥，不实际调用 API
            adapter = create_adapter(
                provider,
                api_key="test-key-for-creation",
                base_url="https://test.example.com"
            )
            assert adapter is not None
            print(f"✓ {provider} adapter created")

    def test_unsupported_provider_raises_error(self):
        """测试不支持的供应商抛出错误"""
        with pytest.raises(ValueError, match="不支持的供应商"):
            create_adapter("unsupported_provider", api_key="test")
```

- [ ] **Step 2: 运行集成测试**

```bash
cd backend
pytest tests/integration/test_llm_adapters.py -v
```

- [ ] **Step 3: 提交**

```bash
git add backend/tests/integration/test_llm_adapters.py
git commit -m "test: 添加 LLM 适配器集成测试

- 测试所有适配器创建
- 测试不支持供应商错误处理

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 13: 文档更新

**Files:**
- Modify: `backend/README.md` (或创建)
- Modify: `CLAUDE.md`

- [ ] **Step 1: 更新项目文档**

在 `CLAUDE.md` 中添加供应商接入说明：

```markdown
## LLM 供应商配置

系统使用适配器模式支持多个 LLM 供应商，所有配置存储在数据库中。

### 支持的供应商

| 供应商 | 代码 | API 类型 | 获取密钥 |
|--------|------|----------|----------|
| OpenAI | openai | OpenAI 兼容 | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| DeepSeek | deepseek | OpenAI 兼容 | [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys) |
| Kimi | kimi | OpenAI 兼容 | [platform.moonshot.cn/console/api-keys](https://platform.moonshot.cn/console/api-keys) |
| GLM | glm | OpenAI 兼容 | [open.bigmodel.cn/usercenter/apikeys](https://open.bigmodel.cn/usercenter/apikeys) |
| 豆包 | doubao | VolcEngine | [console.volcengine.com/ark](https://console.volcengine.com/ark) |
| Claude | claude | AWS Bedrock | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) |
| Google | google | Gemini API | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |

### 配置方式

1. 登录管理后台 `/admin`
2. 进入「模型供应商配置」
3. 创建或编辑供应商：
   - 填写 API 密钥（会加密存储）
   - 配置 API 地址
   - 添加模型配置
```

- [ ] **Step 2: 提交**

```bash
git add CLAUDE.md
git commit -m "docs: 更新 LLM 供应商配置说明

- 添加支持的供应商列表
- 添加 API 密钥获取链接
- 添加配置方式说明

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## 验收标准

完成后，以下标准应该满足：

- [ ] 所有 7 家供应商的适配器已实现
- [ ] 所有适配器支持流式输出
- [ ] 所有配置从数据库读取，无环境变量依赖
- [ ] 单元测试覆盖所有适配器
- [ ] 集成测试通过
- [ ] 文档已更新
- [ ] 代码已提交并推送

---

## 风险与注意事项

1. **豆包 SDK 包名**: `volcengine` 或 `volcengine-python-sdk`，需要验证正确包名
2. **Bedrock 凭证**: 需要同时存储 Access Key 和 Secret Key
3. **Gemini 消息格式**: 使用 `contents` 而非 `messages`
4. **流式输出一致性**: 确保所有供应商的流式输出格式统一
