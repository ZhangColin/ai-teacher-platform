# 流式续写改造设计文档

**日期**: 2026-04-04
**作者**: Claude
**状态**: 设计中

---

## 问题描述

### 当前问题

后端 `ai_service.py` 的 `chat_stream` 方法在检测到内容被截断时，通过**递归调用自己**来实现续写（第 1313 行）：

```python
async for chunk in self.chat_stream(...):  # ❌ 递归调用
    yield chunk
```

**问题**：
1. 前端收到多个独立的流，而不是一个连续的流
2. 前端需要复杂的去重逻辑（`sessionStore.ts:114-151`）
3. 前后端去重逻辑容易不一致
4. 多次修改仍未彻底解决（commit: dc8c45c, c87cacf, 4c8b61b）

### 目标

**后端内部循环续写，前端只看到一个统一的流**

---

## 设计方案

### 整体架构

```
用户请求 → Python后端 → AI API（流式）
                ↓
         检测 finish_reason
         是截断？→ 后端内部循环续写
         否 → 结束
                ↓
         SSE 推送（单一流）
                ↓
         Vue前端 → 追加渲染（无去重逻辑）
```

### 核心改动

#### 1. 后端：将递归改为内部循环

**改造前（递归调用）**：
```python
async def chat_stream(...):
    # 第一次流式输出
    for chunk in api_stream:
        yield chunk

    # 检测到截断，递归调用
    if finish_reason == 'length':
        async for chunk in self.chat_stream(...):  # ❌ 递归
            yield chunk
```

**改造后（内部循环）**：
```python
async def chat_stream(...):
    base_messages = [system] + history + [user]
    accumulated = ""
    total_usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}

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

        # 单次流式调用
        stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True}
        )

        # 处理流式响应
        current_chunk = ""
        finish_reason = None
        last_chunk = None

        for chunk in stream:
            last_chunk = chunk
            if not chunk.choices:
                continue

            # 提取内容
            delta_content = chunk.choices[0].delta.content or ""
            if delta_content:
                accumulated += delta_content
                current_chunk += delta_content
                # 统一使用 dict 格式，前端按 type 区分
                yield {'type': 'content', 'content': delta_content}

            # 持续更新 finish_reason
            if chunk.choices[0].finish_reason:
                finish_reason = chunk.choices[0].finish_reason

            # 累加 usage
            if hasattr(chunk, 'usage') and chunk.usage:
                total_usage['prompt_tokens'] += chunk.usage.prompt_tokens or 0
                total_usage['completion_tokens'] += chunk.usage.completion_tokens or 0
                total_usage['total_tokens'] += chunk.usage.total_tokens or 0

        # 兼容不同供应商的 finish_reason 字段名
        if not finish_reason and last_chunk:
            finish_reason = getattr(last_chunk.choices[0], 'stop_reason', None)

        # 判断是否需要续写
        if finish_reason not in ('length', 'max_tokens'):
            break  # 正常结束

        # 如果是最后一批，停止续写
        if continue_count >= max_continue:
            break

    # 发送最终的 usage 信息
    yield {'type': 'usage', **total_usage}
```

#### 2. 续写 messages 构建（隐式续写优先）

**位置**: `ai_service.py` 顶部，模块级常量

```python
# 平台能力配置表
PLATFORM_CAPS = {
    "anthropic": {"prefill": True},   # 支持 assistant prefill
    "openai":    {"prefill": False},  # 不支持
    "deepseek":  {"prefill": False},  # 不支持
    "kimi":      {"prefill": False},  # 不支持
    "glm":       {"prefill": False},  # 不支持
}

def build_continuation_messages(
    base_messages: list,
    accumulated: str,
    provider_code: str
) -> list:
    """
    构建续写所需的 messages 列表

    优先使用隐式续写（assistant prefill），不支持时降级到显式提示
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

def build_fallback_prompt(content: str) -> str:
    """
    显式续写的提示词，根据内容类型动态调整
    """
    # 判断是否在代码块中
    in_code_block = content.count("```") % 2 == 1

    if in_code_block:
        return "请继续输出代码，直接从截断处续写，不要输出 ``` 标记，不要重复已有代码。"
    else:
        return "请继续，直接从截断处续写，不要重复已有内容。"
```

#### 3. 前端：删除去重逻辑

**改造前（复杂的去重逻辑）**：
```typescript
// sessionStore.ts:114-151
const codeBlockPattern = /^```(\w+)?\s*\n/
const match = newContent.match(codeBlockPattern)
if (match) {
  const fenceMatches = currentContent.match(/```/g) || []
  const openFences = fenceMatches.length
  if (openFences % 2 === 1) {
    newContent = newContent.replace(codeBlockPattern, '')
  }
}

const similarity = calculateSimilarity(newStart, currentEnd)
if (similarity > 0.8) {
  const splitPos = findSplitPosition(currentContent, newContent)
  if (splitPos > 0) {
    newContent = newContent.slice(splitPos)
  }
}
```

**改造后（简单的追加）**：
```typescript
if (data.type === 'content') {
  if (messages.value[aiMsgIndex]) {
    const currentMsg = messages.value[aiMsgIndex]
    messages.value[aiMsgIndex] = {
      ...currentMsg,
      content: currentMsg.content + (data.content || '')
    }
  }
}
```

---

## 关键技术点

### 1. finish_reason 兼容性

不同供应商的 `finish_reason` 字段名不同：

| 供应商 | 字段名 | 截断值 |
|--------|--------|--------|
| OpenAI/DeepSeek/Kimi | `finish_reason` | `"length"` |
| GLM | `finish_reason` | `"length"` |
| Claude（未来） | `stop_reason` | `"max_tokens"` |

**解决方案**：在循环内持续检测，兼容两种字段名。

### 2. usage 累加

续写会发起多次 API 请求，每轮都有独立的 usage：

```python
total_usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}

for continue_count in range(max_continue + 1):
    stream = client.chat.completions.create(
        ...,
        stream_options={"include_usage": True}  # 确保返回 usage
    )

    for chunk in stream:
        if hasattr(chunk, 'usage') and chunk.usage:
            total_usage['prompt_tokens'] += chunk.usage.prompt_tokens or 0
            total_usage['completion_tokens'] += chunk.usage.completion_tokens or 0
            total_usage['total_tokens'] += chunk.usage.total_tokens or 0
```

### 3. messages 结构避免重复

**错误做法（累积 append）**：
```python
messages.append({"role": "assistant", "content": accumulated})  # ❌ 第一轮
messages.append({"role": "assistant", "content": accumulated})  # ❌ 第二轮，重复了
```

**正确做法（每轮重建）**：
```python
base_messages = [system] + history + [user]

for continue_count in range(max_continue + 1):
    if continue_count == 0:
        messages = base_messages
    else:
        messages = base_messages + [{"role": "assistant", "content": accumulated}]
```

### 4. 隐式续写（assistant prefill）

**原理**：
- 不发送用户提示消息
- 直接把已生成内容作为 `assistant` 消息
- AI 认为自己还在生成同一条消息，自然续写

**优势**：
- 不会产生对话性回复（如"好的，继续如下："）
- 不会重复已生成内容
- 不需要在 prompt 里反复叮嘱

**局限**：
- 不是所有 API 都支持
- OpenAI/DeepSeek/Kimi/GLM 不支持
- Claude 原生支持

**解决方案**：优先尝试隐式续写，不支持时自动降级到显式提示。

---

## 改动范围

### 后端改动

**文件**: `backend/src/services/ai_service.py`

**改动内容**:
1. 添加 `PLATFORM_CAPS` 配置表（约 20 行）
2. 添加 `build_continuation_messages()` 函数（约 30 行）
3. 添加 `build_fallback_prompt()` 函数（约 15 行）
4. 重构 `chat_stream()` 方法（约 100 行改造）
5. 删除 `_single_stream_call()` 方法（如果存在）

**预估行数**: +165 行, -50 行（净增 115 行）

### 前端改动

**文件**: `frontend/src/stores/sessionStore.ts`

**改动内容**:
1. **完全删除**去重逻辑（第 114-151 行，约 38 行）
2. 简化为直接追加（约 5 行）
3. **删除**相关的辅助函数（`calculateSimilarity`, `findSplitPosition`, `calculateOverlapScore`）
4. **删除**测试文件 `frontend/tests/unit/codeblockDedup.spec.ts`

**预估行数**: -38 行, +5 行（净减 33 行）

### 测试文件

**删除**: `frontend/tests/unit/codeblockDedup.spec.ts`（不再需要）

---

## 验收标准

### 功能验收

1. **长内容自动续写**
   - 生成超过 `max_output_tokens` 的内容时，自动续写
   - 前端看到连续的流式输出
   - 无重复内容

2. **多供应商兼容**
   - DeepSeek、OpenAI、Kimi、GLM 都能正确续写
   - finish_reason 检测正确

3. **usage 统计准确**
   - 续写多轮后，usage 累加正确
   - 积分扣除正确

4. **前端简化**
   - 无去重逻辑
   - 直接追加内容

### 性能验收

1. **流式延迟**
   - 单次流式请求延迟 < 100ms
   - 续写切换时间 < 500ms

2. **内存占用**
   - 不保留完整的中间历史
   - 只保留必要的 `accumulated` 内容

### 稳定性验收

1. **边界情况**
   - 空内容不续写
   - 网络错误时中断续写，返回已生成内容（标记 `truncated: True`）
   - API 异常时抛出，由上层处理
   - 达到 `max_continue` 时停止

2. **日志完整**
   - 续写触发时记录日志
   - 每轮 usage 记录日志
   - 错误时记录详细堆栈

---

## 风险与应对

### 风险 1：隐式续写不支持

**风险**: 部分 API 不支持 assistant prefill，续写失败

**应对**: 自动降级到显式提示，配置 `PLATFORM_CAPS` 表

### 风险 2：usage 累加错误

**风险**: 多轮续写后 usage 统计不准确，积分扣除错误

**应对**:
- 每轮都累加 usage
- 添加详细日志验证
- 单元测试覆盖累加逻辑

### 风险 3：messages 结构重复

**风险**: 续写时 messages 重复追加，导致 API 拒绝或异常

**应对**:
- 使用 `base_messages` 每轮重建
- 添加单元测试验证 messages 结构

### 风险 4：前端显示异常

**风险**: 删除去重逻辑后，某些边界情况下出现重复

**应对**:
- 前端不保留任何去重逻辑
- 代码块标记的完整性由 `build_fallback_prompt()` 在后端处理
- 前端只负责追加内容，所有重复预防在后端完成

### 风险 5：异常处理不明确

**风险**: 续写过程中发生网络错误或 API 异常，处理行为不明确

**应对**:
- **单轮错误**：中断续写，把已生成的 `accumulated` 通过 `{'type': 'done', 'truncated': True}` 返回
- **致命错误**：抛出异常，由上层 FastAPI 路由处理，返回 500 错误
- **前端显示**：收到 `truncated: True` 时显示"内容被截断，请重新生成"

---

## 实施计划

### Phase 1: 后端改造（2-3小时）

1. 添加配置表和辅助函数（30分钟）
2. 重构 `chat_stream()` 方法（90分钟）
3. 单元测试（30分钟）

### Phase 2: 前端改造（1小时）

1. 删除去重逻辑（20分钟）
2. 简化追加逻辑（10分钟）
3. 手动测试（30分钟）

### Phase 3: 集成测试（1小时）

1. 测试长内容续写（20分钟）
2. 测试多供应商（20分钟）
3. 测试 usage 统计（10分钟）
4. 压力测试（10分钟）

### Phase 4: 代码审查与发布（30分钟）

1. 代码审查（15分钟）
2. Git 提交（5分钟）
3. 发布说明（10分钟）

**总计**: 4.5-5.5 小时

---

## 参考资料

- [sonnect 的续写方案](https://github.com/sonnet)
- OpenAI API 文档: https://platform.openai.com/docs/api-reference/chat/create
- Anthropic API 文档: https://docs.anthropic.com/claude/reference/messages-streaming
- 当前实现: `backend/src/services/ai_service.py:860-1393`
- 前端实现: `frontend/src/stores/sessionStore.ts:86-209`
- 前端测试: `frontend/tests/unit/codeblockDedup.spec.ts`

---

**变更历史**:
- 2026-04-04: 初始版本
- 2026-04-04: 修正 yield 类型不一致问题；明确 PLATFORM_CAPS 位置；澄清前端去重逻辑删除范围；补充异常处理流程
