# 系统重构设计文档

**日期**: 2026-02-27
**目标**: 重构AI教育智研云平台，建立DDD分层架构
**时间框架**: 2周（为模块2-5留出2周）
**原则**: 渐进式重构，每步可测可交付

---

## 📋 执行摘要

### 重构目标

1. **后端重构**：将单体AIService（1276行）拆分为DDD分层架构
2. **前端重构**：拆分PreviewPanel（1348行）和ChatPanel（747行）为小组件
3. **建立测试体系**：pytest单元测试 + Playwright E2E测试
4. **为模块2打好基础**：建立Provider抽象层，支持多模型接入

### 关键约束

- ✅ 渐进式迁移，每日可测增量
- ✅ 2周完成（Day 1-10开发 + Day 11-12测试修复）
- ✅ 清除旧测试，从0建立测试体系
- ✅ 使用DDD分层架构（Domain/Application/Infrastructure/Interfaces）
- ✅ 单元测试覆盖率 >80%
- ✅ Playwright E2E测试覆盖核心流程

---

## 🏗️ 架构设计

### DDD分层架构

```
backend/src/
├── domain/                        # 领域层：纯业务逻辑，无外部依赖
│   ├── __init__.py
│   ├── entities/                 # 实体
│   │   ├── user.py              # User实体
│   │   ├── session.py           # Session实体
│   │   ├── message.py           # Message实体
│   │   └── artifact.py          # Artifact实体
│   ├── value_objects/           # 值对象
│   │   ├── message_role.py      # MessageRole (user/assistant/system)
│   │   └── artifact_type.py     # ArtifactType (html/svg/markdown)
│   └── repositories/            # 仓储接口（抽象）
│       ├── user_repository.py   # UserRepository(ABC)
│       └── session_repository.py # SessionRepository(ABC)
│
├── application/                  # 应用层：用例编排
│   ├── __init__.py
│   ├── services/
│   │   ├── chat_service.py      # 对话用例（编排domain + infrastructure）
│   │   ├── media_service.py     # 媒体生成用例
│   │   └── tool_service.py      # 工具管理用例（已存在，迁移）
│   └── dto/                     # 数据传输对象
│       ├── chat_request.py
│       └── chat_response.py
│
├── infrastructure/               # 基础设施层：外部依赖实现
│   ├── __init__.py
│   ├── providers/               # AI提供商（核心新增）
│   │   ├── base.py              # AIProvider抽象类
│   │   ├── openai_provider.py   # OpenAI实现
│   │   ├── deepseek_provider.py # DeepSeek实现
│   │   ├── kimi_provider.py     # Kimi实现
│   │   └── factory.py           # ProviderFactory
│   ├── repositories/            # 仓储实现（SQLAlchemy）
│   │   ├── user_repository.py   # SQLAlchemy实现
│   │   └── session_repository.py
│   ├── parsers/                 # 成果物解析器
│   │   └── artifact_parser.py   # 已存在，迁移
│   └── html_fixer.py            # HTML修复服务（新增，统一重复逻辑）
│
└── interfaces/                   # 接口层：API和外部交互
    ├── __init__.py
    ├── routers/                 # 路由（按资源拆分）
    │   ├── tools/
    │   │   ├── __init__.py
    │   │   ├── list.py          # GET /api/v2/tools
    │   │   ├── chat.py          # POST /api/v2/tools/{id}/chat
    │   │   ├── conversations.py # GET/DELETE /api/v2/conversations
    │   │   └── media.py         # POST /api/v2/media/generate
    │   ├── auth.py              # 认证路由（已存在，保留）
    │   └── middleware/          # 中间件
    │       ├── error_handler.py # 统一错误处理
    │       └── logging.py       # 请求日志
    └── dependencies.py          # FastAPI依赖注入
```

### 前端组件拆分

```
frontend/src/components/
├── preview/                      # 预览组件组
│   ├── PreviewPanel.vue          # 主容器（~100行）
│   ├── MarkdownPreview.vue       # Markdown渲染（~300行）
│   ├── HtmlPreview.vue           # HTML渲染（~200行）
│   ├── SvgPreview.vue            # SVG渲染（~150行）
│   └── PreviewToolbar.vue        # 工具栏（~100行）
│
├── chat/                         # 聊天组件组
│   ├── ChatPanel.vue             # 主容器（~150行）
│   ├── MessageList.vue           # 消息列表（~200行）
│   ├── MessageItem.vue           # 单条消息（~120行）
│   ├── StreamingMessage.vue      # 流式消息（~100行）
│   └── ChatInput.vue             # 输入框（~180行）
│
└── shared/                       # 共享组件
    ├── LoadingSpinner.vue        # 加载动画
    ├── ErrorMessage.vue          # 错误提示
    └── ArtifactRenderer.vue      # 通用成果物渲染
```

---

## 📅 详细重构计划（12天）

### Day 1: 建立DDD骨架 + 测试框架

**目标**: 创建新目录结构，配置测试框架，不破坏现有代码

**步骤**（每步可测试）：

#### Step 1.1: 创建DDD目录结构（30分钟）
```bash
cd backend/src
mkdir -p domain/{entities,value_objects,repositories}
mkdir -p application/{services,dto}
mkdir -p infrastructure/{providers,repositories,parsers}
mkdir -p interfaces/{routers/tools,middleware}
touch {domain,application,infrastructure,interfaces}/__init__.py
```

**验证**: 运行 `python -c "from src import domain, application, infrastructure, interfaces"` 无报错

#### Step 1.2: 配置pytest测试框架（1小时）
```bash
# backend/pytest.ini 已存在，更新配置
# backend/tests/ 目录结构
mkdir -p tests/{unit/{domain,application,infrastructure},integration,e2e}
touch tests/conftest.py
```

**conftest.py配置**:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

**验证**: 运行 `pytest --collect-only` 能发现0个测试（框架就绪）

#### Step 1.3: 配置Playwright E2E测试（1小时）
```bash
cd frontend
npm install -D @playwright/test
npx playwright install chromium
```

**playwright.config.ts**:
```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://localhost:5173',
  },
  webServer: {
    command: 'npm run dev',
    port: 5173,
  },
});
```

**验证**: 运行 `npx playwright test` 能发现0个测试

**交付物**:
- ✅ DDD目录结构创建完成
- ✅ pytest配置完成
- ✅ Playwright配置完成
- ✅ 现有功能不受影响（运行后端和前端，手动验证）

---

### Day 2: 抽取领域实体 + 仓储接口

**目标**: 将db_models.py中的ORM模型迁移为domain entities（保留旧代码）

#### Step 2.1: 创建User领域实体（1小时）
**文件**: `backend/src/domain/entities/user.py`

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: int
    username: str
    email: str
    is_admin: bool
    created_at: datetime

    def can_access_tool(self, tool_id: str) -> bool:
        """业务规则：管理员可以访问所有工具"""
        return self.is_admin
```

**测试**: `tests/unit/domain/entities/test_user.py`
```python
import pytest
from src.domain.entities.user import User

def test_admin_can_access_all_tools():
    admin = User(id=1, username="admin", email="admin@test.com", is_admin=True, created_at=datetime.now())
    assert admin.can_access_tool("any_tool") is True
```

**验证**: `pytest tests/unit/domain/entities/test_user.py` 通过

#### Step 2.2: 创建Message和Artifact实体（2小时）
**文件**: `backend/src/domain/entities/message.py`

```python
from dataclasses import dataclass
from datetime import datetime
from src.domain.value_objects.message_role import MessageRole
from src.domain.entities.artifact import Artifact

@dataclass
class Message:
    id: int
    session_id: int
    role: MessageRole
    content: str
    artifact: Optional[Artifact]
    created_at: datetime
```

**测试**: `tests/unit/domain/entities/test_message.py`

**验证**: `pytest tests/unit/domain/entities/` 通过

#### Step 2.3: 创建仓储接口（1小时）
**文件**: `backend/src/domain/repositories/user_repository.py`

```python
from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.user import User

class UserRepository(ABC):
    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        pass
```

**验证**: 运行 `python -c "from src.domain.repositories import UserRepository"` 无报错

**交付物**:
- ✅ User/Message/Artifact/Session领域实体创建
- ✅ 仓储接口定义
- ✅ 单元测试通过
- ✅ 现有功能不受影响

---

### Day 3: 实现AIProvider抽象层

**目标**: 创建Provider抽象，为多模型接入打好基础

#### Step 3.1: 定义AIProvider抽象类（1小时）
**文件**: `backend/src/infrastructure/providers/base.py`

```python
from abc import ABC, abstractmethod
from typing import List, AsyncGenerator, Optional
from src.domain.entities.message import Message

@abstractmethod
class AIProvider(ABC):
    """AI提供商抽象接口"""

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        model: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        model: str,
        **kwargs
    ) -> str:
        """非流式对话"""
        pass
```

**测试**: `tests/unit/infrastructure/providers/test_base.py`
```python
import pytest
from src.infrastructure.providers.base import AIProvider

def test_cannot_instantiate_abstract_provider():
    with pytest.raises(TypeError):
        AIProvider()
```

**验证**: `pytest tests/unit/infrastructure/providers/test_base.py` 通过

#### Step 3.2: 实现OpenAI Provider（2小时）
**文件**: `backend/src/infrastructure/providers/openai_provider.py`

```python
from openai import AsyncOpenAI
from src.infrastructure.providers.base import AIProvider
from src.domain.entities.message import Message
from typing import List, AsyncGenerator

class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat_stream(
        self,
        messages: List[Message],
        model: str = "gpt-4",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话实现"""
        openai_messages = [{"role": m.role.value, "content": m.content} for m in messages]

        stream = await self.client.chat.completions.create(
            model=model,
            messages=openai_messages,
            stream=True,
            **kwargs
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

**测试**: Mock OpenAI客户端
```python
import pytest
from src.infrastructure.providers.openai_provider import OpenAIProvider

@pytest.mark.asyncio
async def test_openai_provider_chat_stream():
    provider = OpenAIProvider(api_key="test-key")
    # 使用httpx Mock或者创建测试API
    # 验证流式响应
```

**验证**: `pytest tests/unit/infrastructure/providers/test_openai_provider.py` 通过

#### Step 3.3: 实现ProviderFactory（1小时）
**文件**: `backend/src/infrastructure/providers/factory.py`

```python
import os
from src.infrastructure.providers.base import AIProvider
from src.infrastructure.providers.openai_provider import OpenAIProvider
from src.infrastructure.providers.deepseek_provider import DeepSeekProvider

class ProviderFactory:
    @staticmethod
    def create(provider: str) -> AIProvider:
        if provider == "openai":
            return OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
        elif provider == "deepseek":
            return DeepSeekProvider(api_key=os.getenv("DEEPSEEK_API_KEY"))
        else:
            raise ValueError(f"Unknown provider: {provider}")
```

**测试**: `tests/unit/infrastructure/providers/test_factory.py`

**验证**: `pytest tests/unit/infrastructure/providers/` 全部通过

**交付物**:
- ✅ AIProvider抽象类
- ✅ OpenAI/DeepSeek/Kimi Provider实现
- ✅ ProviderFactory
- ✅ 单元测试覆盖
- ✅ 现有功能不受影响

---

### Day 4: 切换到新Provider层（关键里程碑）

**目标**: 替换AIService中的provider逻辑，使用新实现

#### Step 4.1: 在AIService中添加新Provider（双写模式）（1小时）
**文件**: `backend/src/services/ai_service.py`

```python
# 保留旧的 _get_ai_client 方法
# 添加新的使用Provider的实现

class AIService:
    def __init__(self):
        self._old_client, self._old_model = self._get_ai_client()  # 保留
        self._provider = ProviderFactory.create(os.getenv("CURRENT_PROVIDER", "deepseek"))

    async def chat_stream_v2(self, messages: List[Message], model: str):
        """使用新Provider的实现"""
        async for chunk in self._provider.chat_stream(messages, model):
            yield chunk
```

**验证**: 运行后端，手动测试一个对话（新v2接口）

#### Step 4.2: 添加集成测试（2小时）
**文件**: `tests/integration/api/test_chat_integration.py`

```python
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_chat_stream_integration():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/tools/test-tool/chat/stream", json={
            "messages": [{"role": "user", "content": "Hello"}]
        })
        assert response.status_code == 200
```

**验证**: `pytest tests/integration/api/test_chat_integration.py` 通过

#### Step 4.3: 逐步切换路由到新实现（2小时）
**文件**: `backend/src/routers/tools.py`

```python
# 旧代码（保留）
@router.post("/tools/{tool_id}/chat/stream")
async def chat_stream_old(...):
    ...

# 新代码（添加v2端点测试）
@router.post("/api/v2/tools/{tool_id}/chat/stream")
async def chat_stream_v2(tool_id: str, request: ChatRequest):
    ai_service = get_ai_service()
    # 使用新的chat_stream_v2方法
    return StreamingResponse(
        ai_service.chat_stream_v2(request.messages, request.model),
        media_type="text/event-stream"
    )
```

**验证**:
1. 启动后端
2. 使用前端或Postman测试 `/api/v2/tools/{id}/chat/stream`
3. 验证流式响应正常

#### Step 4.4: 删除旧代码（1小时）
**文件**: `backend/src/services/ai_service.py`

```python
# 删除 _get_ai_client 方法
# 删除旧的 chat_stream 方法
# 重命名 chat_stream_v2 为 chat_stream
```

**验证**:
1. 运行完整测试套件 `pytest`
2. 手动测试所有对话功能
3. 确认无回归

**交付物**:
- ✅ 新Provider层完全替换旧实现
- ✅ 集成测试通过
- ✅ 所有对话功能正常
- ✅ 旧代码已删除

---

### Day 5: 前端PreviewPanel拆分 - Part 1

**目标**: 拆分PreviewPanel为5个子组件

#### Step 5.1: 创建MarkdownPreview组件（2小时）
**文件**: `frontend/src/components/preview/MarkdownPreview.vue`

```vue
<template>
  <div class="markdown-preview" v-html="renderedHtml"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { renderMarkdown } from '@/utils/markdownRenderer';

const props = defineProps<{
  content: string;
}>();

const renderedHtml = computed(() => renderMarkdown(props.content));
</script>
```

**测试**: `tests/unit/components/MarkdownPreview.spec.ts`
```typescript
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import MarkdownPreview from '@/components/preview/MarkdownPreview.vue';

describe('MarkdownPreview', () => {
  it('should render markdown', () => {
    const wrapper = mount(MarkdownPreview, {
      props: { content: '# Hello' }
    });
    expect(wrapper.html()).toContain('<h1>');
  });
});
```

**验证**: `npm run test tests/unit/components/MarkdownPreview.spec.ts` 通过

#### Step 5.2: 创建HtmlPreview组件（1.5小时）
**文件**: `frontend/src/components/preview/HtmlPreview.vue`

```vue
<template>
  <div class="html-preview">
    <iframe :srcdoc="sanitizedHtml" sandbox="allow-scripts"></iframe>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import DOMPurify from 'dompurify';

const props = defineProps<{
  content: string;
}>();

const sanitizedHtml = computed(() => DOMPurify.sanitize(props.content));
</script>
```

**测试**: `tests/unit/components/HtmlPreview.spec.ts`

**验证**: `npm run test` 通过

#### Step 5.3: 创建SvgPreview组件（1.5小时）
**文件**: `frontend/src/components/preview/SvgPreview.vue`

```vue
<template>
  <div class="svg-preview" v-html="sanitizedSvg" @click="handleDownload"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import DOMPurify from 'dompurify';

const props = defineProps<{
  content: string;
}>();

const sanitizedSvg = computed(() => DOMPurify.sanitize(props.content, { USE_PROFILES: { svg: true } }));

const handleDownload = () => {
  const blob = new Blob([props.content], { type: 'image/svg+xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'artifact.svg';
  a.click();
};
</script>
```

**测试**: `tests/unit/components/SvgPreview.spec.ts`

**验证**: `npm run test` 通过

**交付物**:
- ✅ MarkdownPreview组件 + 测试
- ✅ HtmlPreview组件 + 测试
- ✅ SvgPreview组件 + 测试
- ✅ 组件可独立使用

---

### Day 6: 前端PreviewPanel拆分 - Part 2

**目标**: 完成PreviewPanel重构，整合所有子组件

#### Step 6.1: 创建PreviewToolbar组件（1小时）
**文件**: `frontend/src/components/preview/PreviewToolbar.vue`

```vue
<template>
  <div class="preview-toolbar">
    <button @click="$emit('download-markdown')" v-if="isMarkdown">
      下载 Markdown
    </button>
    <button @click="$emit('download-pdf')" v-if="isMarkdown">
      下载 PDF
    </button>
    <button @click="$emit('download-svg')" v-if="isSvg">
      下载 SVG
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  artifactType: string;
}>();

const isMarkdown = computed(() => props.artifactType === 'markdown');
const isSvg = computed(() => props.artifactType === 'svg');

defineEmits(['download-markdown', 'download-pdf', 'download-svg']);
</script>
```

**测试**: `tests/unit/components/PreviewToolbar.spec.ts`

**验证**: `npm run test` 通过

#### Step 6.2: 重构PreviewPanel主容器（2小时）
**文件**: `frontend/src/components/preview/PreviewPanel.vue`

```vue
<template>
  <div class="preview-panel" :class="{ 'is-fullscreen': isFullscreen }">
    <PreviewToolbar
      :artifact-type="artifact?.type"
      @download-markdown="handleDownloadMarkdown"
      @download-pdf="handleDownloadPDF"
      @download-svg="handleDownloadSvg"
    />

    <div class="preview-content">
      <MarkdownPreview v-if="artifact?.type === 'markdown'" :content="artifact.content" />
      <HtmlPreview v-else-if="artifact?.type === 'html'" :content="artifact.content" />
      <SvgPreview v-else-if="isSvgArtifact(artifact)" :content="artifact.content" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import MarkdownPreview from './MarkdownPreview.vue';
import HtmlPreview from './HtmlPreview.vue';
import SvgPreview from './SvgPreview.vue';
import PreviewToolbar from './PreviewToolbar.vue';

const props = defineProps<{
  artifact: Artifact | null;
}>();

const isFullscreen = ref(false);

// 简化的下载方法
const handleDownloadMarkdown = () => { /* ... */ };
const handleDownloadPDF = () => { /* ... */ };
const handleDownloadSvg = () => { /* ... */ };

const isSvgArtifact = (artifact: Artifact | null) => {
  return artifact?.type === 'svg';
};
</script>

<style scoped>
/* 只有布局样式，内容样式在子组件中 */
.preview-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}
</style>
```

**测试**: `tests/unit/components/PreviewPanel.spec.ts`

**验证**: `npm run test` 通过

#### Step 6.3: 集成测试（1小时）
**文件**: `tests/integration/preview.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test('Preview panel renders markdown', async ({ page }) => {
  await page.goto('/modules/ai_tools/lesson-generator');
  await page.fill('[data-testid="chat-input"]', '生成一个Markdown教案');
  await page.click('[data-testid="send-button"]');

  // 等待成果物渲染
  await expect(page.locator('.markdown-preview')).toBeVisible({ timeout: 10000 });
});
```

**验证**: `npx playwright test` 通过

**交付物**:
- ✅ PreviewToolbar组件 + 测试
- ✅ PreviewPanel重构完成（~100行）
- ✅ 所有子组件集成测试通过
- ✅ Playwright E2E测试通过

---

### Day 7: 前端ChatPanel拆分

**目标**: 拆分ChatPanel为5个子组件

#### Step 7.1: 创建MessageItem组件（1.5小时）
**文件**: `frontend/src/components/chat/MessageItem.vue`

```vue
<template>
  <div class="message-item" :class="`message-${message.role}`">
    <div class="message-avatar">
      <img :src="avatarUrl" :alt="message.role" />
    </div>
    <div class="message-content">
      <div class="message-text" v-html="renderedContent"></div>
      <div class="message-time">{{ formattedTime }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { renderMarkdown } from '@/utils/markdownRenderer';

const props = defineProps<{
  message: Message;
}>();

const renderedContent = computed(() => {
  if (props.message.role === 'assistant') {
    return renderMarkdown(props.message.content);
  }
  return props.message.content;
});

const formattedTime = computed(() => {
  return new Date(props.message.created_at).toLocaleTimeString();
});

const avatarUrl = computed(() => {
  return props.message.role === 'user' ? '/user-avatar.png' : '/ai-avatar.png';
});
</script>
```

**测试**: `tests/unit/components/MessageItem.spec.ts`

**验证**: `npm run test` 通过

#### Step 7.2: 创建StreamingMessage组件（1.5小时）
**文件**: `frontend/src/components/chat/StreamingMessage.vue`

```vue
<template>
  <div class="message-item message-assistant streaming">
    <div class="message-avatar">
      <img src="/ai-avatar.png" alt="AI" />
    </div>
    <div class="message-content">
      <div class="message-text" v-html="renderedContent"></div>
      <div class="streaming-indicator">●</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { renderMarkdown } from '@/utils/markdownRenderer';

const props = defineProps<{
  content: string;
}>();

const renderedContent = computed(() => renderMarkdown(props.content));
</script>
```

**测试**: `tests/unit/components/StreamingMessage.spec.ts`

**验证**: `npm run test` 通过

#### Step 7.3: 创建MessageList和ChatInput组件（2小时）
**文件**: `frontend/src/components/chat/MessageList.vue`

```vue
<template>
  <div class="message-list" ref="scrollContainer">
    <MessageItem
      v-for="message in messages"
      :key="message.id"
      :message="message"
    />
    <StreamingMessage
      v-if="streamingContent"
      :content="streamingContent"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import MessageItem from './MessageItem.vue';
import StreamingMessage from './StreamingMessage.vue';

const props = defineProps<{
  messages: Message[];
  streamingContent?: string;
}>();

const scrollContainer = ref<HTMLElement>();

// 自动滚动到底部
watch(() => props.messages.length, async () => {
  await nextTick();
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight;
  }
});
</script>
```

**测试**: `tests/unit/components/MessageList.spec.ts`

**验证**: `npm run test` 通过

#### Step 7.4: 重构ChatPanel主容器（1小时）
**文件**: `frontend/src/components/chat/ChatPanel.vue`

```vue
<template>
  <div class="chat-panel">
    <MessageList
      :messages="messages"
      :streaming-content="streamingContent"
    />
    <ChatInput
      @send="handleSend"
      :disabled="isLoading"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import MessageList from './MessageList.vue';
import ChatInput from './ChatInput.vue';

const messages = ref<Message[]>([]);
const streamingContent = ref('');
const isLoading = ref(false);

const handleSend = async (content: string) => {
  isLoading.value = true;
  // ... 发送逻辑
};
</script>
```

**测试**: `tests/unit/components/ChatPanel.spec.ts`

**验证**: `npm run test` 通过

**交付物**:
- ✅ MessageItem组件 + 测试
- ✅ StreamingMessage组件 + 测试
- ✅ MessageList组件 + 测试
- ✅ ChatInput组件 + 测试
- ✅ ChatPanel重构完成（~150行）
- ✅ 所有组件测试通过

---

### Day 8: 后端路由拆分 - Part 1

**目标**: 将tools.py拆分为按资源组织的路由文件

#### Step 8.1: 创建tools/list.py（1小时）
**文件**: `backend/src/interfaces/routers/tools/list.py`

```python
from fastapi import APIRouter, Depends
from src.models import ToolListResponse
from src.interfaces.dependencies import get_tool_service, get_current_user

router = APIRouter()

@router.get("/tools", response_model=ToolListResponse)
async def get_tools(
    current_user = Depends(get_current_user),
    tool_service = Depends(get_tool_service)
):
    """获取所有工具列表"""
    tools = tool_service.load_all_tools()
    category_groups = tool_service.group_by_category(tools)

    return ToolListResponse(categories=category_groups)
```

**测试**: `tests/integration/api/test_tools_list.py`

**验证**: `pytest tests/integration/api/test_tools_list.py` 通过

#### Step 8.2: 创建tools/chat.py（2小时）
**文件**: `backend/src/interfaces/routers/tools/chat.py`

```python
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from src.models import ChatRequest
from src.interfaces.dependencies import get_ai_service, get_session_service

router = APIRouter()

@router.post("/tools/{tool_id}/chat/stream")
async def chat_stream(
    tool_id: str,
    request: ChatRequest,
    ai_service = Depends(get_ai_service),
    session_service = Depends(get_session_service)
):
    """流式对话"""
    # 获取工具配置
    tool_service = get_tool_service()
    tool = tool_service.get_tool(tool_id)

    # 流式响应
    return StreamingResponse(
        ai_service.chat_stream(
            messages=request.messages,
            model=tool.model,
            system_prompt=tool.system_prompt
        ),
        media_type="text/event-stream"
    )
```

**测试**: `tests/integration/api/test_tools_chat.py`

**验证**: `pytest tests/integration/api/test_tools_chat.py` 通过

#### Step 8.3: 创建tools/conversations.py（1.5小时）
**文件**: `backend/src/interfaces/routers/tools/conversations.py`

```python
from fastapi import APIRouter, Depends
from src.models import ConversationListResponse
from src.interfaces.dependencies import get_session_service

router = APIRouter()

@router.get("/tools/{tool_id}/conversations", response_model=ConversationListResponse)
async def get_conversations(
    tool_id: str,
    session_service = Depends(get_session_service)
):
    """获取会话列表"""
    conversations = session_service.get_user_conversations(tool_id)
    return ConversationListResponse(conversations=conversations)

@router.delete("/tools/{tool_id}/conversations/{conv_id}")
async def delete_conversation(
    tool_id: str,
    conv_id: str,
    session_service = Depends(get_session_service)
):
    """删除会话"""
    session_service.delete_conversation(conv_id)
    return {"message": "Deleted"}
```

**测试**: `tests/integration/api/test_tools_conversations.py`

**验证**: `pytest tests/integration/api/test_tools_conversations.py` 通过

**交付物**:
- ✅ tools/list.py + 测试
- ✅ tools/chat.py + 测试
- ✅ tools/conversations.py + 测试
- ✅ 路由功能独立可测

---

### Day 9: 后端路由拆分 - Part 2

**目标**: 完成路由拆分，添加统一错误处理

#### Step 9.1: 创建tools/media.py（1小时）
**文件**: `backend/src/interfaces/routers/tools/media.py`

```python
from fastapi import APIRouter, Depends
from src.models import MediaGenerateRequest, MediaGenerateResponse

router = APIRouter()

@router.post("/tools/{tool_id}/generate-media")
async def generate_media(
    tool_id: str,
    request: MediaGenerateRequest,
    ai_service = Depends(get_ai_service)
):
    """生成媒体内容（图片/音频）"""
    result = await ai_service.generate_media(
        prompt=request.prompt,
        media_type=request.media_type
    )
    return MediaGenerateResponse(url=result.url)
```

**测试**: `tests/integration/api/test_tools_media.py`

**验证**: `pytest tests/integration/api/test_tools_media.py` 通过

#### Step 9.2: 创建统一错误处理中间件（1.5小时）
**文件**: `backend/src/interfaces/middleware/error_handler.py`

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from logging import getLogger

logger = getLogger(__name__)

class ApplicationException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code

async def error_handler(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except ApplicationException as e:
        logger.error(f"Application error: {e.message}")
        return JSONResponse(
            status_code=e.status_code,
            content={"error": {"code": e.code, "message": e.message}}
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}
        )
```

**测试**: `tests/integration/middleware/test_error_handler.py`

**验证**: `pytest tests/integration/middleware/` 通过

#### Step 9.3: 更新main.py注册新路由（1.5小时）
**文件**: `backend/src/main.py`

```python
from fastapi import FastAPI
from src.interfaces.middleware.error_handler import error_handler
from src.interfaces.routers.tools import list, chat, conversations, media

app = FastAPI()

# 注册中间件
app.middleware("http")(error_handler)

# 注册路由
app.include_router(list.router, tags=["tools"])
app.include_router(chat.router, tags=["tools"])
app.include_router(conversations.router, tags=["tools"])
app.include_router(media.router, tags=["tools"])

# 删除旧的 tools.py 引用
```

**验证**:
1. 启动后端 `python -m src.main`
2. 访问 `/docs` 查看API文档
3. 手动测试所有端点

#### Step 9.4: 删除旧的tools.py（1小时）
```bash
# 确认所有功能正常后删除
rm backend/src/routers/tools.py
```

**验证**: 运行完整测试套件 `pytest`

**交付物**:
- ✅ tools/media.py + 测试
- ✅ 统一错误处理中间件
- ✅ main.py更新
- ✅ 旧tools.py已删除
- ✅ 所有测试通过

---

### Day 10: 建立HTML修复服务

**目标**: 抽取HTML修复逻辑为独立服务

#### Step 10.1: 创建HtmlFixerService（2小时）
**文件**: `backend/src/infrastructure/html_fixer.py`

```python
import re
from bs4 import BeautifulSoup
from typing import List

class HtmlFixerService:
    """HTML修复服务 - 统一处理HTML标签修复"""

    @staticmethod
    def fix_broken_tags(html: str) -> str:
        """修复未闭合的HTML标签"""
        soup = BeautifulSoup(html, 'html.parser')
        return str(soup)

    @staticmethod
    def close_open_tags(html: str) -> str:
        """关闭未闭合的标签（正则表达式方法）"""
        # 常见未闭合标签修复
        html = re.sub(r'<(img|br|hr)(?![^>]*\/)>', r'<\1 />', html)

        # 使用BeautifulSoup确保所有标签闭合
        soup = BeautifulSoup(html, 'html.parser')
        return soup.prettify()

    @staticmethod
    def sanitize_scripts(html: str) -> str:
        """移除危险的script标签"""
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup.find_all('script'):
            script.decompose()
        return str(soup)
```

**测试**: `tests/unit/infrastructure/test_html_fixer.py`
```python
import pytest
from src.infrastructure.html_fixer import HtmlFixerService

def test_fix_broken_tags():
    broken = "<div><p>Hello"
    fixed = HtmlFixerService.fix_broken_tags(broken)
    assert "</p></div>" in fixed

def test_sanitize_scripts():
    html = "<div>Hello<script>alert('xss')</script></div>"
    cleaned = HtmlFixerService.sanitize_scripts(html)
    assert "<script>" not in cleaned
    assert "Hello" in cleaned
```

**验证**: `pytest tests/unit/infrastructure/test_html_fixer.py` 通过

#### Step 10.2: 在项目中应用HtmlFixer（2小时）
**文件**: 更新所有使用HTML修复的地方

```python
# 在 ai_service.py 或 media_service.py 中
from src.infrastructure.html_fixer import HtmlFixerService

class MediaService:
    def generate_html(self, content: str) -> str:
        # 生成HTML
        html = self._generate_raw_html(content)
        # 使用统一修复服务
        return HtmlFixerService.fix_broken_tags(html)
```

**验证**:
1. 运行单元测试
2. 手动测试HTML生成功能
3. 验证所有HTML都正确闭合

**交付物**:
- ✅ HtmlFixerService + 单元测试
- ✅ 所有HTML修复逻辑统一
- ✅ 重复代码已消除

---

### Day 11: 完善测试覆盖

**目标**: 提升测试覆盖率到80%+

#### Step 11.1: 补充领域层测试（2小时）
- 为所有实体添加单元测试
- 为值对象添加测试
- 测试覆盖业务规则

**验证**: `pytest --cov=src/domain --cov-report=term-missing`
目标：domain覆盖率 >90%

#### Step 11.2: 补充应用层测试（2小时）
- 测试用例编排逻辑
- Mock基础设施层
- 测试异常场景

**验证**: `pytest --cov=src/application --cov-report=term-missing`
目标：application覆盖率 >85%

#### Step 11.3: 补充基础设施层测试（2小时）
- Provider Mock测试
- HtmlFixer边界测试
- 仓储集成测试

**验证**: `pytest --cov=src/infrastructure --cov-report=term-missing`
目标：infrastructure覆盖率 >80%

**交付物**:
- ✅ 单元测试覆盖率 >80%
- ✅ 所有核心逻辑有测试保护

---

### Day 12: Playwright E2E测试 + 修复

**目标**: 建立完整的E2E测试套件

#### Step 12.1: 编写核心流程E2E测试（3小时）
**文件**: `frontend/tests/e2e/chat.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('AI对话流程', () => {
  test('完整对话流程', async ({ page }) => {
    // 登录
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password');
    await page.click('[data-testid="login-button"]');

    // 选择工具
    await page.goto('/modules/ai_tools');
    await page.click('[data-testid="tool-lesson-generator"]');

    // 发送消息
    await page.fill('[data-testid="chat-input"]', '帮我生成一个数学教案');
    await page.click('[data-testid="send-button"]');

    // 验证响应
    await expect(page.locator('[data-testid="message-content"]').first()).toBeVisible({ timeout: 10000 });
  });

  test('流式响应显示', async ({ page }) => {
    await page.goto('/modules/ai_tools/lesson-generator');
    await page.fill('[data-testid="chat-input"]', '生成教案');
    await page.click('[data-testid="send-button"]');

    // 验证流式指示器
    await expect(page.locator('.streaming-indicator')).toBeVisible();
    // 等待完成
    await expect(page.locator('.streaming-indicator')).not.toBeVisible({ timeout: 15000 });
  });
});
```

**文件**: `frontend/tests/e2e/preview.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('成果物预览', () => {
  test('Markdown预览渲染', async ({ page }) => {
    await page.goto('/modules/ai_tools/lesson-generator');
    await page.fill('[data-testid="chat-input"]', '生成Markdown教案');
    await page.click('[data-testid="send-button"]');

    // 等待成果物生成
    await expect(page.locator('.markdown-preview')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('h1')).toBeVisible();
  });

  test('下载功能', async ({ page }) => {
    await page.goto('/modules/ai_tools/lesson-generator');
    await page.fill('[data-testid="chat-input"]', '生成教案');
    await page.click('[data-testid="send-button"]');

    // 等待成果物
    await expect(page.locator('[data-testid="download-markdown"]')).toBeVisible();

    // 点击下载
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="download-markdown"]');
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toContain('.md');
  });
});
```

**验证**: `npx playwright test`
目标：所有E2E测试通过

#### Step 12.2: 运行完整测试套件 + 修复问题（3小时）
```bash
# 后端单元测试
pytest --cov=src --cov-report=html

# 前端单元测试
npm run test:coverage

# E2E测试
npx playwright test
```

**验证**: 所有测试通过，覆盖率达标

#### Step 12.3: 性能测试（可选，1小时）
- 测试流式响应延迟
- 测试大文件处理
- 测试并发请求

**交付物**:
- ✅ Playwright E2E测试套件
- ✅ 所有测试通过
- ✅ 测试覆盖率 >80%
- ✅ 无回归问题

---

## 📊 测试策略

### 单元测试（pytest）

**覆盖率目标**: >80%

**分层测试**:
- **Domain层**: 纯逻辑，Mock所有依赖
- **Application层**: Mock Infrastructure层
- **Infrastructure层**: Mock外部API（OpenAI等）
- **Interfaces层**: 集成测试，使用test client

**示例**:
```python
# tests/unit/domain/entities/test_user.py
def test_admin_can_access_all_tools():
    admin = User(id=1, username="admin", is_admin=True, ...)
    assert admin.can_access_tool("any_tool") is True

# tests/unit/infrastructure/providers/test_openai_provider.py
@pytest.mark.asyncio
async def test_openai_provider_chat_stream(mocker):
    mock_client = mocker.patch('openai.AsyncOpenAI')
    provider = OpenAIProvider(api_key="test")
    # 验证调用逻辑
```

### 集成测试

**目标**: 测试API端点

**示例**:
```python
# tests/integration/api/test_chat.py
@pytest.mark.asyncio
async def test_chat_stream_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v2/tools/test/chat/stream", json={...})
        assert response.status_code == 200
```

### E2E测试（Playwright）

**目标**: 覆盖核心用户流程

**测试场景**:
1. 用户登录
2. 选择AI工具
3. 发送对话
4. 流式响应显示
5. 成果物预览
6. 下载功能

**示例**:
```typescript
test('完整对话流程', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[data-testid="email-input"]', 'test@example.com');
  await page.click('[data-testid="login-button"]');
  await expect(page).toHaveURL('/modules/ai_tools');
});
```

---

## 🎯 成功标准

### 功能完整性
- ✅ 所有现有功能正常工作（无回归）
- ✅ 新架构按DDD分层组织
- ✅ 前端组件拆分完成

### 代码质量
- ✅ 单元测试覆盖率 >80%
- ✅ 所有测试通过（pytest + Playwright）
- ✅ 代码行数减少（每个文件<500行）

### 架构质量
- ✅ 清晰的职责分离
- ✅ Provider抽象层建立
- ✅ 统一错误处理
- ✅ 为模块2打好基础

### 时间目标
- ✅ 10天开发完成
- ✅ 2天测试修复
- ✅ 总共12天（2周）

---

## 🚨 风险控制

### 每日检查点
- 每天结束前运行测试套件
- 测试不通过不进入下一步
- Git提交必须通过测试

### Git分支策略
```
main (生产)
  └── dev (开发主分支)
      ├── feature/ddd-layer (Day 1-4)
      ├── feature/frontend-preview (Day 5-6)
      ├── feature/frontend-chat (Day 7)
      ├── feature/backend-routes (Day 8-9)
      └── feature/html-fixer (Day 10)
```

### 回滚计划
- 每个功能独立分支
- 合并到dev前测试
- 出问题可快速回滚

### Feature Flag
```python
# 使用环境变量控制新功能
USE_NEW_PROVIDER = os.getenv("USE_NEW_PROVIDER", "false") == "true"

if USE_NEW_PROVIDER:
    return new_provider.chat_stream(...)
else:
    return old_provider.chat_stream(...)
```

---

## 📚 参考资料

- DDD分层架构：https://martinfowler.com/bliki/PresentationDomainDataLayering.html
- FastAPI测试：https://fastapi.tiangolo.com/tutorial/testing/
- Playwright文档：https://playwright.dev/python/
- pytest覆盖率：https://pytest-cov.readthedocs.io/

---

## ✅ 下一步

设计文档完成后，将：
1. 获取用户批准
2. 调用 `writing-plans` 技能创建实施计划
3. 开始执行Day 1任务
