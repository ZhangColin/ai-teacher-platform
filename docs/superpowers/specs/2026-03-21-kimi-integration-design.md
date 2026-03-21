# Kimi (Moonshot AI) 接入设计文档

**日期**: 2026-03-21
**状态**: 设计完成，待实施

## 1. 概述

本文档描述将 Kimi (Moonshot AI) 接入 AI 智能备课平台的设计方案，同时建立统一的文件上传服务架构，支持多种 AI 供应商。

## 2. 目标

- 接入 Kimi API，支持对话、文件上传、多模态能力
- 建立统一文件上传服务，支持真·文件 API 和文本提取两种模式
- 保持与现有架构的一致性（数据库驱动配置）

## 3. 架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         前端文件上传界面                              │
│                    <input type="file" />                            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   FileUploadService (后端统一接口)                   │
│  POST /api/v1/files/upload                                         │
│   - 接收文件                                                        │
│   - 根据目标 Provider 选择处理策略                                  │
│   - 返回统一格式的结果                                              │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│   FileParserService          │  │   KimiFileService            │
│   (文本提取策略)              │  │   (API 上传策略)             │
│ • PDF → text                │  │ • 上传到 /v1/files          │
│ • Word → text               │  │ • 返回 file_id              │
│ • Excel → text              │  │                            │
│ • TXT → text                │  │                            │
└──────────────────────────────┘  └──────────────────────────────┘
          │                                    │
          ▼                                    ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│  DeepSeekProvider            │  │  KimiProvider                │
│  chat(嵌入文本内容)           │  │  chat_with_file(file_ids)    │
└──────────────────────────────┘  └──────────────────────────────┘
```

### 3.2 供应商策略对比

| 供应商 | 文件 API | 支持格式 | 大小限制 | 处理策略 |
|--------|---------|---------|---------|---------|
| Kimi | ✅ `/v1/files` | PDF, Word, Excel, TXT | 100MB/文件 | API 模式 |
| OpenAI | ✅ Files API | 多种格式 | ~512MB | API 模式 |
| Claude | ✅ Files API | 多种格式 | 30MB/文件 | API 模式 |
| 通义千问 | ✅ UploadDocument | 多种格式 | 100万 Token | API 模式 |
| DeepSeek | ❌ | - | - | 文本提取 |
| 智谱 GLM | ❌ | - | - | 文本提取 |

## 4. 组件设计

### 4.1 KimiProvider

**文件**: `backend/src/infrastructure/providers/kimi_provider.py`

**职责**:
- 实现 `AIProvider` 接口
- 提供流式/非流式对话
- 提供文件上传能力（调用 Kimi `/v1/files` API）
- 提供带文件的对话能力

**支持的模型**:
- `moonshot-v1-8k`
- `moonshot-v1-32k`
- `moonshot-v1-128k`

**关键方法**:
```python
class KimiProvider(AIProvider):
    async def chat_stream(messages, model, **kwargs) -> AsyncGenerator[str, None]
    async def chat(messages, model, **kwargs) -> str
    async def upload_file(file_path: str, filename: str) -> Optional[str]
    async def chat_with_file(messages, file_ids: List[str], model, **kwargs) -> AsyncGenerator[str, None]
    def get_supported_models() -> List[str]
```

### 4.2 FileParserService

**文件**: `backend/src/services/file_parser_service.py`

**职责**:
- 解析各种文件格式，提取文本内容
- 为不支持文件 API 的 Provider 提供文本提取能力

**支持格式**:
- 纯文本: `.txt`, `.md`, `.json`
- PDF: `.pdf`
- Word: `.doc`, `.docx`
- Excel: `.xls`, `.xlsx`
- PPT: `.ppt`, `.pptx`

**关键方法**:
```python
class FileParserService:
    async def parse_file(file_path: str, filename: str) -> str
```

### 4.3 文件上传 API

**文件**: `backend/src/interfaces/routers/tools/files.py`

**端点**: `POST /api/v1/files/upload`

**参数**:
- `file`: 上传的文件
- `provider`: 目标供应商 (kimi, deepseek, openai 等)

**返回格式**:
```json
// API 模式 (Kimi, OpenAI 等)
{
  "success": true,
  "file_id": "file-abc123",
  "provider": "kimi",
  "mode": "api"
}

// 文本提取模式 (DeepSeek 等)
{
  "success": true,
  "content": "提取的文件内容...",
  "content_preview": "前500字符...",
  "provider": "deepseek",
  "mode": "text_extraction"
}
```

### 4.4 前端文件上传组件

**文件**: `frontend/src/components/ChatFileUpload.vue`

**职责**:
- 提供文件选择和上传 UI
- 管理已上传文件列表
- 根据 Provider 模式处理返回结果

## 5. 数据库配置

### 5.1 模型供应商配置

| 字段 | 值 |
|------|-----|
| provider_code | `kimi` |
| provider_name | `Moonshot AI (Kimi)` |
| base_url | `https://api.moonshot.cn` |
| api_key | *(用户在后台填入)* |
| is_enabled | `false` (默认禁用) |
| order | `3` |

### 5.2 模型配置

| model_code | model_name | capabilities |
|------------|------------|--------------|
| moonshot-v1-8k | Kimi 8K | chat,file,image |
| moonshot-v1-32k | Kimi 32K | chat,file,image |
| moonshot-v1-128k | Kimi 128K | chat,file,image |

## 6. AIProvider 基类扩展

在 `backend/src/infrastructure/providers/base.py` 中添加文件相关方法：

```python
class AIProvider(ABC):
    # ... 现有方法 ...

    async def upload_file(
        self,
        file_path: str,
        filename: str
    ) -> Optional[str]:
        """
        上传文件到 AI 服务（默认实现）

        不支持文件的 Provider 可覆盖此方法并记录日志

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

        Yields:
            str: 流式返回的文本片段，不支持时 yield 空字符串
        """
        logger.warning(f"{self.__class__.__name__} does not support file chat")
        yield ""
```

## 7. ProviderFactory 更新

在 `backend/src/infrastructure/providers/factory.py` 中注册 Kimi：

```python
class ProviderFactory:
    _providers: Dict[str, Type[AIProvider]] = {
        "openai": OpenAIProvider,
        "deepseek": DeepSeekProvider,
        "kimi": KimiProvider,  # 新增
    }
```

## 8. 依赖

**新增 Python 依赖** (`backend/requirements.txt`):
```
PyPDF2>=3.0.0          # PDF 解析
python-docx>=1.0.0     # Word 解析
openpyxl>=3.1.0        # Excel 解析
python-pptx>=0.6.0     # PPT 解析
httpx>=0.25.0          # 异步 HTTP 客户端
```

## 9. 新增文件清单

```
backend/src/
├── infrastructure/providers/kimi_provider.py      # Kimi Provider 实现
├── services/file_parser_service.py                # 文件解析服务
├── interfaces/routers/tools/files.py              # 文件上传 API 路由
└── scripts/init_kimi_provider.py                  # Kimi 初始化脚本

frontend/src/components/
└── ChatFileUpload.vue                             # 文件上传组件

docs/superpowers/specs/
└── 2026-03-21-kimi-integration-design.md          # 本文档
```

## 10. 测试策略

1. **单元测试**: `FileParserService` 各格式解析功能
2. **集成测试**: `KimiProvider` 文件上传和对话
3. **E2E 测试**: 前端上传 → 后端处理 → AI 响应全流程

## 11. 参考资料

- [Moonshot API 文档 - 文件接口](https://platform.moonshot.cn/docs/api/files)
- [DeepSeek API 文档](https://api-docs.deepseek.com/)
- [OpenAI Files API](https://help.openai.com/zh-hans-cn/articles/8983675)
