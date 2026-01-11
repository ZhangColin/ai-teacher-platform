# 长文本自动继续生成 - 问题分析与解决方案

## 问题分析

### 1. 核心问题

当 LLM 生成长文本（如 HTML 代码）时，如果达到 token 限制（`finish_reason == 'length'`），代码可能在任意位置截断：

- **HTML 标签中间**：`<div class="container"`（缺少闭合 `>`）
- **JavaScript 函数中间**：`function generate() { const x =`（函数未完成）
- **字符串中间**：`const msg = "Hello wor`（字符串未闭合）
- **代码块中间**：Markdown 代码块标记 ` ```html` 后内容被截断

### 2. 当前方案的问题

**简单拼接策略的缺陷**：

1. **不知道断在哪里**：无法判断代码在哪个位置截断
2. **AI 继续时的行为不可控**：
   - 可能重新生成 Markdown 代码块标记（````html`）
   - 可能添加对话文本（"当然,这里是完成的HTML代码:"）
   - 可能添加注释（`// ... 省略已生成部分 ...`）
   - 可能从错误位置继续（重新开始函数，而不是继续未完成的）
   - 可能重复部分内容
3. **代码结构不完整**：即使清理了 Markdown 标记，代码本身可能仍然不完整（标签未闭合、函数未完成等）

### 3. 行业标准做法

根据研究，行业内处理长文本截断的标准做法：

1. **状态管理**：保存截断时的状态，从最后有效状态继续
2. **结构化输出框架**：使用 FSM（有限状态机）确保结构完整
3. **代码块提取**：提取代码块内容，而不是直接拼接原始响应
4. **智能继续提示**：让模型知道从哪里继续，而不是重新开始

## 完整解决方案

### 方案架构

```
检测截断 → 分析截断位置 → 智能继续提示 → 提取代码内容 → 验证完整性 → 后处理修复
```

### 1. 代码完整性检测

#### 1.1 HTML 结构检测

```python
def check_html_integrity(html_content: str) -> dict:
    """
    检测 HTML 代码的完整性
    
    Returns:
        {
            'is_complete': bool,
            'missing_tags': list,  # 缺失的闭合标签
            'truncated_at': str,   # 截断位置类型
            'last_valid_position': int  # 最后一个完整位置
        }
    """
    # 检测标签匹配
    # 检测字符串是否完整
    # 检测注释是否完整
    # 返回完整性报告
```

#### 1.2 JavaScript 代码检测

```python
def check_javascript_integrity(js_content: str) -> dict:
    """
    检测 JavaScript 代码的完整性
    
    Returns:
        {
            'is_complete': bool,
            'unclosed_braces': int,  # 未闭合的大括号
            'unclosed_strings': list,  # 未闭合的字符串
            'incomplete_functions': list  # 未完成的函数
        }
    """
```

### 2. 智能继续策略

#### 2.1 截断位置分析

```python
def analyze_truncation_point(content: str, content_type: str) -> dict:
    """
    分析代码在哪个位置截断
    
    Args:
        content: 已生成的内容
        content_type: 'html', 'javascript', 'mixed'
    
    Returns:
        {
            'truncated_at': str,  # 'tag', 'function', 'string', 'comment', 'unknown'
            'context': str,  # 截断位置的上下文（最后 N 行）
            'expected_continuation': str  # 期望的继续内容类型
        }
    """
```

#### 2.2 智能继续提示词生成

```python
def generate_continue_prompt(
    truncated_content: str,
    truncation_analysis: dict,
    content_type: str
) -> str:
    """
    根据截断分析生成精确的继续提示词
    
    策略：
    1. 如果 HTML 标签未闭合：提示继续完成标签
    2. 如果 JavaScript 函数未完成：提示继续完成函数
    3. 如果字符串未闭合：提示继续完成字符串
    4. 提供截断位置的上下文，让 AI 知道从哪里继续
    """
```

### 3. 内容清理与提取

#### 3.1 Markdown 代码块提取

```python
def extract_code_from_markdown(content: str) -> str:
    """
    从 Markdown 响应中提取代码内容
    
    处理情况：
    1. 单个代码块：```html ... ```
    2. 多个代码块：提取最后一个
    3. 混合内容：提取代码块，忽略对话文本
    4. 无代码块：返回原始内容（可能是纯代码）
    """
```

#### 3.2 对话文本清理

```python
def clean_dialogue_text(content: str) -> str:
    """
    清理 AI 添加的对话文本和注释
    
    移除：
    - "当然,这里是完成的HTML代码:"
    - "// ... 省略已生成部分 ..."
    - "# ... 省略 ..."
    - 其他常见的对话模式
    """
```

### 4. 重复内容检测与处理

```python
def detect_and_remove_overlap(original: str, continuation: str) -> str:
    """
    检测并去除重复内容
    
    策略：
    1. 比较原始结尾和继续开头的相似度
    2. 如果相似度超过阈值，去除重复部分
    3. 使用更智能的匹配算法（不仅仅是字符串相等）
    """
```

### 5. 后处理验证与修复

```python
def validate_and_fix_code(content: str, content_type: str) -> tuple[str, bool]:
    """
    验证代码完整性，如果不完整则尝试修复
    
    Returns:
        (fixed_content, is_complete)
    
    修复策略：
    1. 自动闭合未闭合的 HTML 标签（如果可能）
    2. 检测并报告无法自动修复的问题
    3. 如果无法修复，返回 False，触发再次继续
    """
```

## 实施计划

### 阶段 1：基础检测（当前）

- [x] 检测 `finish_reason == 'length'`
- [x] 基本的继续逻辑
- [x] Markdown 代码块提取
- [x] 对话文本清理

### 阶段 2：完整性检测

- [ ] HTML 标签匹配检测
- [ ] JavaScript 括号/字符串检测
- [ ] 截断位置分析

### 阶段 3：智能继续

- [ ] 根据截断位置生成精确提示词
- [ ] 提供上下文信息
- [ ] 改进继续策略

### 阶段 4：后处理验证

- [ ] 代码完整性验证
- [ ] 自动修复（如果可能）
- [ ] 多次继续（如果仍然不完整）

## 参考资源

1. **OpenAI API 文档**：`finish_reason` 字段说明
2. **Outlines 库**：结构化输出框架，使用 FSM 管理状态
3. **Kimi/DeepSeek 实践**：观察这些平台如何处理长文本继续

## 注意事项

1. **不要过度修复**：如果代码结构严重破坏，应该重新生成，而不是强行修复
2. **保持简单**：复杂的修复逻辑可能引入新问题
3. **用户可见性**：如果自动继续失败，应该向用户报告，而不是静默失败
4. **性能考虑**：完整性检测不应该太耗时
