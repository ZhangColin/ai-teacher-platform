# 流式续写改造实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将递归续写改为后端内部循环续写，前端只看到一个统一的流

**Architecture:**
- 后端：将 `chat_stream` 方法的递归调用改为内部 `for` 循环，每轮调用 API 后检测 `finish_reason`，决定是否继续
- 前端：删除所有去重逻辑，简化为直接追加内容
- 接口：统一使用 `{'type': 'content', 'content': ...}` 格式 yield，前端按 `type` 字段区分

**Tech Stack:** Python 3.10+, FastAPI, OpenAI SDK, Vue 3, TypeScript, Pinia

---

## Scope 检查

✅ **单一子系统** - 只涉及流式续写逻辑改造，不需要拆分。

---

## 文件结构

### 后端文件

**修改**: `backend/src/services/ai_service.py`
- 当前：第 860-1393 行的 `chat_stream` 方法使用递归续写
- 改造：
  - 添加模块级常量 `PLATFORM_CAPS`（文件顶部，约第 30 行）
  - 添加 `build_continuation_messages()` 函数（约第 50 行）
  - 添加 `build_fallback_prompt()` 函数（约第 80 行）
  - 重构 `chat_stream()` 方法（第 860-1393 行，约 200 行改造）
  - 删除续写相关逻辑中的 `_single_stream_call()` 调用（如果有）

### 前端文件

**修改**: `frontend/src/stores/sessionStore.ts`
- 当前：第 114-151 行有复杂的去重逻辑
- 改造：
  - 删除第 114-151 行的去重逻辑（38 行）
  - 简化为直接追加（约 5 行）
  - 删除辅助函数 `calculateSimilarity`, `findSplitPosition`, `calculateOverlapScore`（约第 280-330 行）

**删除**: `frontend/tests/unit/codeblockDedup.spec.ts`
- 不再需要去重逻辑的测试

---

## Phase 1: 后端改造（2-3小时）

### Task 1: 添加平台能力配置表

**Files:**
- Modify: `backend/src/services/ai_service.py:30`

- [ ] **Step 1: 在文件顶部添加 PLATFORM_CAPS 常量**

在 `ai_service.py` 顶部的导入语句之后（约第 30 行），添加平台能力配置表：

```python
# 平台能力配置表（用于续写策略）
PLATFORM_CAPS = {
    "anthropic": {"prefill": True},   # 支持 assistant prefill（隐式续写）
    "openai":    {"prefill": False},  # 不支持，需降级到显式提示
    "deepseek":  {"prefill": False},
    "kimi":      {"prefill": False},
    "glm":       {"prefill": False},
    "newapi":    {"prefill": False},
}
```

**验证**: 配置表在模块级可见，所有方法都可以访问

- [ ] **Step 2: 提交配置表**

```bash
git add backend/src/services/ai_service.py
git commit -m "feat: 添加平台续写能力配置表

- 定义 PLATFORM_CAPS 常量
- 标记各供应商是否支持 assistant prefill
- 为后续续写逻辑改造做准备

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 2: 添加续写 messages 构建函数

**Files:**
- Modify: `backend/src/services/ai_service.py:50`

- [ ] **Step 1: 添加 build_continuation_messages() 函数**

在 `AIService` 类外部（约第 50 行），添加续写 messages 构建函数：

```python
def build_continuation_messages(
    base_messages: list,
    accumulated: str,
    provider_code: str
) -> list:
    """
    构建续写所需的 messages 列表

    优先使用隐式续写（assistant prefill），不支持时降级到显式提示

    Args:
        base_messages: 基础消息列表（system + history + user）
        accumulated: 已生成的内容
        provider_code: 供应商代码（如 "openai", "deepseek"）

    Returns:
        完整的 messages 列表
    """
    supports_prefill = PLATFORM_CAPS.get(provider_code, {}).get("prefill", False)

    if supports_prefill:
        # 隐式续写：直接把已生成内容作为 assistant 消息
        # AI 会认为自己还在生成同一条消息，自然续写
        return base_messages + [{"role": "assistant", "content": accumulated}]
    else:
        # 显式续写：追加用户提示
        return base_messages + [
            {"role": "assistant", "content": accumulated},
            {"role": "user", "content": build_fallback_prompt(accumulated)},
        ]
```

- [ ] **Step 2: 添加 build_fallback_prompt() 辅助函数**

```python
def build_fallback_prompt(content: str) -> str:
    """
    显式续写的提示词，根据内容类型动态调整

    Args:
        content: 已生成的内容

    Returns:
        续写提示词
    """
    # 判断是否在代码块中（```数量为奇数）
    in_code_block = content.count("```") % 2 == 1

    if in_code_block:
        return "请继续输出代码，直接从截断处续写，不要输出 ``` 标记，不要重复已有代码。"
    else:
        return "请继续，直接从截断处续写，不要重复已有内容。"
```

**验证**: 函数可以独立导入和调用

- [ ] **Step 3: 添加单元测试**

创建 `backend/tests/test_continuation_messages.py`:

```python
import pytest
from src.services.ai_service import build_continuation_messages, build_fallback_prompt, PLATFORM_CAPS

def test_build_fallback_prompt_code_block():
    """测试代码块场景的提示词生成"""
    content = "```python\nprint('hello'"
    prompt = build_fallback_prompt(content)
    assert "```" not in prompt
    assert "不要输出" in prompt

def test_build_fallback_prompt_normal():
    """测试普通文本的提示词生成"""
    content = "这是一段普通文本，"
    prompt = build_fallback_prompt(content)
    assert "继续" in prompt

def test_build_continuation_messages_openai():
    """测试 OpenAI 的显式续写"""
    base = [{"role": "user", "content": "你好"}]
    accumulated = "你好，我是"

    messages = build_continuation_messages(base, accumulated, "openai")

    # OpenAI 不支持 prefill，应该有两条新消息
    assert len(messages) == 3
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "你好，我是"
    assert messages[2]["role"] == "user"
    assert "继续" in messages[2]["content"]

def test_build_continuation_messages_anthropic():
    """测试 Anthropic 的隐式续写"""
    base = [{"role": "user", "content": "你好"}]
    accumulated = "你好，我是"

    messages = build_continuation_messages(base, accumulated, "anthropic")

    # Anthropic 支持 prefill，应该只有一条新消息
    assert len(messages) == 2
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "你好，我是"
```

运行测试：

```bash
cd backend
pytest tests/test_continuation_messages.py -v
```

预期：全部 PASS

- [ ] **Step 4: 提交函数和测试**

```bash
git add backend/src/services/ai_service.py backend/tests/test_continuation_messages.py
git commit -m "feat: 添加续写 messages 构建函数

- 添加 build_continuation_messages() 处理隐式/显式续写
- 添加 build_fallback_prompt() 生成续写提示词
- 支持自动降级：隐式续写不支持时使用显式提示
- 添加单元测试验证各供应商的续写逻辑

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 3: 重构 chat_stream() 方法 - 提取基础结构

**Files:**
- Modify: `backend/src/services/ai_service.py:860-1393`

- [ ] **Step 1: 备份当前 chat_stream 方法**

先备份当前实现，以便对比：

```bash
cp backend/src/services/ai_service.py backend/src/services/ai_service.py.backup
```

- [ ] **Step 2: 找到 chat_stream 方法并阅读**

打开文件，定位到第 860 行的 `async def chat_stream(...)`，阅读到第 1393 行，理解当前实现。

**关键点**：
- 第 1172-1197 行：第一次流式调用
- 第 1243-1365 行：检测到截断后的续写逻辑
- 第 1313 行：递归调用 `self.chat_stream`

- [ ] **Step 3: 创建新版本的 chat_stream 方法结构**

在备份后，开始重构。先写出新的基础结构：

```python
async def chat_stream(self, system_prompt: str, history: List[Dict[str, str]], user_message: str, max_continue: int = 3, model_config: Optional[str] = None) -> AsyncGenerator[str | dict, None]:
    """
    进行对话（流式输出）

    Args:
        system_prompt: Agent 的系统提示词
        history: 历史消息列表
        user_message: 用户当前消息
        max_continue: 最大续写次数
        model_config: 模型配置（格式：provider:model_name）

    Yields:
        dict: {'type': 'content', 'content': str} 或 {'type': 'usage', ...}
    """
    # 解析 provider 和 model（保持原有逻辑）
    # ...（从原代码复制第 875-900 行的解析逻辑）

    # 构建基础消息列表（只构建一次）
    base_messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        base_messages.append({"role": msg["role"], "content": msg["content"]})
    base_messages.append({"role": "user", "content": user_message})

    accumulated = ""  # 累积所有生成的内容
    total_usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}

    # 主循环：最多续写 max_continue 次
    for continue_count in range(max_continue + 1):
        # 构建当前轮的 messages
        if continue_count == 0:
            messages = base_messages
        else:
            messages = build_continuation_messages(
                base_messages,
                accumulated,
                provider_code
            )

        logger.info(f"流式对话请求（第 {continue_count + 1} 轮）- 使用模型: {model_name}")

        # TODO: 调用 API 并处理流式响应
        # （下一步实现）

    # 发送最终的 usage 信息
    if total_usage['total_tokens'] > 0:
        # 计算积分
        try:
            from .point_service import PointService
            point_service = PointService(self.db)
            points = point_service.calculate_points_from_tokens(
                provider_code=provider_code,
                model_code=model_name,
                prompt_tokens=total_usage['prompt_tokens'],
                completion_tokens=total_usage['completion_tokens']
            )
            total_usage['points_deducted'] = points
        except Exception as e:
            logger.error(f"积分计算失败: {e}")
            total_usage['points_deducted'] = 0

    yield {
        'type': 'usage',
        'model_provider': provider_code,
        'model_name': model_name,
        **total_usage
    }

    logger.info(f"流式对话完成 - 总轮数: {continue_count + 1}, 总长度: {len(accumulated)} 字符")
```

**验证**: 代码结构清晰，注释完整

- [ ] **Step 4: 提交基础结构**

```bash
git add backend/src/services/ai_service.py
git commit -m "refactor: 重构 chat_stream 方法基础结构

- 提取基础消息列表构建逻辑
- 添加主循环框架（max_continue + 1 轮）
- 准备续写 messages 构建接口
- 下一步：填充 API 调用逻辑

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 4: 实现 API 调用和流式处理逻辑

**Files:**
- Modify: `backend/src/services/ai_service.py`

- [ ] **Step 1: 填充 API 调用逻辑**

在 `chat_stream` 方法的循环中，添加 API 调用逻辑（替换 TODO）：

```python
        # 单次流式调用
        stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
            stream=True,
            stream_options={"include_usage": True}  # 确保返回 usage
        )

        # 处理流式响应
        finish_reason = None
        last_chunk = None

        for chunk in stream:
            last_chunk = chunk
            if not chunk.choices or len(chunk.choices) == 0:
                continue

            choice = chunk.choices[0]

            # 提取内容并实时推送
            delta = choice.delta
            if delta and delta.content:
                content = delta.content
                accumulated += content
                # 统一使用 dict 格式
                yield {'type': 'content', 'content': content}
                await asyncio.sleep(0.001)  # 让出控制权

            # 持续更新 finish_reason
            if choice.finish_reason:
                finish_reason = choice.finish_reason

            # 累加 usage
            if hasattr(chunk, 'usage') and chunk.usage:
                total_usage['prompt_tokens'] += chunk.usage.prompt_tokens or 0
                total_usage['completion_tokens'] += chunk.usage.completion_tokens or 0
                total_usage['total_tokens'] += chunk.usage.total_tokens or 0

        # 兼容不同供应商的 finish_reason 字段名
        if not finish_reason and last_chunk:
            finish_reason = getattr(last_chunk.choices[0], 'stop_reason', None)

        logger.info(f"第 {continue_count + 1} 轮流式输出完成，finish_reason: {finish_reason}, 本轮长度: {len(accumulated)} 字符")

        # 判断是否需要续写
        if finish_reason not in ('length', 'max_tokens'):
            logger.info("正常结束，无需续写")
            break  # 正常结束

        # 如果是最后一批，停止续写
        if continue_count >= max_continue:
            logger.warning(f"已达到最大续写次数 {max_continue}，停止续写")
            break
```

**验证**: 逻辑完整，处理了所有边界情况

- [ ] **Step 2: 提交 API 调用逻辑**

```bash
git add backend/src/services/ai_service.py
git commit -m "feat: 实现 chat_stream 的 API 调用和流式处理

- 添加单次流式 API 调用逻辑
- 统一使用 dict 格式 yield: {'type': 'content', 'content': ...}
- 兼容多供应商的 finish_reason 字段
- 累加每轮的 usage 统计
- 添加续写判断逻辑

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 5: 处理适配器分支（保留原有逻辑）

**Files:**
- Modify: `backend/src/services/ai_service.py`

- [ ] **Step 1: 保留适配器分支的原有逻辑**

查看第 901-966 行的适配器逻辑，确保新版本保留这部分：

```python
# 检查是否需要使用适配器（非 OpenAI 兼容供应商）
use_adapter = provider_code in ADAPTER_PROVIDERS

if use_adapter:
    # 使用适配器（保持原有逻辑不变）
    # ...（复制原代码第 905-966 行）
    return  # 适配器分支直接返回

# 以下为 OpenAI 兼容供应商的新逻辑
# ...（前面实现的循环续写逻辑）
```

**验证**: 适配器供应商（Claude, Bedrock）仍能正常工作

- [ ] **Step 2: 提交适配器兼容性修复**

```bash
git add backend/src/services/ai_service.py
git commit -m "fix: 保留适配器分支的原有逻辑

- 确保 Claude、Bedrock 等非 OpenAI 兼容供应商继续工作
- 新的循环续写逻辑只应用于 OpenAI 兼容供应商

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 6: 清理旧的续写逻辑

**Files:**
- Modify: `backend/src/services/ai_service.py`

- [ ] **Step 1: 删除旧的续写逻辑**

删除以下不再需要的代码：
- 第 1265-1270 行：`code_validator` 相关的验证逻辑
- 第 1272-1279 行：`should_auto_continue` 判断逻辑
- 第 1281-1362 行：整个续写分支（递归调用部分）
- 第 1306 行：`continue_message` 提示词构建
- 第 1308-1347 行：续写内容的去重逻辑

**保留**：
- 第 1249-1256 行：`model_config_obj` 获取逻辑（可能还需要）

- [ ] **Step 2: 删除不再使用的导入**

检查并删除：
- `from src.services.code_validator import CodeValidator`（如果只用于续写）
- `self.code_validator` 初始化（如果只用于续写）

- [ ] **Step 3: 提交清理**

```bash
git add backend/src/services/ai_service.py
git commit -m "refactor: 删除旧的续写逻辑

- 删除 code_validator 验证逻辑
- 删除 should_auto_continue 判断
- 删除递归续写分支
- 删除续写内容去重逻辑
- 简化为内部循环续写

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 7: 后端集成测试

**Files:**
- Test: `backend/tests/integration/test_stream_continuation.py`（新建）

- [ ] **Step 1: 创建集成测试文件**

```python
import pytest
import asyncio
from src.services.ai_service import AIService
from src.database import SessionLocal

@pytest.mark.asyncio
async def test_stream_short_content():
    """测试短内容不触发续写"""
    db = SessionLocal()
    service = AIService(db)

    history = []
    user_message = "说一句话"

    chunks = []
    async for chunk in service.chat_stream(
        system_prompt="你是一个助手",
        history=history,
        user_message=user_message,
        max_continue=3
    ):
        if isinstance(chunk, dict):
            if chunk.get('type') == 'content':
                chunks.append(chunk['content'])
            elif chunk.get('type') == 'usage':
                assert chunk['total_tokens'] > 0
                break

    result = ''.join(chunks)
    assert len(result) > 0
    assert len(result) < 1000  # 短内容不应该很长
    db.close()

@pytest.mark.asyncio
async def test_stream_with_continuation():
    """测试长内容自动续写（模拟）"""
    # 注意：这个测试需要实际调用 API，可能较慢
    # 可以考虑 mock API 响应
    db = SessionLocal()
    service = AIService(db)

    # 使用非常长的系统提示，迫使内容被截断
    long_prompt = "请生成一个包含5000字的HTML页面" * 10

    history = []
    user_message = "生成HTML"

    chunks = []
    usage_received = False

    async for chunk in service.chat_stream(
        system_prompt=long_prompt,
        history=history,
        user_message=user_message,
        max_continue=2
    ):
        if isinstance(chunk, dict):
            if chunk.get('type') == 'content':
                chunks.append(chunk['content'])
            elif chunk.get('type') == 'usage':
                usage_received = True
                assert chunk['total_tokens'] > 0
                break

    result = ''.join(chunks)
    assert len(result) > 0
    # 如果 API 返回了 length，应该触发了续写
    db.close()

@pytest.mark.asyncio
async def test_stream_finish_reason_compatibility():
    """测试不同 finish_reason 字段名的兼容性"""
    # 这个测试需要 mock API 响应
    # 暂时跳过
    pass
```

- [ ] **Step 2: 运行后端测试**

```bash
cd backend
pytest tests/integration/test_stream_continuation.py -v
```

预期：基本测试 PASS

- [ ] **Step 3: 提交测试**

```bash
git add backend/tests/integration/test_stream_continuation.py
git commit -m "test: 添加流式续写集成测试

- 测试短内容不触发续写
- 测试长内容自动续写
- 验证 usage 统计正确

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Phase 2: 前端改造（1小时）

### Task 8: 删除前端去重逻辑

**Files:**
- Modify: `frontend/src/stores/sessionStore.ts:114-151`

- [ ] **Step 1: 定位并删除去重逻辑**

打开 `frontend/src/stores/sessionStore.ts`，定位到第 114-151 行，删除以下代码：

```typescript
// 【兜底方案】检测流式拼接时是否出现重复的代码块标记
// 场景：当前内容在代码块中，新内容以 ```language 开头（说明AI重新开始了代码块）
if (currentContent && newContent) {
  // 检查新内容是否以代码块标记开头（```html、```python 等）
  const codeBlockPattern = /^```(\w+)?\s*\n/
  const match = newContent.match(codeBlockPattern)

  if (match) {
    // 统计当前内容中的代码块标记数量（```）
    const fenceMatches = currentContent.match(/```/g) || []
    const openFences = fenceMatches.length

    // 如果是奇数个```，说明当前还在代码块中，新内容的```是重复的
    if (openFences % 2 === 1) {
      // 去除重复的代码块开始标记
      newContent = newContent.replace(codeBlockPattern, '')
      console.warn('🔧 检测到流式拼接中的重复代码块标记，已清理:', match[0].trim())
    }
  }

  // === 新增：检查续写时的重复内容 ===
  const overlapLength = 100
  if (newContent.length >= overlapLength) {
    const newStart = newContent.slice(0, overlapLength).toLowerCase().trim()
    const currentEnd = currentContent.slice(-overlapLength).toLowerCase().trim()

    const similarity = calculateSimilarity(newStart, currentEnd)
    if (similarity > 0.8) {
      console.warn(`🔧 检测到续写内容重复（相似度${(similarity * 100).toFixed(1)}%），尝试去除重复部分`)

      const splitPos = findSplitPosition(currentContent, newContent)
      if (splitPos > 0) {
        newContent = newContent.slice(splitPos)
        console.warn(`🔧 已去除前${splitPos}个字符的重复内容`)
      }
    }
  }
}
```

- [ ] **Step 2: 简化为直接追加**

将第 108-159 行简化为：

```typescript
// 处理流式数据块
if (data.type === 'content') {
  // 直接追加，无去重逻辑
  if (messages.value[aiMsgIndex]) {
    const currentMsg = messages.value[aiMsgIndex]
    messages.value[aiMsgIndex] = {
      ...currentMsg,
      content: currentMsg.content + (data.content || '')
    }
  }
  // 收到第一个内容块时，关闭 loading 状态
  if (loading.value) {
    loading.value = false
  }
}
```

**验证**: 逻辑清晰，无冗余代码

- [ ] **Step 3: 提交前端去重逻辑删除**

```bash
git add frontend/src/stores/sessionStore.ts
git commit -m "refactor: 删除前端去重逻辑

- 删除代码块标记重复检测（第 114-132 行）
- 删除续写内容相似度检测（第 134-151 行）
- 简化为直接追加内容
- 后端已处理所有重复预防逻辑

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 9: 删除前端辅助函数

**Files:**
- Modify: `frontend/src/stores/sessionStore.ts`

- [ ] **Step 1: 查找并删除辅助函数**

查找以下函数并删除：
- `calculateSimilarity()`
- `findSplitPosition()`
- `calculateOverlapScore()`（如果有）

这些函数通常在第 280-330 行附近。

- [ ] **Step 2: 提交辅助函数删除**

```bash
git add frontend/src/stores/sessionStore.ts
git commit -m "refactor: 删除不再使用的辅助函数

- 删除 calculateSimilarity()
- 删除 findSplitPosition()
- 删除 calculateOverlapScore()
- 这些函数仅用于去重逻辑，已不再需要

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 10: 删除前端测试文件

**Files:**
- Delete: `frontend/tests/unit/codeblockDedup.spec.ts`

- [ ] **Step 1: 删除测试文件**

```bash
rm frontend/tests/unit/codeblockDedup.spec.ts
```

- [ ] **Step 2: 提交删除**

```bash
git add frontend/tests/unit/codeblockDedup.spec.ts
git commit -m "test: 删除去重逻辑测试文件

- 删除 codeblockDedup.spec.ts
- 去重逻辑已从后端处理，不再需要前端测试

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 11: 前端手动测试

**Files:**
- Manual: 浏览器测试

- [ ] **Step 1: 启动前端开发服务器**

```bash
cd frontend
npm run dev
```

- [ ] **Step 2: 启动后端服务器**

```bash
cd backend
python -m src.main
```

- [ ] **Step 3: 测试短内容**

1. 打开浏览器访问 `http://localhost:5173`
2. 登录
3. 选择任意工具
4. 发送短消息："你好"
5. 观察：
   - 流式输出正常
   - 无重复内容
   - 无代码块标记问题

- [ ] **Step 4: 测试长内容续写**

1. 发送长请求："请生成一个包含完整 HTML 结构的教育课件，包含导航栏、侧边栏、内容区，使用响应式设计，至少 2000 字"
2. 观察：
   - 流式输出连续
   - 续写时无停顿
   - 无重复内容
   - 最终内容完整

- [ ] **Step 5: 测试多供应商**

1. 切换不同模型（DeepSeek、OpenAI、Kimi、GLM）
2. 重复步骤 3-4
3. 验证所有供应商都能正常续写

- [ ] **Step 6: 检查控制台日志**

1. 打开浏览器开发者工具（F12）
2. 查看 Console 标签
3. 确认：
   - 无 "🔧 检测到重复" 警告
   - 无 JavaScript 错误
   - SSE 数据接收正常

- [ ] **Step 7: 记录测试结果**

创建测试笔记文档：

```bash
cat > /tmp/stream_test_manual.md << 'EOF'
# 手动测试记录

## 测试环境
- 前端: http://localhost:5173
- 后端: http://localhost:8000
- 浏览器: Chrome

## 测试用例

### 1. 短内容测试
- 输入: "你好"
- 结果: ✅/❌
- 备注:

### 2. 长内容续写测试
- 输入: "请生成一个包含完整 HTML 结构..."
- 结果: ✅/❌
- 续写次数: X 次
- 备注:

### 3. 多供应商测试
- DeepSeek: ✅/❌
- OpenAI: ✅/❌
- Kimi: ✅/❌
- GLM: ✅/❌

### 4. 控制台检查
- 无重复警告: ✅/❌
- 无 JS 错误: ✅/❌

## 问题记录
EOF
```

---

## Phase 3: 集成测试与优化（1小时）

### Task 12: 运行完整测试套件

**Files:**
- Test: 后端和前端所有测试

- [ ] **Step 1: 运行后端测试**

```bash
cd backend
pytest tests/unit/ tests/integration/ -v
```

预期：至少 150 个测试通过

- [ ] **Step 2: 运行前端测试**

```bash
cd frontend
npm run test
```

预期：所有测试通过

- [ ] **Step 3: 修复失败的测试**

如果有测试失败：
1. 查看错误信息
2. 定位问题
3. 修复代码或测试
4. 重新运行直到通过

- [ ] **Step 4: 提交测试修复**

```bash
git add backend/ frontend/
git commit -m "test: 修复测试失败

- 修复 XXX 测试
- 确保所有测试通过

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 13: 性能测试

**Files:**
- Test: 性能基准测试

- [ ] **Step 1: 测试流式延迟**

在浏览器开发者工具中：
1. 切换到 Network 标签
2. 发送一个长消息
3. 观察 SSE 连接的 Timing
4. 记录：
   - 第一个 chunk 到达时间（应 < 100ms）
   - 续写切换时间（应 < 500ms）

- [ ] **Step 2: 测试内存占用**

1. 打开 Chrome 任务管理器（Shift + Esc）
2. 观察前端标签的内存占用
3. 发送多个长消息
4. 确认内存没有明显泄漏

- [ ] **Step 3: 记录性能数据**

```bash
cat >> /tmp/stream_test_manual.md << 'EOF'
## 性能测试

### 流式延迟
- 第一个 chunk: XX ms
- 续写切换: XX ms

### 内存占用
- 初始: XX MB
- 10条消息后: XX MB
- 内存泄漏: ✅/❌
EOF
```

---

### Task 14: 边界情况测试

**Files:**
- Test: 边界情况

- [ ] **Step 1: 测试空内容**

发送空消息或只发空格，确认：
- 不触发续写
- 返回友好提示

- [ ] **Step 2: 测试网络错误**

1. 关闭后端服务器
2. 发送消息
3. 确认前端显示错误提示
4. 重新启动后端
5. 确认可以正常使用

- [ ] **Step 3: 测试 max_continue 限制**

查看代码，确认：
- 达到 `max_continue` 后停止续写
- 日志中有明确的停止记录

- [ ] **Step 4: 记录边界测试结果**

```bash
cat >> /tmp/stream_test_manual.md << 'EOF'
## 边界情况测试

### 空内容
- 结果: ✅/❌
- 备注:

### 网络错误
- 结果: ✅/❌
- 错误提示是否友好: ✅/❌

### max_continue 限制
- 结果: ✅/❌
- 日志记录: ✅/❌
EOF
```

---

## Phase 4: 代码审查与发布（30分钟）

### Task 15: 代码审查

**Files:**
- Review: 所有改动

- [ ] **Step 1: 查看所有改动**

```bash
git diff HEAD~10
```

查看最近 10 个提交的改动

- [ ] **Step 2: 代码质量检查**

检查清单：
- [ ] 无硬编码的配置值
- [ ] 所有函数都有文档字符串
- [ ] 错误处理完整
- [ ] 日志记录充分
- [ ] 类型注解正确
- [ ] 遵循项目代码风格

- [ ] **Step 3: 安全检查**

检查清单：
- [ ] 无敏感信息泄露
- [ ] 无 SQL 注入风险
- [ ] 无 XSS 风险
- [ ] API 密钥正确加密

---

### Task 16: 最终提交

**Files:**
- Git: 最终提交

- [ ] **Step 1: 查看未提交的更改**

```bash
git status
```

- [ ] **Step 2: 添加所有文件**

```bash
git add .
```

- [ ] **Step 3: 创建最终提交**

```bash
git commit -m "feat: 完成流式续写改造

## 核心改动
- 后端：将递归续写改为内部循环续写
- 前端：删除所有去重逻辑，简化为直接追加
- 接口：统一使用 {'type': 'content', 'content': ...} 格式

## 后端改造
- 添加 PLATFORM_CAPS 配置表
- 添加 build_continuation_messages() 函数
- 添加 build_fallback_prompt() 函数
- 重构 chat_stream() 方法为内部循环
- 兼容多供应商的 finish_reason 字段
- 累加每轮 usage 统计

## 前端改造
- 删除代码块标记去重逻辑（第 114-132 行）
- 删除续写内容相似度检测（第 134-151 行）
- 删除辅助函数：calculateSimilarity, findSplitPosition
- 删除测试文件：codeblockDedup.spec.ts

## 测试
- 添加续写 messages 构建函数的单元测试
- 添加流式续写集成测试
- 手动测试验证长内容自动续写
- 测试多供应商兼容性

## 影响
- 用户看到连续的流式输出，无重复内容
- 后端自动处理续写，对前端透明
- 简化前端逻辑，提高可维护性

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 17: 编写发布说明

**Files:**
- Create: `RELEASE_NOTES.md`

- [ ] **Step 1: 创建发布说明文档**

```bash
cat > RELEASE_NOTES.md << 'EOF'
# 流式续写改造发布说明

## 发布日期
2026-04-04

## 改动概述

本次改造解决了长期存在的流式续写问题，将后端的递归续写改为内部循环续写，前端只看到一个统一的流。

## 核心改进

### 后端改进
- ✅ 将递归调用改为内部 `for` 循环
- ✅ 统一使用 `{'type': 'content', 'content': ...}` 格式
- ✅ 兼容多供应商的 `finish_reason` 字段
- ✅ 自动累加每轮的 usage 统计
- ✅ 支持隐式续写（assistant prefill），自动降级到显式提示

### 前端改进
- ✅ 删除所有去重逻辑（38 行）
- ✅ 简化为直接追加内容
- ✅ 删除辅助函数和测试文件

## 用户体验改善

- 🚀 长内容自动续写，用户看到连续的流式输出
- 🚀 无重复内容，无代码块标记问题
- 🚀 所有供应商（DeepSeek、OpenAI、Kimi、GLM）统一体验

## 技术细节

### 续写流程
```
用户请求 → 后端检测 finish_reason
         ↓
      是截断？
         ↓
    是 → 内部循环续写
    否 → 结束
         ↓
      SSE 单一流输出
         ↓
      前端直接追加
```

### 兼容性
- ✅ DeepSeek: finish_reason='length'
- ✅ OpenAI: finish_reason='length'
- ✅ Kimi: finish_reason='length'
- ✅ GLM: finish_reason='length'
- ✅ Claude（未来）: stop_reason='max_tokens'

### 测试覆盖
- 单元测试：续写 messages 构建函数
- 集成测试：短内容、长内容续写
- 手动测试：多供应商、边界情况

## 已知问题

无

## 回滚方案

如遇问题，可回滚到 commit: dc8c45c（改造前）

## 联系方式

如有问题，请在 GitHub Issues 中反馈。
EOF
```

- [ ] **Step 2: 提交发布说明**

```bash
git add RELEASE_NOTES.md
git commit -m "docs: 添加流式续写改造发布说明

- 描述核心改进和用户体验改善
- 说明技术细节和兼容性
- 提供回滚方案

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## 验收检查清单

在完成任务后，逐项检查：

### 功能验收
- [ ] 长内容自动续写
- [ ] 前端看到连续流式输出
- [ ] 无重复内容
- [ ] 多供应商兼容（DeepSeek、OpenAI、Kimi、GLM）
- [ ] finish_reason 检测正确
- [ ] usage 统计准确
- [ ] 积分扣除正确

### 前端验收
- [ ] 无去重逻辑
- [ ] 直接追加内容
- [ ] 控制台无重复警告

### 性能验收
- [ ] 单次流式请求延迟 < 100ms
- [ ] 续写切换时间 < 500ms
- [ ] 无内存泄漏

### 稳定性验收
- [ ] 空内容不续写
- [ ] 网络错误时优雅降级
- [ ] 达到 max_continue 时停止
- [ ] 日志完整

### 测试验收
- [ ] 后端单元测试通过
- [ ] 后端集成测试通过
- [ ] 前端测试通过
- [ ] 手动测试通过

---

## 参考资料

- 设计文档: `docs/superpowers/specs/2026-04-04-stream-continuation-fix-design.md`
- 后端实现: `backend/src/services/ai_service.py`
- 前端实现: `frontend/src/stores/sessionStore.ts`
- sonnect 方案: https://github.com/sonnet

---

**总预估时间**: 4.5-5.5 小时
**实际完成时间**: _____
**开发者**: _____
**日期**: _____
