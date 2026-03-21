# Kimi (Moonshot AI) 接入实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标:** 将 Kimi (Moonshot AI) 接入 AI 智能备课平台，同时建立统一的文件上传服务架构

**架构:**
1. 创建 `KimiProvider` 实现 AIProvider 接口
2. 创建 `FileParserService` 提取文件文本内容
3. 扩展 `AIProvider` 基类添加文件相关方法
4. 创建文件上传 API 路由，根据供应商选择策略
5. 注册 Kimi 到 ProviderFactory

**技术栈:**
- FastAPI (后端)
- Vue 3 + TypeScript (前端)
- PyPDF2, python-docx, openpyxl, python-pptx (文件解析)
- httpx (异步 HTTP)
- OpenAI SDK (Kimi 兼容 OpenAI 协议)

---

## 文件结构

### 新建文件

| 文件 | 职责 |
|------|------|
| `backend/src/infrastructure/providers/kimi_provider.py` | Kimi API 实现 |
| `backend/src/services/file_parser_service.py` | 文件解析服务 |
| `backend/src/interfaces/routers/tools/files.py` | 文件上传 API |
| `backend/src/scripts/init_kimi_provider.py` | Kimi 初始化脚本 |
| `frontend/src/components/ChatFileUpload.vue` | 文件上传组件 |
| `backend/tests/unit/test_file_parser_service.py` | 文件解析测试 |
| `backend/tests/integration/test_kimi_provider.py` | Kimi 集成测试 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `backend/src/infrastructure/providers/base.py` | 添加 upload_file, chat_with_file 方法 |
| `backend/src/infrastructure/providers/factory.py` | 注册 KimiProvider |
| `backend/requirements.txt` | 添加新依赖 |
| `backend/src/main.py` | 注册文件上传路由 |
| `frontend/src/services/apiClient.ts` | 添加文件上传 API 调用 |

---

## Task 1: 扩展 AIProvider 基类

**Files:**
- Modify: `backend/src/infrastructure/providers/base.py`

- [ ] **Step 1: 添加文件相关方法到 AIProvider**

```python
# 在 AIProvider 类中添加以下方法

    async def upload_file(
        self,
        file_path: str,
        filename: str
    ) -> Optional[str]:
        """
        上传文件到 AI 服务（默认实现）

        不支持文件的 Provider 可覆盖此方法并记录日志

        Args:
            file_path: 本地文件路径
            filename: 文件名

        Returns:
            str: 文件ID，不支持时返回 None
        """
        logger.warning(f"{self.__class__.__name__} does not support file upload")
        return None

    async def chat_with_file(
        self,
        messages: List[Message],
        file_ids: List[str],
        model: str,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        带文件的流式对话（默认实现）

        不支持文件的 Provider 可覆盖此方法并记录日志

        Args:
            messages: 消息列表
            file_ids: 文件ID列表
            model: 模型名称
            temperature: 温度参数
            **kwargs: 其他参数

        Yields:
            str: 流式返回的文本片段，不支持时 yield 空字符串
        """
        logger.warning(f"{self.__class__.__name__} does not support file chat")
        yield ""
```

- [ ] **Step 2: 运行现有测试确保没有破坏**

```bash
cd backend && python -m pytest tests/unit/ tests/integration/ -v
```

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add backend/src/infrastructure/providers/base.py
git commit -m "feat(ai-provider): 添加文件上传和带文件对话的默认方法"
```

---

## Task 2: 创建 FileParserService

**Files:**
- Create: `backend/src/services/file_parser_service.py`
- Create: `backend/tests/unit/test_file_parser_service.py`

- [ ] **Step 1: 编写 FileParserService 测试**

```python
# backend/tests/unit/test_file_parser_service.py
import pytest
import tempfile
import os
from src.services.file_parser_service import FileParserService

@pytest.fixture
def parser():
    return FileParserService()

@pytest.fixture
def temp_txt_file():
    """创建临时文本文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("测试内容\n这是第二行")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.mark.asyncio
async def test_parse_txt_file(parser, temp_txt_file):
    """测试解析文本文件"""
    result = await parser.parse_file(temp_txt_file, "test.txt")
    assert "测试内容" in result
    assert "这是第二行" in result

@pytest.mark.asyncio
async def test_unsupported_format(parser):
    """测试不支持的格式"""
    with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
        f.write(b"content")
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Unsupported file format"):
            await parser.parse_file(temp_path, "test.xyz")
    finally:
        os.unlink(temp_path)

@pytest.mark.asyncio
async def test_supported_formats(parser):
    """测试支持的格式列表"""
    formats = parser.SUPPORTED_FORMATS
    assert '.txt' in formats
    assert '.pdf' in formats
    assert '.docx' in formats
    assert '.xlsx' in formats
    assert '.pptx' in formats
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/unit/test_file_parser_service.py -v
```

Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 创建 FileParserService**

```python
# backend/src/services/file_parser_service.py
# -*- coding: utf-8 -*-
"""文件解析服务

提供各种文件格式的文本提取功能
"""
import logging
import os
from typing import Set
from pathlib import Path

logger = logging.getLogger(__name__)


class FileParserService:
    """文件解析服务 - 提取文件文本内容"""

    SUPPORTED_FORMATS: Set[str] = {
        '.txt', '.md', '.json',      # 纯文本
        '.pdf',                       # PDF
        '.doc', '.docx',             # Word
        '.xls', '.xlsx',             # Excel
        '.ppt', '.pptx',             # PPT
    }

    async def parse_file(self, file_path: str, filename: str) -> str:
        """
        解析文件，提取文本内容

        Args:
            file_path: 文件路径
            filename: 文件名

        Returns:
            str: 提取的文本内容

        Raises:
            ValueError: 不支持的文件格式
        """
        ext = Path(filename).suffix.lower()

        if ext in {'.txt', '.md', '.json'}:
            return await self._parse_text(file_path)
        elif ext == '.pdf':
            return await self._parse_pdf(file_path)
        elif ext in {'.doc', '.docx'}:
            return await self._parse_word(file_path)
        elif ext in {'.xls', '.xlsx'}:
            return await self._parse_excel(file_path)
        elif ext in {'.ppt', '.pptx'}:
            return await self._parse_ppt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    async def _parse_text(self, file_path: str) -> str:
        """解析纯文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='gb18030') as f:
                return f.read()

    async def _parse_pdf(self, file_path: str) -> str:
        """解析 PDF 文件"""
        try:
            import PyPDF2
        except ImportError:
            logger.error("PyPDF2 未安装，请运行: pip install PyPDF2")
            return "[PDF 解析失败: PyPDF2 未安装]"

        try:
            text_parts = []
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return '\n'.join(text_parts)
        except Exception as e:
            logger.error(f"PDF 解析失败: {e}")
            return f"[PDF 解析失败: {str(e)}]"

    async def _parse_word(self, file_path: str) -> str:
        """解析 Word 文件"""
        try:
            from docx import Document
        except ImportError:
            logger.error("python-docx 未安装，请运行: pip install python-docx")
            return "[Word 解析失败: python-docx 未安装]"

        try:
            doc = Document(file_path)
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text_parts.append(paragraph.text)
            return '\n'.join(text_parts)
        except Exception as e:
            logger.error(f"Word 解析失败: {e}")
            return f"[Word 解析失败: {str(e)}]"

    async def _parse_excel(self, file_path: str) -> str:
        """解析 Excel 文件"""
        try:
            import openpyxl
        except ImportError:
            logger.error("openpyxl 未安装，请运行: pip install openpyxl")
            return "[Excel 解析失败: openpyxl 未安装]"

        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
            text_parts = []
            for sheet in wb.worksheets:
                text_parts.append(f"### 工作表: {sheet.title} ###")
                for row in sheet.iter_rows(values_only=True):
                    row_text = '\t'.join(str(cell) if cell is not None else '' for cell in row)
                    if row_text.strip():
                        text_parts.append(row_text)
            return '\n'.join(text_parts)
        except Exception as e:
            logger.error(f"Excel 解析失败: {e}")
            return f"[Excel 解析失败: {str(e)}]"

    async def _parse_ppt(self, file_path: str) -> str:
        """解析 PPT 文件"""
        try:
            from pptx import Presentation
        except ImportError:
            logger.error("python-pptx 未安装，请运行: pip install python-pptx")
            return "[PPT 解析失败: python-pptx 未安装]"

        try:
            prs = Presentation(file_path)
            text_parts = []
            for i, slide in enumerate(prs.slides):
                text_parts.append(f"### 幻灯片 {i + 1} ###")
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        text_parts.append(shape.text)
            return '\n'.join(text_parts)
        except Exception as e:
            logger.error(f"PPT 解析失败: {e}")
            return f"[PPT 解析失败: {str(e)}]"
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/unit/test_file_parser_service.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/services/file_parser_service.py backend/tests/unit/test_file_parser_service.py
git commit -m "feat(file-parser): 添加文件解析服务"
```

---

## Task 3: 创建 KimiProvider

**Files:**
- Create: `backend/src/infrastructure/providers/kimi_provider.py`
- Create: `backend/tests/integration/test_kimi_provider.py`

- [ ] **Step 1: 编写 KimiProvider 测试**

```python
# backend/tests/integration/test_kimi_provider.py
import pytest
from src.infrastructure.providers.kimi_provider import KimiProvider

@pytest.fixture
def kimi_provider():
    """创建 Kimi Provider 测试实例"""
    return KimiProvider(api_key="test_key")

def test_supported_models(kimi_provider):
    """测试支持的模型列表"""
    models = kimi_provider.get_supported_models()
    assert "moonshot-v1-8k" in models
    assert "moonshot-v1-32k" in models
    assert "moonshot-v1-128k" in models

def test_validate_model(kimi_provider):
    """测试模型验证"""
    assert kimi_provider.validate_model("moonshot-v1-8k") is True
    assert kimi_provider.validate_model("unknown-model") is False

def test_provider_initialization(kimi_provider):
    """测试 Provider 初始化"""
    assert kimi_provider._base_url == "https://api.moonshot.cn"
    assert kimi_provider._api_key == "test_key"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/integration/test_kimi_provider.py -v
```

Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 创建 KimiProvider**

```python
# backend/src/infrastructure/providers/kimi_provider.py
# -*- coding: utf-8 -*-
"""
Kimi (Moonshot AI) Provider实现

提供 Kimi API 的实现，Kimi 兼容 OpenAI 协议
支持对话、文件上传、多模态能力
"""
import logging
from typing import List, AsyncGenerator, Optional

import httpx
from openai import AsyncOpenAI

from src.infrastructure.providers.base import AIProvider
from src.domain.entities.message import Message
from src.domain.value_objects.message_role import MessageRole

logger = logging.getLogger(__name__)


class KimiProvider(AIProvider):
    """
    Kimi (Moonshot AI) API 提供商实现

    支持能力：
    - 流式/非流式对话
    - 文件上传和文档问答
    - 多模态图片识别

    支持的模型：
    - moonshot-v1-8k
    - moonshot-v1-32k
    - moonshot-v1-128k
    """

    def __init__(self, api_key: str, base_url: str = "https://api.moonshot.cn"):
        """
        初始化 Kimi Provider

        Args:
            api_key: Kimi API 密钥
            base_url: API 基础 URL（默认为 Kimi 官方 API 地址）
        """
        self._api_key = api_key
        self._base_url = base_url
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self._http_client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        logger.info(f"Kimi Provider initialized with base_url: {base_url}")

    def get_supported_models(self) -> List[str]:
        """
        获取支持的模型列表

        Returns:
            List[str]: Kimi 模型列表
        """
        return ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]

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
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Yields:
            str: 流式返回的文本片段
        """
        try:
            # 转换消息格式
            kimi_messages = self._convert_messages(messages)

            # 调用 Kimi API (stream=True 返回 async generator)
            stream = self._client.chat.completions.create(
                model=model,
                messages=kimi_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            # 流式返回内容
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Kimi stream chat error: {e}")
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
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Returns:
            str: 完整的 AI 响应文本
        """
        try:
            # 转换消息格式
            kimi_messages = self._convert_messages(messages)

            # 调用 Kimi API
            response = await self._client.chat.completions.create(
                model=model,
                messages=kimi_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                **kwargs
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Kimi chat error: {e}")
            raise

    async def upload_file(
        self,
        file_path: str,
        filename: str
    ) -> Optional[str]:
        """
        上传文件到 Kimi 服务器

        Args:
            file_path: 本地文件路径
            filename: 文件名

        Returns:
            str: file_id，用于后续对话引用
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/octet-stream')}
                response = await self._http_client.post('/v1/files', files=files)

            response.raise_for_status()
            result = response.json()
            file_id = result.get('id')
            logger.info(f"Kimi file uploaded: {filename} -> {file_id}")
            return file_id

        except Exception as e:
            logger.error(f"Kimi file upload error: {e}")
            return None

    async def chat_with_file(
        self,
        messages: List[Message],
        file_ids: List[str],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        带文件的流式对话

        Args:
            messages: 消息列表
            file_ids: 通过 upload_file 获取的文件 ID 列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Yields:
            str: 流式返回的文本片段
        """
        try:
            kimi_messages = self._convert_messages(messages)

            # Kimi 文件引用格式 - 在第一条消息中添加文件引用
            if file_ids and kimi_messages:
                # 创建文件引用消息
                file_content = []
                for file_id in file_ids:
                    file_content.append({"type": "file", "file_id": file_id})

                # 将文件引用插入到第一条用户消息
                for msg in kimi_messages:
                    if msg.get("role") == "user":
                        if isinstance(msg.get("content"), str):
                            msg["content"] = [
                                {"type": "text", "text": msg["content"]},
                                *file_content
                            ]
                        break

            stream = self._client.chat.completions.create(
                model=model,
                messages=kimi_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Kimi chat with file error: {e}")
            raise

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        **kwargs
    ) -> str:
        """
        图片识别（Kimi 支持图片输入）

        实际使用时通过 chat 接口传入图片 URL 或 base64
        Kimi 不支持生成图片，只支持图片识别

        Args:
            prompt: 图片描述提示词（用于识别）
            size: 图片尺寸
            **kwargs: 其他参数

        Returns:
            str: 图片识别结果

        Raises:
            NotImplementedError: Kimi 不支持图片生成
        """
        raise NotImplementedError(
            "Kimi does not support image generation. "
            "Use chat with image_url content for image recognition."
        )

    async def generate_audio(
        self,
        text: str,
        voice: str = "alloy",
        **kwargs
    ) -> str:
        """
        生成音频

        Kimi 不支持音频生成

        Args:
            text: 要转换为音频的文本
            voice: 音色/声音
            **kwargs: 其他参数

        Returns:
            str: 音频文件 URL 或 base64 编码

        Raises:
            NotImplementedError: Kimi 不支持音频生成
        """
        raise NotImplementedError(
            "Kimi does not support audio generation."
        )

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """
        将 Message 对象列表转换为 Kimi API 格式

        Args:
            messages: Message 对象列表

        Returns:
            List[dict]: Kimi 格式的消息列表（与 OpenAI 格式相同）
        """
        kimi_messages = []

        for message in messages:
            msg_dict = {
                "role": self._convert_role(message.role),
                "content": message.content
            }
            kimi_messages.append(msg_dict)

        return kimi_messages

    def _convert_role(self, role: MessageRole) -> str:
        """
        转换消息角色

        Args:
            role: MessageRole 枚举

        Returns:
            str: Kimi 格式的角色字符串（与 OpenAI 格式相同）
        """
        if role.is_system_message():
            return "system"
        elif role.is_user_message():
            return "user"
        elif role.is_assistant_message():
            return "assistant"
        else:
            return "user"  # 默认为 user

    async def close(self):
        """关闭 HTTP 客户端"""
        await self._http_client.aclose()
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/integration/test_kimi_provider.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/infrastructure/providers/kimi_provider.py backend/tests/integration/test_kimi_provider.py
git commit -m "feat(kimi): 添加 Kimi Provider 实现"
```

---

## Task 4: 注册 Kimi 到 ProviderFactory

**Files:**
- Modify: `backend/src/infrastructure/providers/factory.py`
- Test: `backend/tests/unit/test_factory.py`

- [ ] **Step 1: 编写工厂注册测试**

```python
# 在 backend/tests/unit/test_factory.py 中添加

def test_kimi_provider_registered():
    """测试 Kimi Provider 已注册"""
    from src.infrastructure.providers.factory import ProviderFactory

    assert "kimi" in ProviderFactory.get_registered_providers()
    assert ProviderFactory.is_provider_registered("kimi") is True

def test_create_kimi_provider():
    """测试创建 Kimi Provider"""
    from src.infrastructure.providers.factory import ProviderFactory

    provider = ProviderFactory.create(
        provider_name="kimi",
        api_key="test_key"
    )

    assert provider is not None
    assert provider.__class__.__name__ == "KimiProvider"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/unit/test_factory.py::test_kimi_provider_registered -v
```

Expected: FAIL - Kimi 未注册

- [ ] **Step 3: 注册 KimiProvider**

```python
# backend/src/infrastructure/providers/factory.py
# 修改 ProviderFactory 类

from src.infrastructure.providers.base import AIProvider
from src.infrastructure.providers.openai_provider import OpenAIProvider
from src.infrastructure.providers.deepseek_provider import DeepSeekProvider
from src.infrastructure.providers.kimi_provider import KimiProvider  # 新增导入

class ProviderFactory:
    """AI Provider 工厂类"""

    # Provider 注册表：provider 名称 -> Provider 类
    _providers: Dict[str, Type[AIProvider]] = {
        "openai": OpenAIProvider,
        "deepseek": DeepSeekProvider,
        "kimi": KimiProvider,  # 新增
    }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/unit/test_factory.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/infrastructure/providers/factory.py backend/tests/unit/test_factory.py
git commit -m "feat(factory): 注册 KimiProvider"
```

---

## Task 5: 创建文件上传 API

**Files:**
- Create: `backend/src/interfaces/routers/tools/files.py`
- Create: `backend/tests/integration/test_files_api.py`
- Modify: `backend/src/main.py`

- [ ] **Step 1: 编写文件上传 API 测试**

```python
# backend/tests/integration/test_files_api.py
import pytest
import tempfile
import os
from fastapi.testclient import TestClient

@pytest.fixture
def files_client():
    """文件上传 API 测试客户端"""
    from src.main import app
    return TestClient(app)

@pytest.fixture
def auth_token(files_client):
    """获取测试认证 token"""
    response = files_client.post("/api/v1/auth/login", json={
        "username": "test_user",
        "password": "test_password"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    # 如果登录失败，使用 mock
    return "test_token"

@pytest.fixture
def test_file():
    """创建测试文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("这是测试文件内容")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_upload_file_text_extraction_mode(files_client, auth_token, test_file):
    """测试文本提取模式（DeepSeek 等）"""
    with open(test_file, 'rb') as f:
        response = files_client.post(
            "/api/v1/files/upload?provider=deepseek",
            files={"file": ("test.txt", f, "text/plain")},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["mode"] == "text_extraction"
    assert "content" in data
    assert "测试文件内容" in data["content"]
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend && python -m pytest tests/integration/test_files_api.py -v
```

Expected: FAIL - 路由不存在

- [ ] **Step 3: 创建文件上传 API**

```python
# backend/src/interfaces/routers/tools/files.py
# -*- coding: utf-8 -*-
"""
文件上传 API 路由

提供统一的文件上传接口，根据目标供应商自动选择处理策略
"""
import logging
import os
import tempfile
import uuid
from typing import Optional

from fastapi import APIRouter, UploadFile, Query, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.interfaces.dependencies import get_current_user
from src.db_models import UserModel
from src.services.file_parser_service import FileParserService
from src.infrastructure.providers.factory import ProviderFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["文件上传"])


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    provider: str = Query(..., description="目标供应商: kimi, deepseek, openai"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    统一文件上传接口

    根据目标供应商自动选择处理策略：
    - kimi/openai/claude: 上传到供应商服务器，返回 file_id
    - deepseek/glm: 本地解析文本，返回文本内容

    Args:
        file: 上传的文件
        provider: 目标供应商
        current_user: 当前用户
        db: 数据库会话

    Returns:
        {
            "success": True,
            "file_id": "...",  // API 模式
            "content": "...",  // 文本提取模式
            "provider": "kimi",
            "mode": "api" | "text_extraction"
        }
    """
    # 验证供应商
    if not ProviderFactory.is_provider_registered(provider):
        raise HTTPException(status_code=400, detail=f"不支持的供应商: {provider}")

    # 保存临时文件
    temp_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = os.path.join(tempfile.gettempdir(), temp_filename)

    try:
        # 保存上传的文件
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        file_size = len(content)
        logger.info(f"User {current_user.username} uploaded file: {file.filename} ({file_size} bytes)")

        # 根据供应商选择处理策略
        if provider in {"kimi", "openai"}:
            # API 模式 - 上传到供应商服务器
            provider_instance = ProviderFactory.create(
                provider_name=provider,
                api_key="",  # TODO: 从数据库获取
            )
            file_id = await provider_instance.upload_file(temp_path, file.filename)

            if file_id:
                return {
                    "success": True,
                    "file_id": file_id,
                    "filename": file.filename,
                    "provider": provider,
                    "mode": "api"
                }
            else:
                raise HTTPException(status_code=500, detail="文件上传失败")

        else:
            # 文本提取模式
            parser = FileParserService()
            text_content = await parser.parse_file(temp_path, file.filename)

            # 生成预览（前 500 字符）
            preview = text_content[:500] if len(text_content) > 500 else text_content

            return {
                "success": True,
                "content": text_content,
                "content_preview": preview,
                "filename": file.filename,
                "provider": provider,
                "mode": "text_extraction"
            }

    except ValueError as e:
        # 不支持的文件格式
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)
```

- [ ] **Step 4: 在 main.py 中注册路由**

```python
# backend/src/main.py
# 在路由注册部分添加

from src.interfaces.routers.tools.files import router as files_router

# 注册文件上传路由
app.include_router(files_router, prefix="/api/v1", tags=["文件上传"])
```

- [ ] **Step 5: 运行测试验证通过**

```bash
cd backend && python -m pytest tests/integration/test_files_api.py -v
```

Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add backend/src/interfaces/routers/tools/files.py backend/src/main.py backend/tests/integration/test_files_api.py
git commit -m "feat(files-api): 添加文件上传 API"
```

---

## Task 6: 添加 Python 依赖

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 添加新依赖**

```bash
# 在 backend/requirements.txt 中添加以下行

# 文件解析依赖
PyPDF2>=3.0.0          # PDF 解析
python-docx>=1.0.0     # Word 解析
openpyxl>=3.1.0        # Excel 解析
python-pptx>=0.6.0     # PPT 解析
httpx>=0.25.0          # 异步 HTTP 客户端
```

- [ ] **Step 2: 安装依赖**

```bash
cd backend && pip install PyPDF2 python-docx openpyxl python-pptx httpx
```

Expected: 安装成功

- [ ] **Step 3: 提交**

```bash
git add backend/requirements.txt
git commit -m "chore(deps): 添加文件解析依赖"
```

---

## Task 7: 创建 Kimi 初始化脚本

**Files:**
- Create: `backend/src/scripts/init_kimi_provider.py`

- [ ] **Step 1: 创建初始化脚本**

```python
# backend/src/scripts/init_kimi_provider.py
# -*- coding: utf-8 -*-
"""
Kimi 供应商初始化脚本

运行此脚本在数据库中创建 Kimi 供应商配置
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from sqlalchemy.orm import Session
from src.database import engine
from src.db_models import ModelProviderModel, ModelConfigModel
from datetime import datetime


def init_kimi_provider(db: Session):
    """初始化 Kimi 供应商配置"""

    # 检查是否已存在
    existing = db.query(ModelProviderModel).filter(
        ModelProviderModel.provider_code == "kimi"
    ).first()

    if existing:
        print("Kimi 供应商已存在，跳过创建")
        return existing.id

    # 创建供应商
    provider = ModelProviderModel(
        provider_code="kimi",
        provider_name="Moonshot AI (Kimi)",
        api_key_encrypted="",  # 用户在后台填入
        base_url="https://api.moonshot.cn",
        is_enabled=False,  # 默认禁用，用户配置后启用
        is_default=False,
        order=3,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(provider)
    db.flush()  # 获取 provider.id

    # 创建模型配置
    models = [
        {
            "model_code": "moonshot-v1-8k",
            "model_name": "Kimi 8K",
            "capabilities": "chat,file,image"
        },
        {
            "model_code": "moonshot-v1-32k",
            "model_name": "Kimi 32K",
            "capabilities": "chat,file,image"
        },
        {
            "model_code": "moonshot-v1-128k",
            "model_name": "Kimi 128K",
            "capabilities": "chat,file,image"
        },
    ]

    for model_config in models:
        model = ModelConfigModel(
            provider_id=provider.id,
            model_code=model_config["model_code"],
            model_name=model_config["model_name"],
            capabilities=model_config["capabilities"],
            is_enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(model)

    db.commit()

    print(f"Kimi 供应商创建成功: {provider.id}")
    print(f"  - 已创建 {len(models)} 个模型配置")
    print("  - 请在管理后台配置 API Key 后启用")

    return provider.id


if __name__ == "__main__":
    from src.database import SessionLocal

    db = SessionLocal()
    try:
        init_kimi_provider(db)
        print("\n初始化完成！")
    except Exception as e:
        print(f"初始化失败: {e}")
        db.rollback()
    finally:
        db.close()
```

- [ ] **Step 2: 测试运行脚本**

```bash
cd backend && python src/scripts/init_kimi_provider.py
```

Expected: 输出 "Kimi 供应商创建成功"

- [ ] **Step 3: 提交**

```bash
git add backend/src/scripts/init_kimi_provider.py
git commit -m "chore(kimi): 添加 Kimi 初始化脚本"
```

---

## Task 8: 创建前端文件上传组件

**Files:**
- Create: `frontend/src/components/ChatFileUpload.vue`

- [ ] **Step 1: 创建文件上传组件**

```vue
<!-- frontend/src/components/ChatFileUpload.vue -->
<template>
  <div class="file-upload">
    <input
      type="file"
      ref="fileInput"
      @change="handleFileSelect"
      :accept="acceptTypes"
      style="display: none"
    />
    <button
      @click="$refs.fileInput.click()"
      class="upload-btn"
      :disabled="isUploading"
      :title="uploadTitle"
    >
      <span v-if="!isUploading">📎 上传文件</span>
      <span v-else>上传中...</span>
    </button>

    <!-- 文件列表 -->
    <div v-if="uploadedFiles.length > 0" class="file-list">
      <div
        v-for="file in uploadedFiles"
        :key="file.id"
        class="file-item"
      >
        <span class="file-icon">📄</span>
        <span class="file-name">{{ file.name }}</span>
        <button
          @click="removeFile(file.id)"
          class="remove-btn"
          title="移除"
        >×</button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { apiClient } from '@/services/apiClient'
import { useSessionStore } from '@/stores/sessionStore'

interface UploadedFile {
  id: string
  name: string
  content?: string
  mode: 'api' | 'text_extraction'
}

const emit = defineEmits<{
  (e: 'files-changed', files: UploadedFile[]): void
}>()

const sessionStore = useSessionStore()
const fileInput = ref<HTMLInputElement>()
const uploadedFiles = ref<UploadedFile[]>([])
const isUploading = ref(false)
const error = ref<string>('')

// 支持的文件类型
const acceptTypes = '.txt,.md,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx'

const uploadTitle = computed(() => {
  return `支持的文件类型: ${acceptTypes}`
})

async function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  isUploading.value = true
  error.value = ''

  try {
    const formData = new FormData()
    formData.append('file', file)

    // 获取当前选择的 provider
    const provider = sessionStore.selectedModelProvider || 'deepseek'

    const response = await apiClient.post(
      `/files/upload?provider=${provider}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )

    const result = response.data

    if (result.success) {
      const newFile: UploadedFile = {
        id: result.file_id || crypto.randomUUID(),
        name: file.name,
        content: result.content,
        mode: result.mode
      }

      uploadedFiles.value.push(newFile)
      emit('files-changed', uploadedFiles.value)
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || '文件上传失败'
  } finally {
    isUploading.value = false
    // 清空 input 以便重复上传同一文件
    input.value = ''
  }
}

function removeFile(fileId: string) {
  uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== fileId)
  emit('files-changed', uploadedFiles.value)
}

function clearFiles() {
  uploadedFiles.value = []
  emit('files-changed', uploadedFiles.value)
}

// 暴露给父组件
defineExpose({
  clearFiles,
  getFiles: () => uploadedFiles.value
})
</script>

<style scoped>
.file-upload {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.upload-btn {
  padding: 8px 16px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.upload-btn:hover:not(:disabled) {
  background: #e0e0e0;
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 150px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #f9f9f9;
  border-radius: 4px;
  font-size: 13px;
}

.file-icon {
  font-size: 14px;
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  padding: 0 4px;
}

.remove-btn:hover {
  color: #f56c6c;
}

.error-message {
  color: #f56c6c;
  font-size: 12px;
}
</style>
```

- [ ] **Step 2: 更新 apiClient 添加类型支持**

```typescript
// frontend/src/services/apiClient.ts
// 添加文件上传相关的类型定义

export interface FileUploadResponse {
  success: boolean
  file_id?: string
  content?: string
  content_preview?: string
  filename: string
  provider: string
  mode: 'api' | 'text_extraction'
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/ChatFileUpload.vue frontend/src/services/apiClient.ts
git commit -m "feat(frontend): 添加文件上传组件"
```

---

## Task 9: 运行全部测试

**Files:**
- All test files

- [ ] **Step 1: 运行后端单元测试**

```bash
cd backend && python -m pytest tests/unit/ -v
```

Expected: 全部通过

- [ ] **Step 2: 运行后端集成测试**

```bash
cd backend && python -m pytest tests/integration/ -v
```

Expected: 全部通过

- [ ] **Step 3: 运行前端测试**

```bash
cd frontend && npm run test
```

Expected: 全部通过

- [ ] **Step 4: 运行 E2E 测试**

```bash
cd frontend && npm run test:e2e
```

Expected: 全部通过

---

## Task 10: 最终提交和文档

- [ ] **Step 1: 检查 git 状态**

```bash
git status
```

确保所有更改都已提交

- [ ] **Step 2: 创建最终合并提交**

```bash
git commit --allow-empty -m "$(cat <<'EOF'
feat(kimi): 完成 Kimi (Moonshot AI) 接入

- 添加 KimiProvider 实现
- 添加 FileParserService 文件解析服务
- 添加统一文件上传 API
- 添加前端文件上传组件
- 注册 Kimi 到 ProviderFactory

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: 更新 CLAUDE.md**

在 `CLAUDE.md` 中添加 Kimi 相关说明：

```markdown
### Kimi (Moonshot AI)

- API 端点: `https://api.moonshot.cn`
- 支持模型: moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k
- 特性: 文件上传、多模态、长上下文
```

---

## 验收标准

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] Kimi 供应商可通过管理后台配置
- [ ] 文件上传 API 可正常工作
- [ ] 前端文件上传组件可正常使用
- [ ] 可通过 Kimi 模型进行对话
- [ ] 文件上传后可正常对话（Kimi 模式）
- [ ] 文件内容可提取用于对话（DeepSeek 模式）

---

## 参考资料

- [Kimi API 文档](https://platform.moonshot.cn/docs/api/files)
- [设计文档](../specs/2026-03-21-kimi-integration-design.md)
- [OpenAI SDK 文档](https://github.com/openai/openai-python)
