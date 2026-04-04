# 流式代码块完整性保障系统设计文档（渐进式增强方案）

**文档版本**: v2.0（渐进式增强）
**创建日期**: 2026-04-04
**最后修改**: 2026-04-04
**作者**: Claude
**状态**: 待批准

---

## 修订历史

| 版本 | 日期 | 修改内容 | 修改人 |
|------|------|----------|--------|
| v1.0 | 2026-04-04 | 初始版本（三层防护架构） | Claude |
| v2.0 | 2026-04-04 | 重新设计为渐进式增强策略 | Claude |

**v2.0变更说明**：根据评审反馈，从"一次性彻底解决"改为"渐进式增强"，降低风险，分阶段实施。

---

## 一、问题定义

### 1.1 核心问题

当AI返回的内容超过单次输出限制时，系统会触发续写机制。在续写时，新的AI返回内容可能在代码块中间开始，导致拼接后的代码块格式错误，使得代码无法执行。

**具体表现**：

1. **代码块标记重复**：续写内容以 ``` 开头，导致出现两个代码块开始标记
2. **代码块被错误截断**：第一次返回在代码块中间截断，续写直接继续，导致代码块不完整
3. **HTML/代码语法错误**：在标签、括号等关键位置截断，导致语法错误

### 1.2 影响范围

- **用户影响**：生成的代码无法复制使用，影响教学效果
- **系统影响**：AI备课平台的核心功能受损，降低了平台的可靠性
- **模型影响**：所有通过OpenAI SDK接入的模型（DeepSeek、Kimi、OpenAI、GLM等）都存在此问题

### 1.3 约束条件

1. **必须模型无关**：方案不能依赖特定模型的API或行为
2. **必须向后兼容**：不能破坏现有的流式输出体验
3. **必须保证正确性**：代码必须100%可执行，不能有妥协
4. **必须可维护**：方案易于理解和维护，不能引入过度复杂的逻辑

---

## 二、解决方案概述

### 2.1 核心策略：渐进式增强

采用**三阶段渐进式增强**策略，逐步验证方案有效性，降低风险：

**第一阶段（立即实施）**：增强现有的代码块标记去重逻辑
- 优化前端已存在的代码块去重逻辑（sessionStore.ts line 114-133）
- 实现后端完整性验证，在续写触发时使用
- 目标：解决80%的代码块问题

**第二阶段（验证后实施）**：实现智能续写优化
- 在续写时，根据完整性验证结果，生成更精确的续写提示词
- 去除续写内容中的重复代码块标记
- 目标：解决15%的复杂场景

**第三阶段（可选）**：评估是否需要前端缓冲
- 收集前两个阶段的数据，评估剩余问题的频率
- 如果问题仍然存在，实现轻量级的前端缓冲
- 目标：解决最后5%的极端场景

### 2.2 设计原则

- **渐进式增强**：分阶段实施，逐步验证，降低风险
- **模型无关**：所有逻辑基于文本内容分析，适用于所有模型
- **最小侵入**：不破坏现有功能，只增强关键环节
- **数据驱动**：基于实际数据决策，是否进入下一阶段

---

## 三、第一阶段：增强现有去重逻辑 + 后端验证（优先级：高）

### 3.1 目标

解决80%的代码块问题，主要是代码块标记重复和明显的截断问题。

### 3.2 方案设计

#### 3.2.1 优化前端代码块去重逻辑

**现状**：`frontend/src/stores/sessionStore.ts` 已有基本的去重逻辑（line 114-133）

**问题**：逻辑不够完善，无法处理所有场景

**优化方案**：

```typescript
// frontend/src/stores/sessionStore.ts

// 修改现有的去重逻辑（line 114-133）
if (currentContent && newContent) {
  // 检查新内容是否以代码块标记开头
  const codeBlockPattern = /^```(\w+)?\s*\n/
  const match = newContent.match(codeBlockPattern)

  if (match) {
    // 统计当前内容中的代码块标记数量（```）
    const fenceMatches = currentContent.match(/```/g) || []
    const openFences = fenceMatches.length

    // 如果是奇数个```，说明当前还在代码块中，新内容的```是重复的
    if (openFences % 2 === 1) {
      newContent = newContent.replace(codeBlockPattern, '')
      console.warn('🔧 检测到流式拼接中的重复代码块标记，已清理:', match[0].trim())
    }
  }

  // === 新增：检查续写时的重复内容 ===
  // 检查新内容的前N个字符是否在当前内容的末尾出现过
  const overlapLength = 100  // 检查前100个字符
  if (newContent.length >= overlapLength) {
    const newStart = newContent.substring(0, overlapLength).toLowerCase().trim()
    const currentEnd = currentContent.substring(-overlapLength).toLowerCase().trim()

    // 如果相似度>80%，认为是重复内容
    const similarity = calculateSimilarity(newStart, currentEnd)
    if (similarity > 0.8) {
      console.warn(`🔧 检测到续写内容重复（相似度${(similarity * 100).toFixed(1)}%），尝试去除重复部分`)

      // 找到最佳分割点
      const splitPos = findSplitPosition(currentContent, newContent)
      if (splitPos > 0) {
        newContent = newContent.substring(splitPos)
        console.warn(`🔧 已去除前${splitPos}个字符的重复内容`)
      }
    }
  }

  // 触发响应式更新
  const currentMsg = messages.value[aiMsgIndex]
  messages.value[aiMsgIndex] = {
    ...currentMsg,
    content: currentMsg.content + newContent
  }
}

// === 新增辅助函数 ===

// 计算两个字符串的相似度（简化版）
function calculateSimilarity(str1: string, str2: string): number {
  const len = Math.min(str1.length, str2.length)
  if (len === 0) return 0

  let sameChars = 0
  for (let i = 0; i < len; i++) {
    if (str1[i] === str2[i]) sameChars++
  }

  return sameChars / len
}

// 找到两个字符串的最佳分割点
function findSplitPosition(current: string, newContent: string): number {
  // 从后往前匹配，找到最长的公共后缀
  const maxCheck = Math.min(200, current.length, newContent.length)

  for (let i = maxCheck; i >= 10; i--) {
    const currentEnd = current.substring(-i).toLowerCase()
    const newStart = newContent.substring(0, i).toLowerCase()

    if (currentEnd === newStart) {
      return i
    }
  }

  return 0
}
```

#### 3.2.2 实现后端完整性验证器

**文件位置**：`backend/src/services/code_validator.py`（新文件）

```python
"""代码完整性验证器 - 验证代码块是否完整"""
import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool                    # 是否有效
    issues: List[str]              # 问题列表
    needs_continue: bool           # 是否需要续写

    def to_dict(self) -> dict:
        return {
            'valid': self.valid,
            'issues': self.issues,
            'needs_continue': self.needs_continue
        }


class CodeValidator:
    """代码验证器 - 验证代码完整性"""

    def __init__(self):
        pass

    def validate_content(self, content: str) -> ValidationResult:
        """
        验证内容完整性

        Args:
            content: 要验证的内容

        Returns:
            ValidationResult: 验证结果
        """
        issues = []

        # 1. 检查Markdown代码块是否闭合
        fence_issues = self.check_fence_blocks(content)
        if fence_issues:
            issues.extend(fence_issues)

        # 2. 检查HTML完整性
        if '<html' in content.lower() or '<div' in content.lower():
            html_issues = self.check_html_completeness(content)
            if html_issues:
                issues.extend(html_issues)

        # 3. 检查括号配对
        bracket_issues = self.check_brackets_balance(content)
        if bracket_issues:
            issues.extend(bracket_issues)

        valid = len(issues) == 0
        needs_continue = not valid  # 如果无效，需要续写

        result = ValidationResult(
            valid=valid,
            issues=issues,
            needs_continue=needs_continue
        )

        if not valid:
            logger.warning(f"内容验证失败: {issues}")
        else:
            logger.info("内容验证通过")

        return result

    def check_fence_blocks(self, content: str) -> List[str]:
        """检查Markdown代码块是否闭合"""
        issues = []

        # 统计```数量
        fence_count = content.count('```')

        if fence_count % 2 != 0:
            issues.append(f"代码块未闭合：```数量为奇数（{fence_count}个）")

        return issues

    def check_html_completeness(self, content: str) -> List[str]:
        """检查HTML完整性"""
        issues = []

        # 使用栈式检查HTML标签配对
        stack = []
        # 匹配开始标签（如 <div>）
        open_tags = re.findall(r'<(\w+)(?:\s[^>]*)?>', content)
        # 匹配结束标签（如 </div>）
        close_tags = re.findall(r'</(\w+)>', content)

        # 简单的栈式配对检查
        tag_stack = []
        for tag in open_tags:
            # 忽略自闭合标签
            if tag in ['br', 'hr', 'img', 'input', 'meta', 'link']:
                continue
            tag_stack.append(tag)

        for tag in close_tags:
            if tag_stack and tag_stack[-1] == tag:
                tag_stack.pop()
            else:
                issues.append(f"HTML标签不匹配: </{tag}>")

        # 检查未闭合的标签
        if tag_stack:
            issues.append(f"未闭合的HTML标签: {', '.join(tag_stack)}")

        return issues

    def check_brackets_balance(self, content: str) -> List[str]:
        """检查括号配对"""
        issues = []

        # 定义括号对
        bracket_pairs = {
            '(': ')',
            '{': '}',
            '[': ']'
        }

        # 检查每种括号
        for open_bracket, close_bracket in bracket_pairs.items():
            open_count = content.count(open_bracket)
            close_count = content.count(close_bracket)

            if open_count > close_count:
                issues.append(f"未闭合的括号 '{open_bracket}': {open_count - close_count}个")
            elif close_count > open_count:
                issues.append(f"多余的闭合括号 '{close_bracket}': {close_count - open_count}个")

        return issues
```

#### 3.2.3 在续写逻辑中集成验证器

**文件位置**：`backend/src/services/ai_service.py`

**修改位置**：`chat_stream` 方法中的续写逻辑（约line 1330-1422）

```python
# 在续写逻辑中使用验证器
async def chat_stream(self, ...):
    # ... 流式输出代码 ...

    # === 续写逻辑 ===
    if accumulated_content and finish_reason == 'length':
        # === 新增：验证当前内容的完整性 ===
        validator = CodeValidator()
        validation = validator.validate_content(accumulated_content)

        if not validation.valid:
            logger.warning(f"内容不完整，触发续写: {validation.issues}")

            # 原有的续写逻辑
            # ...
        else:
            logger.info("内容已完整，无需续写")
```

### 3.3 实施计划

**时间估算**：4-6小时

**任务清单**：
1. [ ] 创建 `backend/src/services/code_validator.py`
2. [ ] 实现 `CodeValidator` 类
3. [ ] 在 `ai_service.py` 中集成验证器
4. [ ] 优化前端代码块去重逻辑
5. [ ] 编写单元测试
6. [ ] 手动测试验证

**验收标准**：
- [ ] 代码块标记重复问题解决
- [ ] 明显的截断问题能够检测并触发续写
- [ ] 用户体验无明显影响
- [ ] 单元测试覆盖率>80%

---

## 四、第二阶段：智能续写优化（优先级：中）

### 4.1 前提条件

第一阶段实施完成并运行1-2周后，收集数据分析效果。

### 4.2 目标

解决15%的复杂场景，主要是续写内容的精确拼接。

### 4.3 方案设计

#### 4.3.1 智能续写提示词生成

根据完整性验证结果，生成更精确的续写提示词：

```python
# 在 ai_service.py 的续写逻辑中
if not validation.valid:
    # 根据验证结果生成续写提示词
    if "代码块未闭合" in str(validation.issues):
        continue_message = "上面的代码块被截断了，请继续完成剩余的代码块。注意：只输出代码内容，不要包含```标记，不要重复已生成的部分。"
    elif "未闭合的HTML标签" in str(validation.issues):
        continue_message = f"上面的HTML代码被截断了，缺少以下标签的闭合: {validation.issues}。请继续完成，注意：只输出HTML代码，不要包含```标记。"
    elif "未闭合的括号" in str(validation.issues):
        continue_message = f"上面的代码被截断了，{validation.issues}。请继续完成代码，注意：只输出代码内容，不要包含```标记。"
    else:
        continue_message = "请继续完成上面的内容，不要重复已生成的部分，不要包含```标记。"

    # 触发续写
    # ...
```

#### 4.3.2 去除续写内容中的重复代码块标记

优化现有的 `_clean_continue_result` 方法：

```python
def _clean_continue_result(self, continue_result: str, is_html: bool = False) -> str:
    """清理自动继续返回的内容，提取纯代码内容"""
    import re

    result = continue_result.strip()

    # 1. 尝试提取Markdown代码块内的内容
    code_block_pattern = re.compile(r'```(?:\w+)?\s*\n(.*?)```', re.DOTALL)
    matches = code_block_pattern.findall(result)
    if matches:
        result = matches[-1].strip()
        logger.info(f"从Markdown代码块中提取内容，原始长度: {len(continue_result)}, 提取后长度: {len(result)}")

    # 2. 清理常见的对话文本
    lines = result.split('\n')
    cleaned_lines = []
    skip_patterns = [
        r'^当然[,，].*',
        r'^这里是.*',
        r'^以下是.*',
        r'^//\s*\.\.\.\s*.*',
        r'^//\s*省略.*',
        r'^#\s*\.\.\.\s*.*',
        r'^#\s*省略.*',
    ]

    for line in lines:
        should_skip = False
        for pattern in skip_patterns:
            if re.match(pattern, line.strip(), re.IGNORECASE):
                should_skip = True
                break
        if not should_skip:
            cleaned_lines.append(line)

    result = '\n'.join(cleaned_lines).strip()

    # 3. 如果是HTML，确保没有残留的Markdown标记
    if is_html:
        result = re.sub(r'^```\s*\w*\s*\n', '', result, flags=re.MULTILINE)
        result = re.sub(r'\n```\s*$', '', result, flags=re.MULTILINE)
        result = result.strip()

    logger.info(f"清理完成，最终内容长度: {len(result)} 字符")
    return result
```

### 4.4 实施计划

**时间估算**：2-3小时

**任务清单**：
1. [ ] 优化续写提示词生成逻辑
2. [ ] 优化 `_clean_continue_result` 方法
3. [ ] 编写单元测试
4. [ ] 手动测试验证

**验收标准**：
- [ ] 续写内容正确拼接
- [ ] 不再出现代码块标记重复
- [ ] 复杂场景能够正确处理

---

## 五、第三阶段：前端缓冲（可选）

### 5.1 前提条件

第二阶段实施完成并运行2-4周后，收集数据评估是否需要实施。

### 5.2 数据收集指标

- **问题频率**：代码块问题仍然发生的频率（目标：<5%）
- **问题类型**：剩余问题的类型分布
- **用户反馈**：用户对代码质量的满意度

### 5.3 决策标准

**需要实施第三阶段的情况**：
- 代码块问题频率仍然>5%
- 用户投诉仍然较多
- 问题类型主要是"边界截断导致的格式错误"

**不需要实施第三阶段的情况**：
- 代码块问题频率<5%
- 用户满意度良好
- 剩余问题主要是AI生成内容本身的问题（非拼接问题）

### 5.4 方案设计（如果需要实施）

采用**轻量级前端缓冲**方案：

1. **延迟渲染策略**：只在安全边界处渲染内容
2. **状态跟踪**：跟踪代码块状态（是否在代码块内）
3. **缓冲时间限制**：最多缓冲500ms，避免影响用户体验

**注意**：这个方案会影响用户体验（短时间的延迟），需要谨慎评估。

---

## 六、测试方案

### 6.1 第一阶段测试

#### 6.1.1 单元测试

```python
# backend/tests/unit/test_code_validator.py
import pytest
from src.services.code_validator import CodeValidator

class TestCodeValidator:

    def test_fence_block_validation(self):
        """测试代码块验证"""
        validator = CodeValidator()

        # 完整的代码块
        result = validator.validate_content('```html\n<div>内容</div>\n```')
        assert result.valid == True

        # 不完整的代码块
        result = validator.validate_content('```html\n<div>内容')
        assert result.valid == False
        assert "代码块未闭合" in str(result.issues)

    def test_html_validation(self):
        """测试HTML验证"""
        validator = CodeValidator()

        # 完整的HTML
        result = validator.validate_content('<div><p>内容</p></div>')
        assert result.valid == True

        # 不完整的HTML
        result = validator.validate_content('<div><p>内容</p>')
        assert result.valid == False
        assert "未闭合的HTML标签" in str(result.issues)
```

#### 6.1.2 集成测试

```python
# backend/tests/integration/test_codeblock_integration.py
import pytest
from src.services.ai_service import AIService

@pytest.mark.asyncio
async def test_continue_with_validation(db_session):
    """测试带验证的续写逻辑"""
    ai_service = AIService(db_session)

    system_prompt = "你是一个HTML生成助手"
    history = []
    user_message = "生成一个完整的HTML页面"

    chunks = []
    async for chunk in ai_service.chat_stream(
        system_prompt=system_prompt,
        history=history,
        user_message=user_message,
        max_continue=2
    ):
        if isinstance(chunk, str):
            chunks.append(chunk)

    full_content = ''.join(chunks)

    # 验证：代码块完整
    assert full_content.count('```') % 2 == 0
    assert '</html>' in full_content
```

### 6.2 手动测试清单

- [ ] 生成代码块 - 验证去重逻辑有效
- [ ] 生成长HTML代码 - 验证续写触发
- [ ] 使用DeepSeek模型 - 验证模型无关性
- [ ] 使用Kimi模型 - 验证模型无关性
- [ ] 使用OpenAI模型 - 验证模型无关性
- [ ] 生成包含多个代码块的内容 - 验证每个代码块都正确
- [ ] 生成JavaScript代码 - 验证括号配对检测
- [ ] 生成Python代码 - 验证代码块完整性

---

## 七、风险与应对

### 7.1 风险识别

| 风险 | 可能性 | 影响 | 应对措施 |
|------|--------|------|----------|
| 第一阶段无法解决问题 | 中 | 高 | 收集数据，分析失败原因，进入第二阶段 |
| 第二阶段效果不明显 | 低 | 中 | 评估是否需要第三阶段 |
| 第三阶段影响用户体验 | 中 | 高 | 谨慎评估，充分测试后再上线 |
| 引入新的bug | 中 | 中 | 完善单元测试，代码审查 |

### 7.2 回滚方案

每个阶段都可以独立回滚：

1. **第一阶段回滚**：
   - 前端：恢复sessionStore.ts的原始逻辑
   - 后端：移除CodeValidator调用

2. **第二阶段回滚**：
   - 恢复原有的续写提示词生成逻辑
   - 恢复原有的_clean_continue_result方法

3. **第三阶段回滚**：
   - 移除前端缓冲逻辑

---

## 八、性能影响评估

### 8.1 第一阶段性能影响

- **前端**：增加相似度计算（O(n)，n=100字符），约0.1-0.2ms
- **后端**：完整性验证（O(n)，n=内容长度），只在续写时执行
- **总影响**：<1%，用户无感知

### 8.2 第二阶段性能影响

- **后端**：续写提示词生成（O(1)）
- **总影响**：<0.1%

### 8.3 第三阶段性能影响（如果实施）

- **前端**：缓冲延迟（最多500ms）
- **总影响**：用户体验可能下降，需要谨慎评估

---

## 九、总结

### 9.1 核心价值

1. **降低风险**：分阶段实施，逐步验证，避免一次性大规模修改
2. **数据驱动**：基于实际数据决策，不盲目实施
3. **易于维护**：每个阶段的逻辑简单清晰
4. **渐进增强**：先解决80%的问题，再处理剩余20%

### 9.2 关键指标

**成功标准**（第一阶段）：
- [ ] 代码块问题率从当前的~30%降低到<5%
- [ ] 用户满意度提升
- [ ] 性能影响<1%

**成功标准**（第二阶段）：
- [ ] 代码块问题率进一步降低到<1%
- [ ] 复杂场景正确处理

**决策标准**（第三阶段）：
- 基于数据决定是否实施

### 9.3 验收标准

**第一阶段验收**：
- [ ] 所有单元测试通过（覆盖率>80%）
- [ ] 集成测试通过
- [ ] 手动测试清单全部通过
- [ ] 性能测试通过（影响<1%）

**第二阶段验收**：
- [ ] 单元测试通过
- [ ] 手动测试通过
- [ ] 数据分析显示问题率<1%

**第三阶段决策**：
- [ ] 收集数据分析
- [ ] 评估用户反馈
- [ ] 决定是否实施

---

**文档结束**
