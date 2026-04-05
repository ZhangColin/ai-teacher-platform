# AI 工具系统改造方案

## 一、现状分析

### 1.1 多供应商接入 —— 三条路径并存的混乱

当前 `AIService`（ai_service.py，1800+ 行）存在三条并行的调用路径：

| 路径 | 适用供应商 | 实现方式 | 问题 |
|------|-----------|---------|------|
| 适配器路径 | bedrock/claude/anthropic | `BaseLLMAdapter` 子类 | 仅 3 个供应商使用 |
| NewAPI 路径 | newapi | 手写 aiohttp HTTP 请求 | 大量重复代码，约 200 行 |
| OpenAI SDK 路径 | deepseek/kimi/glm/openai 等 | `OpenAI()` 客户端 | 默认路径，但无法处理供应商特殊逻辑 |

**矛盾**：`backend/src/services/llm/` 目录下已有完整的适配器体系（7 个适配器：OpenAI/DeepSeek/Kimi/GLM/Gemini/Doubao/Bedrock），但 `AIService` 只对 bedrock 系列使用适配器，其他供应商仍然直连 OpenAI SDK。适配器体系形同虚设。

**具体问题**：
- `chat_stream()` 方法 400+ 行，充斥 `if provider_code == "newapi"` 分支
- `_get_ai_client()` 对所有非 adapter 供应商统一返回 `OpenAI()` 客户端，无法处理供应商差异
- 供应商特殊配置（如 kimi-k2.5 只支持 temperature=1）用全局字典 `MODEL_SPECIFIC_CONFIG` 硬编码
- newapi 的代码与 OpenAI SDK 路径几乎完全重复，仅 HTTP 客户端不同

### 1.2 自动续写 —— 逻辑脆弱且流式/非流式不统一

当 AI 输出超过 token 上限时（`finish_reason == 'length'`），系统需要自动继续生成并拼接。

**非流式 `chat()` 的续写**（约 150 行）：
- 递归调用自身，将已生成内容作为 assistant 消息放入历史
- 有 HTML 完整性检查（`_check_code_completeness`）、重复检测（`_detect_content_duplication`）、内容清理（`_clean_continue_result`）
- 递归模式导致消息历史不断膨胀，每次续写都把全部已生成内容放入 history

**流式 `chat_stream()` 的续写**（约 60 行）：
- 递归调用自身的流式版本
- 仅有简单的代码块标记清理（去除 \`\`\`html 前缀）
- 没有 HTML 完整性检查、没有重复检测
- 没有内容清理

**共同问题**：
1. **重复检测不可靠**：逐字符比较 + 阈值判断，容易误判
2. **HTML 标签计数太粗糙**：简单统计开闭标签数量，不考虑嵌套结构
3. **续写提示词不稳定**：用中文要求"不要包含 Markdown 代码块标记"，但模型经常不遵守
4. **拼接点可能破坏代码结构**：如截断发生在 `<script>` 标签内的 JavaScript 代码中间
5. **流式续写对用户不透明**：续写期间前端不知道正在发生什么，可能出现长时间无输出

### 1.3 辅助函数过度膨胀

`AIService` 中有 6 个续写相关的辅助方法（`_find_html_end_position`、`_detect_content_duplication`、`_clean_after_html_end`、`_check_code_completeness`、`_clean_continue_result`、以及续写循环本身），都混在主类里，职责不清。

---

## 二、改造目标与整体架构

### 2.1 改造目标

1. **统一供应商接入**：所有供应商通过适配器模式接入，消除 `AIService` 中的供应商分支逻辑
2. **可靠的自动续写**：对 HTML/代码类长内容的截断，实现用户无感的自动拼接，保证代码结构完整
3. **关注点分离**：续写逻辑从 `AIService` 中独立出来，成为可测试的独立模块

### 2.2 目标架构

```
┌─────────────────────────────────────────────────────┐
│                   路由层 (chat.py)                     │
│         处理 HTTP、会话管理、积分、标题生成              │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              AIService (精简版)                        │
│  职责：构建消息、调用适配器、协调续写                    │
│  - chat()/chat_stream() 只做编排                      │
│  - 不包含任何供应商特定逻辑                             │
│  - 不包含 HTML 解析/拼接逻辑                           │
└──────┬────────────────────────┬──────────────────────┘
       │                        │
       ▼                        ▼
┌──────────────┐    ┌───────────────────────┐
│ LLM 适配器层   │    │   ContinuationManager  │
│ (统一接口)     │    │   (自动续写管理器)       │
│              │    │                       │
│ - chat()     │    │ - 检测是否需要续写      │
│ - stream()   │    │ - 构造续写 prompt       │
│ - 返回统一的  │    │ - 智能拼接（去重+修复）  │
│   finish 信号 │    │ - 完整性验证            │
└──────────────┘    └───────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│              各供应商适配器                             │
│  OpenAI / DeepSeek / Kimi / GLM / Bedrock /          │
│  Gemini / Doubao / NewAPI(新增)                       │
│  每个适配器处理自己供应商的特殊逻辑                      │
└─────────────────────────────────────────────────────┘
```

### 2.3 核心设计原则

1. **适配器是唯一的 LLM 调用入口**：`AIService` 不再直接创建 `OpenAI()` 客户端
2. **续写是独立的中间件**：`ContinuationManager` 包装适配器的输出，自动处理续写
3. **供应商差异封装在适配器内**：temperature 限制、特殊 header、不同的 API 格式等
4. **流式和非流式共享续写逻辑**：统一的完整性检查和拼接策略

---

## 三、改造方案 —— 供应商适配器统一化

### 3.1 扩展适配器接口

现有 `BaseLLMAdapter` 接口已经够用，只需补充一点：

```python
# backend/src/services/llm/base_adapter.py
class BaseLLMAdapter(ABC):
    # 现有接口保持不变：
    # - chat() -> (str, Optional[Dict])
    # - chat_stream() -> AsyncGenerator[str | Dict, None]

    # 新增：适配器自我描述
    @property
    def provider_code(self) -> str:
        """返回供应商代码"""
        raise NotImplementedError
```

### 3.2 让所有供应商走适配器

**改动 1**：在 `ADAPTER_REGISTRY`（factory.py）中注册所有供应商，包括新增 newapi：

```python
# backend/src/services/llm/factory.py  新增：
    "newapi": NewAPIAdapter,
```

**改动 2**：新增 `NewAPIAdapter`（backend/src/services/llm/newapi_adapter.py）：
- 将 AIService 中约 200 行 aiohttp 代码提取到此适配器
- 实现 `chat()` 和 `chat_stream()` 接口
- 处理 newapi 特有的 HTTP 兼容性问题

**改动 3**：各适配器的 `chat_stream()` 最终 yield 的 dict 中增加 `'finish_reason'` 字段：
- 值为 `'length'`（被截断）或 `'stop'`（正常结束）
- 这是续写管理器判断是否需要续写的关键依据

### 3.3 重构 AIService 的调用路径

**改造前**（三条路径）：
```
AIService.chat_stream()
  ├─ if provider in ADAPTER_PROVIDERS → adapter.chat_stream()
  ├─ if provider == "newapi" → aiohttp 手写请求
  └─ else → OpenAI().chat.completions.create(stream=True)
```

**改造后**（一条路径）：
```
AIService.chat_stream()
  └─ adapter = self._get_adapter(model_config)
     └─ adapter.chat_stream()
```

新增 `_get_adapter()` 方法替代 `_get_ai_client()`：
- 解析 model_config 或获取默认供应商
- 从数据库读取 api_key、base_url
- 调用 `create_adapter(provider_code, api_key=..., base_url=...)`
- 返回适配器实例

### 3.4 删除的代码

- `AIService._get_ai_client()` / `_get_ai_client_from_env()` —— 被 `_get_adapter()` 替代
- `chat_stream()` 中的 newapi 分支（约 150 行）和 OpenAI SDK 直连分支（约 100 行）
- `chat()` 中的 newapi 分支（约 60 行）
- 全局变量 `ADAPTER_PROVIDERS`、`MODEL_SPECIFIC_CONFIG` —— 移入各适配器内部
- `backend/refactor_continue_logic.py`、`backend/refactor_v2.py` —— 历史遗留脚本

### 3.5 供应商特殊逻辑的归属

| 特殊逻辑 | 当前位置 | 改造后位置 |
|---------|---------|-----------|
| kimi-k2.5 temperature=1 | `MODEL_SPECIFIC_CONFIG` 全局字典 | `KimiAdapter` 内部处理 |
| newapi httpx 不兼容 | AIService 中特判 | `NewAPIAdapter` 用 aiohttp |
| bedrock 非 OpenAI 格式 | 已在 BedrockAdapter 中 | 不变 |
| 流式 usage 信息提取 | AIService 中 3 处重复代码 | 各适配器统一处理 |

---

## 四、改造方案 —— 自动续写（ContinuationManager）

### 4.1 核心思路

将续写逻辑从 `AIService` 中完全剥离，封装为独立的 `ContinuationManager` 类。

关键洞察：**续写本质上是一个"检测-请求-拼接"的循环**，与具体的 LLM 供应商无关。

```
用户请求 → 第1次LLM调用 → finish_reason=='length'?
                                    │
                            ┌───────┴────────┐
                            │ No             │ Yes
                            ▼                ▼
                         返回结果        分析截断点
                                         │
                                         ▼
                                    构造续写prompt
                                         │
                                         ▼
                                    第2次LLM调用
                                         │
                                         ▼
                                    智能拼接（去重+修复）
                                         │
                                         ▼
                                    完整性检查 ──→ 不完整则继续循环
                                         │           (最多 max_continue 次)
                                         ▼
                                      返回结果
```

### 4.2 ContinuationManager 设计

新文件：`backend/src/services/continuation_manager.py`

```python
class ContinuationManager:
    """自动续写管理器 —— 处理 LLM 输出因 token 限制被截断的情况"""

    def __init__(self, max_continue: int = 3):
        self.max_continue = max_continue

    async def chat_with_continuation(
        self, adapter, messages, model, system_prompt, temperature, **kwargs
    ) -> tuple[str, Optional[dict]]:
        """非流式调用，自动续写直到完整"""
        ...

    async def chat_stream_with_continuation(
        self, adapter, messages, model, system_prompt, temperature, **kwargs
    ) -> AsyncGenerator[str | dict, None]:
        """流式调用，自动续写直到完整，对外表现为连续的流"""
        ...
```

### 4.3 智能拼接策略

现有的拼接问题主要出在两个地方：(1) 续写内容与原内容重叠，(2) 截断点破坏代码结构。

**策略 1：基于上下文重叠的去重**

不再用逐字符比较，而是用"锚点匹配"：
- 取原内容最后 200 字符作为"锚点"
- 在续写内容的前 500 字符中搜索锚点的子串匹配
- 找到最长匹配后，从匹配结束位置开始拼接

```python
def _find_overlap(self, original: str, continuation: str) -> int:
    """找到续写内容中与原内容重叠的部分，返回应该跳过的字符数"""
    tail = original[-200:]  # 原内容的尾部
    # 从长到短尝试匹配
    for length in range(min(len(tail), 200), 20, -1):
        anchor = tail[-length:]
        pos = continuation.find(anchor)
        if pos != -1:
            return pos + length  # 跳过重叠部分
    return 0  # 没有重叠
```

**策略 2：续写 prompt 的设计**

不用中文，用英文 + 结构化指令（模型遵从性更好）：

```
The previous response was cut off due to length limits.
Continue EXACTLY from where it stopped. Rules:
1. Output ONLY the continuation content, no explanations
2. Do NOT repeat any content that was already generated
3. Do NOT wrap in markdown code fences (``` )
4. The last 100 characters of the previous response were:
   [插入最后100字符]
5. Continue from that exact point.
```

**策略 3：清理续写内容**

提取 `_clean_continue_result` 中的逻辑，增强为：
- 去除开头的 markdown 代码块标记（```html、```javascript 等）
- 去除开头的对话性文本（"Sure, here is..."、"当然，以下是..."）
- 去除结尾的多余 markdown 闭合标记（```）

### 4.4 完整性检查的改进

将 `_check_code_completeness` 改造为独立的 `ContentValidator`：

```python
class ContentValidator:
    """内容完整性验证器"""

    @staticmethod
    def check_html(content: str) -> ValidationResult:
        """检查 HTML 完整性"""
        ...

    @staticmethod
    def check_code_blocks(content: str) -> ValidationResult:
        """检查代码块（括号匹配等）"""
        ...

    @staticmethod
    def is_complete(content: str) -> bool:
        """综合判断内容是否完整"""
        ...
```

改进点：
- HTML 检查：使用 Python 内置 `html.parser.HTMLParser` 替代简单的标签计数，能正确处理嵌套
- 括号匹配：用栈而非简单计数，能识别字符串内的括号
- 增加"已经完整但末尾有多余内容"的处理（截断到 `</html>` 后面）

### 4.5 流式续写的用户体验

当流式输出中断并需要续写时：
1. 前端不需要任何改动 —— 续写在后端完全透明处理
2. 后端在续写请求期间，可以发送一个轻量的心跳 SSE 事件（`{type: "heartbeat"}`），防止前端超时
3. 续写内容直接追加到流中，前端像收到正常内容一样处理

```python
async def chat_stream_with_continuation(self, adapter, ...):
    accumulated = ""
    finish_reason = None

    # 第一次调用
    async for chunk in adapter.chat_stream(messages, model, ...):
        if isinstance(chunk, dict):
            finish_reason = chunk.get('finish_reason', 'stop')
            yield chunk  # usage info
        else:
            accumulated += chunk
            yield chunk

    # 续写循环
    continue_count = 0
    while finish_reason == 'length' and continue_count < self.max_continue:
        if not self._should_continue(accumulated):
            break

        continue_count += 1
        # 构造续写消息
        continue_messages = messages + [
            {"role": "assistant", "content": accumulated},
            {"role": "user", "content": self._build_continue_prompt(accumulated)}
        ]

        # 发送心跳
        yield {"type": "heartbeat"}

        # 续写调用
        continuation = ""
        async for chunk in adapter.chat_stream(continue_messages, model, ...):
            if isinstance(chunk, dict):
                finish_reason = chunk.get('finish_reason', 'stop')
            else:
                continuation += chunk

        # 智能拼接
        cleaned = self._clean_continuation(continuation)
        overlap = self._find_overlap(accumulated, cleaned)
        new_content = cleaned[overlap:]

        if not new_content.strip():
            break

        accumulated += new_content
        yield new_content  # 把新增内容发送给前端

    # 最终完整性检查 + 修复
    if ContentValidator.needs_repair(accumulated):
        repair = ContentValidator.repair_html(accumulated)
        if repair != accumulated:
            yield repair[len(accumulated):]  # 只发送修复新增的部分
```

### 4.6 异常处理策略

续写过程中可能在任意阶段失败（网络超时、API 限流、模型错误等），需要明确策略：

**原则：已生成的内容不能丢**

```python
class ContinuationManager:
    async def chat_stream_with_continuation(self, adapter, ...):
        accumulated = ""
        total_usage = _empty_usage()

        # 第一次调用 —— 失败直接抛出（没有已生成内容可保留）
        async for chunk in adapter.chat_stream(...):
            if isinstance(chunk, dict):
                finish_reason = chunk.get('finish_reason', 'stop')
                total_usage = _merge_usage(total_usage, chunk)
            else:
                accumulated += chunk
                yield chunk

        # 续写调用 —— 失败时返回已有内容 + 警告
        while finish_reason == 'length' and continue_count < self.max_continue:
            try:
                async for chunk in adapter.chat_stream(continue_messages, ...):
                    ...
            except Exception as e:
                logger.warning(f"续写第 {continue_count} 次失败: {e}，返回已生成内容")
                # 不抛出异常，跳出续写循环，返回已累积的内容
                break

        # 返回累积的 usage 信息
        yield {
            'type': 'usage',
            'finish_reason': finish_reason,
            **total_usage
        }
```

**异常分级**：
| 场景 | 处理方式 |
|------|---------|
| 第一次调用就失败 | 直接抛出异常，由路由层处理 |
| 续写过程中网络超时 | 返回已有内容 + 日志警告，不重试 |
| 续写返回空内容 | 视为"模型认为已完整"，正常结束 |
| 续写内容与原内容完全重复 | 终止续写，返回已有内容 |
| 超过 max_continue 次数 | 终止续写，返回已有内容 + 日志记录 |

### 4.7 积分累加方案

每次续写都是一次独立的 API 调用，产生独立的 token 消耗。ContinuationManager 负责累加：

```python
def _merge_usage(self, total: dict, new: dict) -> dict:
    """累加多次 API 调用的 usage 信息"""
    return {
        'prompt_tokens': total.get('prompt_tokens', 0) + new.get('prompt_tokens', 0),
        'completion_tokens': total.get('completion_tokens', 0) + new.get('completion_tokens', 0),
        'total_tokens': total.get('total_tokens', 0) + new.get('total_tokens', 0),
        'model_provider': new.get('model_provider', total.get('model_provider')),
        'model_name': new.get('model_name', total.get('model_name')),
        'continuation_count': total.get('continuation_count', 0) + 1,
    }
```

**对外返回的 usage 是累加后的总量**，路由层（chat.py）按总量计算积分，无需关心续写了几次。

`continuation_count` 字段记录续写次数，仅用于日志和监控，不影响积分计算。

### 4.8 关键测试用例

| 测试场景 | 验证点 |
|---------|-------|
| 正常短回复（无截断） | 不触发续写，内容正确 |
| 单次续写（finish_reason=length 一次） | 拼接正确，无重叠，usage 累加正确 |
| 多次续写（max_continue=3，需续写 3 次） | 循环正确，最终内容完整 |
| 续写内容开头有 markdown 代码块标记 | 标记被正确清理 |
| 续写内容与原内容重叠 200 字符 | 重叠被检测并去除 |
| HTML 内容截断在 `<script>` 标签内 | 续写后 JS 括号匹配正确 |
| HTML 内容截断但已有 `</html>` | 不触发续写（已完整） |
| 续写第 2 次时网络超时 | 返回前两次的累积内容，不报错 |
| 续写返回空内容 | 正常终止，不死循环 |
| 续写内容完全重复 | 检测到重复后终止 |
| 不同供应商的 finish_reason 格式 | 各适配器正确返回 'length'/'stop' |

### 4.9 从 AIService 中删除的续写代码

以下方法将从 `AIService` 中移除，由 `ContinuationManager` 和 `ContentValidator` 替代：
- `_find_html_end_position()`
- `_detect_content_duplication()`
- `_clean_after_html_end()`
- `_check_code_completeness()`
- `_clean_continue_result()`
- `chat()` 中的续写循环（约 120 行）
- `chat_stream()` 中的续写分支（约 60 行）

---

## 五、实施步骤（按顺序执行）

### 阶段 1：适配器层补全（不动 AIService）

**目标**：确保所有供应商都有可用的适配器，且接口统一。

1. **补充 finish_reason 返回**：修改 `BaseLLMAdapter.chat_stream()` 的约定，在最终的 usage dict 中增加 `finish_reason` 字段。逐个检查现有 7 个适配器，确保都返回该字段。

2. **新增 NewAPIAdapter**：
   - 创建 `backend/src/services/llm/newapi_adapter.py`
   - 从 `AIService.chat_stream()` 中提取 newapi 的 aiohttp 代码
   - 在 factory.py 中注册

3. **验证**：为每个适配器写一个简单的集成测试（可选，视环境而定）。

**改动文件**：
- `backend/src/services/llm/base_adapter.py`（小改）
- `backend/src/services/llm/newapi_adapter.py`（新增）
- `backend/src/services/llm/factory.py`（注册 newapi）
- 各现有适配器文件（补充 finish_reason）

### 阶段 2：续写管理器独立实现（不动 AIService）

**目标**：实现 ContinuationManager 和 ContentValidator，独立可测试。

1. **创建 ContentValidator**：
   - `backend/src/services/content_validator.py`
   - 实现 HTML 完整性检查（用 HTMLParser）
   - 实现括号匹配检查（用栈）
   - 实现 `is_complete()` 综合判断
   - 实现 `repair_html()` 自动补全缺失的闭合标签

2. **创建 ContinuationManager**：
   - `backend/src/services/continuation_manager.py`
   - 实现 `_find_overlap()` 重叠检测
   - 实现 `_build_continue_prompt()` 续写提示词构造
   - 实现 `_clean_continuation()` 内容清理
   - 实现 `_should_continue()` 续写条件判断
   - 实现 `chat_with_continuation()` 非流式续写
   - 实现 `chat_stream_with_continuation()` 流式续写

3. **单元测试**：
   - 测试 ContentValidator 的各种 HTML 片段
   - 测试 ContinuationManager 的重叠检测和内容清理
   - 用 mock adapter 测试续写循环

**改动文件**：
- `backend/src/services/content_validator.py`（新增）
- `backend/src/services/continuation_manager.py`（新增）
- `backend/tests/unit/test_content_validator.py`（新增）
- `backend/tests/unit/test_continuation_manager.py`（新增）

### 阶段 3：重构 AIService（核心改动）

**目标**：将 AIService 从 1800 行精简到约 300 行。

1. **替换 `_get_ai_client()` 为 `_get_adapter()`**：
   - 从数据库读取配置
   - 调用 `create_adapter()` 返回适配器实例
   - 测试环境用环境变量创建适配器

2. **重写 `chat()`**：
   ```python
   async def chat(self, system_prompt, history, user_message,
                  max_continue=3, model_config=None):
       adapter = self._get_adapter(model_config)
       messages = self._build_messages(system_prompt, history, user_message)
       manager = ContinuationManager(max_continue=max_continue)
       return await manager.chat_with_continuation(
           adapter, messages, self._model_name, system_prompt, 0.7
       )
   ```

3. **重写 `chat_stream()`**：
   ```python
   async def chat_stream(self, system_prompt, history, user_message,
                         max_continue=3, model_config=None):
       adapter = self._get_adapter(model_config)
       messages = self._build_messages(system_prompt, history, user_message)
       manager = ContinuationManager(max_continue=max_continue)
       async for chunk in manager.chat_stream_with_continuation(
           adapter, messages, self._model_name, system_prompt, 0.7
       ):
           yield chunk
   ```

4. **删除废弃代码**：
   - 删除所有 6 个续写辅助方法
   - 删除 `_get_ai_client()` / `_get_ai_client_from_env()`
   - 删除 newapi 分支代码
   - 删除 `ADAPTER_PROVIDERS` / `MODEL_SPECIFIC_CONFIG`
   - 保留多模态方法（generate_image/audio/video）不动

**改动文件**：
- `backend/src/services/ai_service.py`（大改，从 1800 行缩减到约 500 行）

### 阶段 4：集成验证

1. **确保路由层不变**：`chat.py` 中的接口调用方式不变（`ai_service.chat_stream()` 的签名不变）
2. **确保前端不变**：SSE 协议不变，前端代码零改动
3. **运行现有测试**：
   ```bash
   cd backend && python3 -m pytest tests/unit/ tests/integration/ -v
   cd frontend && npm run test:e2e -- tests/e2e/chat.spec.ts --project=chromium
   ```
4. **删除历史遗留文件**：
   - `backend/refactor_continue_logic.py`
   - `backend/refactor_v2.py`

### 阶段 5（后续）：多模态适配器化

当前多模态方法（generate_image/audio/video）仅 GLM 供应商使用，与 chat 流程完全独立。
本次重构不动这部分，但为未来扩展预留接口。在本次 4 个阶段全部验证通过后，可独立进行：

1. 在 `BaseLLMAdapter` 中增加可选的多模态接口（提供默认的 `NotImplementedError`）
2. 在 `GLMAdapter` 中实现 `generate_image()` / `generate_audio()` / `generate_video()`
3. 将 `AIService` 中的多模态方法改为委托给适配器

此阶段可在独立 PR 中完成，不影响本次核心改造。

### 分支策略

所有阶段在一个功能分支（如 `refactor/ai-service-unified`）上完成。
**不要每个阶段都合并**，避免中间不兼容状态进入 dev 分支。
验收通过后一次性合并。

---

## 六、文件变更清单

| 文件 | 操作 | 说明 |
|-----|------|------|
| `backend/src/services/llm/base_adapter.py` | 修改 | 增加 provider_code 属性，约定 finish_reason |
| `backend/src/services/llm/newapi_adapter.py` | **新增** | NewAPI 供应商适配器 |
| `backend/src/services/llm/factory.py` | 修改 | 注册 newapi |
| `backend/src/services/llm/openai_adapter.py` | 修改 | 补充 finish_reason 返回 |
| `backend/src/services/llm/deepseek_adapter.py` | 修改 | 补充 finish_reason 返回 |
| `backend/src/services/llm/kimi_adapter.py` | 修改 | 补充 finish_reason + temperature 逻辑 |
| `backend/src/services/llm/glm_adapter.py` | 修改 | 补充 finish_reason 返回 |
| `backend/src/services/llm/bedrock_adapter.py` | 修改 | 补充 finish_reason 返回 |
| `backend/src/services/llm/gemini_adapter.py` | 修改 | 补充 finish_reason 返回 |
| `backend/src/services/llm/doubao_adapter.py` | 修改 | 补充 finish_reason 返回 |
| `backend/src/services/content_validator.py` | **新增** | HTML/代码完整性验证 |
| `backend/src/services/continuation_manager.py` | **新增** | 自动续写管理器 |
| `backend/src/services/ai_service.py` | **大改** | 精简为编排层 |
| `backend/tests/unit/test_content_validator.py` | **新增** | 验证器测试 |
| `backend/tests/unit/test_continuation_manager.py` | **新增** | 续写管理器测试（含异常场景） |
| `backend/tests/integration/test_continuation_e2e.py` | **新增** | 续写集成测试（用 mock adapter） |
| `backend/refactor_continue_logic.py` | **删除** | 历史遗留脚本 |
| `backend/refactor_v2.py` | **删除** | 历史遗留脚本 |

**不变的文件**：
- `backend/src/interfaces/routers/tools/chat.py` —— 路由层不动
- `frontend/src/services/apiClient.ts` —— 前端零改动
- `frontend/src/components/ChatInterface.vue` —— 前端零改动
- `backend/src/services/model_provider_service.py` —— 供应商管理不动
- `backend/src/services/artifact_parser.py` —— 成果物解析不动

---

## 七、风险与注意事项

1. **兼容性风险**：重构 AIService 是核心改动，需要确保 `chat()` 和 `chat_stream()` 的外部签名完全不变
2. **适配器验证**：现有的 7 个适配器可能有未测试的 edge case，特别是流式响应中 finish_reason 的传递
3. **续写 prompt 的模型兼容性**：不同模型对续写指令的遵从度不同，需要实际测试验证
4. **积分准确性**：ContinuationManager 必须累加所有续写调用的 usage，对外返回总量。路由层按总量扣费，不感知续写
5. **测试覆盖**：阶段 1-2 完成后先测适配器和续写器；阶段 3 完成后运行完整回归测试
6. **分支策略**：所有阶段在同一功能分支完成，验收通过后一次合并，避免中间状态
7. **异常容错**：续写失败不能丢失已生成内容，遵循"第一次失败抛异常，续写失败保内容"的原则

---
