# NewAPI Provider 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-step. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标:** 添加 NewAPI 作为新的模型供应商，支持通过管理后台动态管理模型

**架构:** NewAPIProvider 继承 AIProvider 抽象基类，使用 OpenAI SDK（兼容 OpenAI API 规范），注册到 ProviderFactory

**技术栈:** Python 3.10+, AsyncOpenAI SDK, SQLAlchemy, pytest

---

## 文件结构

```
backend/src/infrastructure/providers/
├── base.py              # AIProvider 抽象基类（不修改）
├── openai_provider.py   # OpenAI 实现（参考，不修改）
├── newapi_provider.py   # NewAPI 实现（新建）
└── factory.py           # Provider 工厂（修改：注册 newapi）

backend/tests/unit/
└── test_newapi_provider.py  # NewAPI 单元测试（新建）
```

---

## Task 1: 创建 NewAPIProvider 类

**文件:**
- Create: `backend/src/infrastructure/providers/newapi_provider.py`

- [ ] **Step 1: 创建文件并编写基本结构**

创建文件 `backend/src/infrastructure/providers/newapi_provider.py`:

```python
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
```

- [ ] **Step 2: 验证文件创建成功**

运行: `ls -la backend/src/infrastructure/providers/newapi_provider.py`
预期: 文件存在

- [ ] **Step 3: 提交**

```bash
git add backend/src/infrastructure/providers/newapi_provider.py
git commit -m "feat: 添加 NewAPIProvider 类"
```

---

## Task 2: 注册 NewAPIProvider 到工厂

**文件:**
- Modify: `backend/src/infrastructure/providers/factory.py`

- [ ] **Step 1: 添加 import**

在文件顶部添加导入:

```python
from src.infrastructure.providers.newapi_provider import NewAPIProvider
```

- [ ] **Step 2: 注册到 _providers 字典**

在 `_providers` 字典中添加 `"newapi": NewAPIProvider`:

```python
_providers: Dict[str, Type[AIProvider]] = {
    "openai": OpenAIProvider,
    "deepseek": DeepSeekProvider,
    "kimi": KimiProvider,
    "newapi": NewAPIProvider,  # 新增
}
```

- [ ] **Step 3: 验证 Python 语法正确**

运行: `python -m py_compile backend/src/infrastructure/providers/factory.py`
预期: 无错误

- [ ] **Step 4: 提交**

```bash
git add backend/src/infrastructure/providers/factory.py
git commit -m "feat: 注册 NewAPIProvider 到 ProviderFactory"
```

---

## Task 3: 编写单元测试 - 初始化

**文件:**
- Create: `backend/tests/unit/test_newapi_provider.py`

- [ ] **Step 1: 创建测试文件并编写初始化测试**

创建文件 `backend/tests/unit/test_newapi_provider.py`:

```python
"""
NewAPIProvider 单元测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.infrastructure.providers.newapi_provider import NewAPIProvider
from src.domain.entities.message import Message
from src.domain.value_objects.message_role import MessageRole
from datetime import datetime


class TestNewAPIProviderInit:
    """测试 NewAPIProvider 初始化"""

    @patch("src.infrastructure.providers.newapi_provider.AsyncOpenAI")
    def test_init_with_base_url(self, mock_openai):
        """测试使用 base_url 初始化"""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        provider = NewAPIProvider(
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

        assert provider._api_key == "test-key"
        assert provider._base_url == "https://newapi.example.com/v1"
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

    @patch("src.infrastructure.providers.newapi_provider.AsyncOpenAI")
    def test_init_creates_client(self, mock_openai):
        """测试初始化时创建 OpenAI 客户端"""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        provider = NewAPIProvider(
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

        assert provider._client == mock_client

    @patch("src.infrastructure.providers.newapi_provider.AsyncOpenAI")
    def test_get_supported_models_returns_empty_list(self, mock_openai):
        """测试 get_supported_models 返回空列表（模型由数据库管理）"""
        mock_openai.return_value = Mock()

        provider = NewAPIProvider(
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

        assert provider.get_supported_models() == []
```

- [ ] **Step 2: 运行测试验证通过**

运行: `cd backend && pytest tests/unit/test_newapi_provider.py::TestNewAPIProviderInit -v`
预期: PASS (3 passed)

- [ ] **Step 3: 提交**

```bash
git add backend/tests/unit/test_newapi_provider.py
git commit -m "test: 添加 NewAPIProvider 初始化测试"
```

---

## Task 4: 编写单元测试 - 消息转换

**文件:**
- Modify: `backend/tests/unit/test_newapi_provider.py`

- [ ] **Step 1: 添加消息转换测试**

在测试文件中添加新的测试类:

```python
class TestNewAPIProviderMessageConversion:
    """测试消息格式转换"""

    def setup_method(self):
        """每个测试前创建 provider 实例"""
        with patch("src.infrastructure.providers.newapi_provider.AsyncOpenAI"):
            self.provider = NewAPIProvider(
                api_key="test-key",
                base_url="https://newapi.example.com/v1"
            )

    def test_convert_user_message(self):
        """测试转换用户消息"""
        message = Message(
            id="1",
            session_id="session-1",
            role=MessageRole.USER,
            content="Hello, AI!",
            artifact=None,
            created_at=datetime.now()
        )

        result = self.provider._convert_messages([message])

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello, AI!"

    def test_convert_assistant_message(self):
        """测试转换助手消息"""
        message = Message(
            id="2",
            session_id="session-1",
            role=MessageRole.ASSISTANT,
            content="Hello, human!",
            artifact=None,
            created_at=datetime.now()
        )

        result = self.provider._convert_messages([message])

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "Hello, human!"

    def test_convert_system_message(self):
        """测试转换系统消息"""
        message = Message(
            id="3",
            session_id="session-1",
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant.",
            artifact=None,
            created_at=datetime.now()
        )

        result = self.provider._convert_messages([message])

        assert len(result) == 1
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are a helpful assistant."

    def test_convert_multiple_messages(self):
        """测试转换多条消息"""
        messages = [
            Message(
                id="1",
                session_id="session-1",
                role=MessageRole.SYSTEM,
                content="You are helpful.",
                artifact=None,
                created_at=datetime.now()
            ),
            Message(
                id="2",
                session_id="session-1",
                role=MessageRole.USER,
                content="Hello!",
                artifact=None,
                created_at=datetime.now()
            ),
            Message(
                id="3",
                session_id="session-1",
                role=MessageRole.ASSISTANT,
                content="Hi there!",
                artifact=None,
                created_at=datetime.now()
            ),
        ]

        result = self.provider._convert_messages(messages)

        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[2]["role"] == "assistant"

    def test_convert_role_user(self):
        """测试 role 转换 - user"""
        assert self.provider._convert_role(MessageRole.USER) == "user"

    def test_convert_role_assistant(self):
        """测试 role 转换 - assistant"""
        assert self.provider._convert_role(MessageRole.ASSISTANT) == "assistant"

    def test_convert_role_system(self):
        """测试 role 转换 - system"""
        assert self.provider._convert_role(MessageRole.SYSTEM) == "system"
```

- [ ] **Step 2: 运行测试验证通过**

运行: `cd backend && pytest tests/unit/test_newapi_provider.py::TestNewAPIProviderMessageConversion -v`
预期: PASS (7 passed)

- [ ] **Step 3: 提交**

```bash
git add backend/tests/unit/test_newapi_provider.py
git commit -m "test: 添加消息转换测试"
```

---

## Task 5: 编写单元测试 - ProviderFactory 注册

**文件:**
- Modify: `backend/tests/unit/test_newapi_provider.py`

- [ ] **Step 1: 添加工厂注册测试**

在测试文件中添加新的测试类:

```python
class TestProviderFactoryRegistration:
    """测试 ProviderFactory 注册"""

    def test_newapi_is_registered(self):
        """测试 newapi 已注册到 ProviderFactory"""
        from src.infrastructure.providers.factory import ProviderFactory

        assert "newapi" in ProviderFactory.get_registered_providers()

    def test_is_provider_registered_returns_true(self):
        """测试 is_provider_registered 对 newapi 返回 True"""
        from src.infrastructure.providers.factory import ProviderFactory

        assert ProviderFactory.is_provider_registered("newapi") is True
        assert ProviderFactory.is_provider_registered("newapi") is True  # 大小写不敏感

    def test_create_newapi_provider(self):
        """测试通过工厂创建 NewAPIProvider"""
        from src.infrastructure.providers.factory import ProviderFactory

        provider = ProviderFactory.create(
            provider_name="newapi",
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

        assert isinstance(provider, NewAPIProvider)
        assert provider._api_key == "test-key"
        assert provider._base_url == "https://newapi.example.com/v1"

    def test_create_newapi_provider_case_insensitive(self):
        """测试创建 provider 时名称大小写不敏感"""
        from src.infrastructure.providers.factory import ProviderFactory

        provider1 = ProviderFactory.create(
            provider_name="newapi",
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )
        provider2 = ProviderFactory.create(
            provider_name="NewAPI",
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )
        provider3 = ProviderFactory.create(
            provider_name="NEWAPI",
            api_key="test-key",
            base_url="https://newapi.example.com/v1"
        )

        assert isinstance(provider1, NewAPIProvider)
        assert isinstance(provider2, NewAPIProvider)
        assert isinstance(provider3, NewAPIProvider)
```

- [ ] **Step 2: 运行测试验证通过**

运行: `cd backend && pytest tests/unit/test_newapi_provider.py::TestProviderFactoryRegistration -v`
预期: PASS (4 passed)

- [ ] **Step 3: 提交**

```bash
git add backend/tests/unit/test_newapi_provider.py
git commit -m "test: 添加工厂注册测试"
```

---

## Task 6: 运行所有单元测试

- [ ] **Step 1: 运行完整的 NewAPIProvider 测试套件**

运行: `cd backend && pytest tests/unit/test_newapi_provider.py -v`
预期: PASS (14 passed)

- [ ] **Step 2: 运行所有单元测试确保没有破坏现有功能**

运行: `cd backend && pytest tests/unit/ -v`
预期: PASS (所有测试通过)

---

## Task 7: 验证实现

- [ ] **Step 1: 检查代码覆盖率**

运行: `cd backend && pytest tests/unit/test_newapi_provider.py --cov=src/infrastructure/providers/newapi_provider --cov-report=term-missing`
预期: 覆盖率 > 80%

- [ ] **Step 2: 验证所有文件已提交**

运行: `git status`
预期: 没有 uncommitted changes

- [ ] **Step 3: 查看提交历史**

运行: `git log --oneline -5`
预期: 看到新提交

---

## 验收标准

1. ✅ `NewAPIProvider` 类创建成功，继承 `AIProvider`
2. ✅ `NewAPIProvider` 注册到 `ProviderFactory`
3. ✅ 所有单元测试通过（至少 14 个测试）
4. ✅ 代码覆盖率 > 80%
5. ✅ 没有破坏现有的单元测试

---

## 使用说明（管理员配置）

实现完成后，管理员需要在管理后台配置 NewAPI：

1. 访问 `/admin/model-providers`
2. 点击"新增供应商"
3. 填写：
   - 代码: `newapi`
   - 名称: `NewAPI`
   - API 地址: `https://your-domain.com/v1`
   - API 密钥: `your-api-key`
4. 保存

然后添加模型：
1. 访问 `/admin/model-configs`
2. 点击"新增模型"
3. 填写：
   - 供应商: 选择 NewAPI
   - 模型代码: `gpt-4o`
   - 模型名称: `GPT-4o`
   - 能力: `chat,vision`
4. 保存

用户即可在聊天界面选择 `newapi:gpt-4o` 模型进行对话。
