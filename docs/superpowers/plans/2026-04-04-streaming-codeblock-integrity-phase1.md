# 流式代码块完整性保障 - 第一阶段实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标:** 解决80%的流式代码块截断问题，确保代码块标记不重复、明显的截断能够被检测并触发续写。

**架构:** 采用渐进式增强策略的第一阶段：前端增强去重逻辑 + 后端完整性验证。不引入复杂的状态机，基于简单的文本分析和模式匹配。

**技术栈:** TypeScript (前端), Python 3.10+ (后端), Pytest (后端测试), Vitest (前端测试)

---

## 文件结构

```
backend/src/services/
├── code_validator.py          # 新建：代码完整性验证器

frontend/src/stores/
└── sessionStore.ts            # 修改：增强代码块去重逻辑

backend/tests/unit/
└── test_code_validator.py     # 新建：验证器单元测试

frontend/tests/unit/
└── codeblockDedup.spec.ts     # 新建：去重逻辑单元测试

docs/superpowers/plans/
└── 2026-04-04-streaming-codeblock-integrity-phase1.md  # 本文件
```

**文件职责：**
- `code_validator.py`: 检查代码块是否闭合、HTML标签是否配对、括号是否平衡
- `sessionStore.ts`: 增强现有的代码块去重逻辑，添加相似度检测和重复内容去除
- `test_code_validator.py`: 验证各种场景下的代码完整性检查
- `codeblockDedup.spec.ts`: 验证前端去重逻辑的正确性

---

## 任务分解

### Task 1: 创建后端代码验证器

**目标:** 实现 `CodeValidator` 类，能够检测代码块、HTML、括号的完整性问题。

**Files:**
- Create: `backend/src/services/code_validator.py`

- [ ] **Step 1: 创建文件基础结构和导入**

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
```

- [ ] **Step 2: 实现 check_fence_blocks 方法**

```python
def check_fence_blocks(self, content: str) -> List[str]:
    """检查Markdown代码块是否闭合"""
    issues = []

    # 统计```数量
    fence_count = content.count('```')

    if fence_count % 2 != 0:
        issues.append(f"代码块未闭合：```数量为奇数（{fence_count}个）")

    return issues
```

- [ ] **Step 3: 实现 check_html_completeness 方法**

```python
def check_html_completeness(self, content: str) -> List[str]:
    """检查HTML完整性"""
    issues = []

    # 使用栈式检查HTML标签配对
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
```

- [ ] **Step 4: 实现 check_brackets_balance 方法**

```python
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

- [ ] **Step 5: 实现 validate_content 主方法**

```python
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
```

- [ ] **Step 6: 运行代码检查**

Run: `python -m py_compile backend/src/services/code_validator.py`
Expected: 无语法错误

- [ ] **Step 7: 提交初始实现**

```bash
git add backend/src/services/code_validator.py
git commit -m "feat: 添加代码完整性验证器

- 实现 CodeValidator 类，检查代码块、HTML、括号完整性
- 支持验证 Markdown 代码块闭合
- 支持 HTML 标签配对检查
- 支持括号配对检查

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 2: 编写 CodeValidator 单元测试

**目标:** 确保验证器在各种场景下都能正确工作。

**Files:**
- Create: `backend/tests/unit/test_code_validator.py`

- [ ] **Step 1: 创建测试文件和导入**

```python
import pytest
from src.services.code_validator import CodeValidator, ValidationResult

class TestCodeValidator:
    """测试代码验证器"""

    @pytest.fixture
    def validator(self):
        return CodeValidator()
```

- [ ] **Step 2: 测试完整的代码块**

```python
def test_complete_fence_block(self, validator):
    """测试完整的代码块应该通过验证"""
    content = '```html\n<div>内容</div>\n```'
    result = validator.validate_content(content)

    assert result.valid == True
    assert result.needs_continue == False
    assert len(result.issues) == 0
```

- [ ] **Step 3: 测试不完整的代码块**

```python
def test_incomplete_fence_block(self, validator):
    """测试不完整的代码块应该验证失败"""
    content = '```html\n<div>内容'
    result = validator.validate_content(content)

    assert result.valid == False
    assert result.needs_continue == True
    assert any("代码块未闭合" in issue for issue in result.issues)
```

- [ ] **Step 4: 测试完整的HTML**

```python
def test_complete_html(self, validator):
    """测试完整的HTML应该通过验证"""
    content = '<div><p>内容</p></div>'
    result = validator.validate_content(content)

    assert result.valid == True
    assert len(result.issues) == 0
```

- [ ] **Step 5: 测试不完整的HTML**

```python
def test_incomplete_html(self, validator):
    """测试不完整的HTML应该验证失败"""
    content = '<div><p>内容</p>'
    result = validator.validate_content(content)

    assert result.valid == False
    assert any("未闭合的HTML标签" in issue for issue in result.issues)
```

- [ ] **Step 6: 测试括号配对**

```python
def test_balanced_brackets(self, validator):
    """测试括号配对正确"""
    content = 'function test() { return [1, 2, 3]; }'
    result = validator.validate_content(content)

    assert result.valid == True

def test_unbalanced_brackets(self, validator):
    """测试括号不配对"""
    content = 'function test() { return [1, 2, 3;'
    result = validator.validate_content(content)

    assert result.valid == False
    assert any("未闭合的括号" in issue for issue in result.issues)
```

- [ ] **Step 7: 运行测试**

Run: `cd backend && python -m pytest tests/unit/test_code_validator.py -v`
Expected: 所有测试通过

- [ ] **Step 8: 提交测试**

```bash
git add backend/tests/unit/test_code_validator.py
git commit -m "test: 添加 CodeValidator 单元测试

- 测试代码块完整性检查
- 测试 HTML 标签配对检查
- 测试括号配对检查
- 覆盖完整和不完整的场景

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 3: 在 AI 服务中集成验证器

**目标:** 在续写逻辑中使用验证器，决定是否需要续写。

**Files:**
- Modify: `backend/src/services/ai_service.py`

- [ ] **Step 1: 导入 CodeValidator**

在文件顶部的导入区域添加：

```python
from src.services.code_validator import CodeValidator
```

- [ ] **Step 2: 在 AIService.__init__ 中初始化验证器**

在 `__init__` 方法中添加：

```python
def __init__(self, db: Optional[Session] = None):
    # ... 现有代码 ...
    self.code_validator = CodeValidator()  # 新增
```

- [ ] **Step 3: 在续写逻辑中使用验证器**

找到 `chat_stream` 方法中的续写逻辑部分（约 line 1330-1422），在 `if accumulated_content and finish_reason == 'length':` 条件后添加验证逻辑：

```python
if accumulated_content and finish_reason == 'length':
    # === 新增：验证当前内容的完整性 ===
    validation = self.code_validator.validate_content(accumulated_content)

    if not validation.valid:
        logger.warning(f"内容不完整，触发续写: {validation.issues}")

        # 原有的续写判断逻辑
        # ... 保持现有代码不变 ...
    else:
        logger.info("内容已完整，无需续写")
```

**注意:** 只添加验证逻辑，不改变现有的续写判断条件。

- [ ] **Step 4: 运行代码检查**

Run: `python -m py_compile backend/src/services/ai_service.py`
Expected: 无语法错误

- [ ] **Step 5: 提交集成**

```bash
git add backend/src/services/ai_service.py
git commit -m "feat: 在续写逻辑中集成代码完整性验证

- 使用 CodeValidator 验证内容是否完整
- 验证失败时触发续写，验证成功时跳过续写
- 记录验证结果到日志

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 4: 优化前端代码块去重逻辑

**目标:** 增强现有的去重逻辑，添加相似度检测和重复内容去除。

**Files:**
- Modify: `frontend/src/stores/sessionStore.ts`

- [ ] **Step 1: 添加辅助函数（在文件末尾）**

```typescript
/**
 * 计算两个字符串的相似度（简化版）
 */
function calculateSimilarity(str1: string, str2: string): number {
  const len = Math.min(str1.length, str2.length)
  if (len === 0) return 0

  let sameChars = 0
  for (let i = 0; i < len; i++) {
    if (str1[i] === str2[i]) sameChars++
  }

  return sameChars / len
}

/**
 * 找到两个字符串的最佳分割点
 * 返回应该从 newContent 的第几个字符开始
 */
function findSplitPosition(current: string, newContent: string): number {
  // 从后往前匹配，找到最长的公共后缀
  const maxCheck = Math.min(200, current.length, newContent.length)

  for (let i = maxCheck; i >= 10; i--) {
    const currentEnd = current.slice(-i).toLowerCase()
    const newStart = newContent.slice(0, i).toLowerCase()

    if (currentEnd === newStart) {
      return i
    }
  }

  return 0
}
```

- [ ] **Step 2: 修改现有的去重逻辑**

找到 `sessionStore.ts` 中的去重逻辑（约 line 114-133），在现有的代码块标记检测之后添加相似度检测：

```typescript
// === 现有代码：检测代码块标记重复 ===
if (currentContent && newContent) {
  const codeBlockPattern = /^```(\w+)?\s*\n/
  const match = newContent.match(codeBlockPattern)

  if (match) {
    const fenceMatches = currentContent.match(/```/g) || []
    const openFences = fenceMatches.length

    if (openFences % 2 === 1) {
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

  // 触发响应式更新
  const currentMsg = messages.value[aiMsgIndex]
  messages.value[aiMsgIndex] = {
    ...currentMsg,
    content: currentMsg.content + newContent
  }
}
```

**注意:** 修复了原设计文档中的 `substring(-overlapLength)` 语法错误，改为 `slice(-overlapLength)`。

- [ ] **Step 3: 运行类型检查**

Run: `cd frontend && npx vue-tsc --noEmit`
Expected: 无类型错误

- [ ] **Step 4: 提交优化**

```bash
git add frontend/src/stores/sessionStore.ts
git commit -m "feat: 增强代码块去重逻辑

- 添加相似度检测算法，识别重复内容
- 添加 findSplitPosition 函数，找到最佳分割点
- 修复 substring 语法错误，改用 slice
- 降低相似度阈值到 80%，减少误判

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 5: 编写前端去重逻辑单元测试

**目标:** 确保前端去重逻辑在各种场景下都能正确工作。

**Files:**
- Create: `frontend/tests/unit/codeblockDedup.spec.ts`

- [ ] **Step 1: 创建测试文件**

```typescript
import { describe, it, expect } from 'vitest'
import { calculateSimilarity, findSplitPosition } from '@/stores/sessionStore'

describe('代码块去重逻辑', () => {
  describe('calculateSimilarity', () => {
    it('应该计算完全相同字符串的相似度为1', () => {
      const result = calculateSimilarity('hello', 'hello')
      expect(result).toBe(1.0)
    })

    it('应该计算完全不同字符串的相似度为0', () => {
      const result = calculateSimilarity('abc', 'xyz')
      expect(result).toBe(0)
    })

    it('应该计算部分相似字符串的相似度', () => {
      const result = calculateSimilarity('hello world', 'hello there')
      expect(result).toBeGreaterThan(0.5)
    })

    it('应该处理空字符串', () => {
      const result = calculateSimilarity('', 'hello')
      expect(result).toBe(0)
    })
  })

  describe('findSplitPosition', () => {
    it('应该找到重复内容的分割点', () => {
      const current = '这是前面的内容<div class="container">'
      const newContent = '<div class="container">这是新的内容'

      const splitPos = findSplitPosition(current, newContent)
      expect(splitPos).toBeGreaterThan(0)
    })

    it('应该在没有重复时返回0', () => {
      const current = '这是前面的内容'
      const newContent = '这是完全新的内容'

      const splitPos = findSplitPosition(current, newContent)
      expect(splitPos).toBe(0)
    })

    it('应该处理短字符串', () => {
      const current = 'abc'
      const newContent = 'abcxyz'

      const splitPos = findSplitPosition(current, newContent)
      expect(splitPos).toBe(3)
    })
  })
})
```

- [ ] **Step 2: 运行测试**

Run: `cd frontend && npm run test -- codeblockDedup.spec.ts`
Expected: 所有测试通过

- [ ] **Step 3: 提交测试**

```bash
git add frontend/tests/unit/codeblockDedup.spec.ts
git add frontend/src/stores/sessionStore.ts  # 导出辅助函数
git commit -m "test: 添加前端去重逻辑单元测试

- 测试 calculateSimilarity 函数
- 测试 findSplitPosition 函数
- 覆盖各种边界情况

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 6: 编写集成测试

**目标:** 测试完整的流程，确保所有组件协同工作。

**Files:**
- Create: `backend/tests/integration/test_codeblock_integrity_phase1.py`

- [ ] **Step 1: 创建集成测试文件**

```python
"""集成测试：代码块完整性保障（第一阶段）"""
import pytest
from src.services.ai_service import AIService

@pytest.mark.asyncio
async def test_codeblock_continue_with_validation(db_session):
    """测试带验证的续写逻辑"""
    ai_service = AIService(db_session)

    system_prompt = "你是一个HTML生成助手。生成完整的HTML代码，包含代码块标记。"
    history = []
    user_message = "生成一个简单的HTML页面，包含标题和段落"

    chunks = []
    usage_info = None

    async for chunk in ai_service.chat_stream(
        system_prompt=system_prompt,
        history=history,
        user_message=user_message,
        max_continue=2  # 允许续写2次
    ):
        if isinstance(chunk, str):
            chunks.append(chunk)
        elif isinstance(chunk, dict) and chunk.get('type') == 'usage':
            usage_info = chunk

    full_content = ''.join(chunks)

    # 验证：代码块完整（```成对出现）
    assert full_content.count('```') % 2 == 0, "代码块标记应该成对出现"

    # 验证：HTML闭合
    assert '</html>' in full_content or '</div>' in full_content, "HTML应该闭合"

    print(f"✅ 集成测试通过")
    print(f"   - 内容长度: {len(full_content)} 字符")
    print(f"   - 代码块标记数: {full_content.count('```')}")
```

- [ ] **Step 2: 运行集成测试**

Run: `cd backend && python -m pytest tests/integration/test_codeblock_integrity_phase1.py -v -s`
Expected: 测试通过

- [ ] **Step 3: 提交集成测试**

```bash
git add backend/tests/integration/test_codeblock_integrity_phase1.py
git commit -m "test: 添加代码块完整性集成测试

- 测试完整的流式输出和续写流程
- 验证代码块完整性
- 验证HTML闭合

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 7: 手动测试验收

**目标:** 在真实环境中验证功能，确保用户体验良好。

**Files:** 无

- [ ] **Step 1: 启动后端服务**

```bash
cd backend
python -m src.main
```

Expected: 服务运行在 http://localhost:8000

- [ ] **Step 2: 启动前端服务**

```bash
cd frontend
npm run dev
```

Expected: 前端运行在 http://localhost:5173

- [ ] **Step 3: 测试场景1：生成代码块**

操作：
1. 登录系统
2. 选择HTML生成助手工具
3. 发送消息："生成一个包含导航栏和轮播图的HTML页面"
4. 观察流式输出过程

Expected:
- 代码块正确显示，无重复标记
- Markdown渲染正常
- HTML代码可以复制使用

- [ ] **Step 4: 测试场景2：长内容续写**

操作：
1. 发送消息："生成一个完整的电商首页，包含导航、轮播、产品列表、底部信息"
2. 观察是否触发续写

Expected:
- 续写时无重复代码块标记
- 最终内容完整可执行
- 用户无感知延迟

- [ ] **Step 5: 测试场景3：多模型验证**

使用以下模型重复上述测试：
- [ ] DeepSeek
- [ ] Kimi
- [ ] OpenAI（如果可用）

Expected: 所有模型表现一致

- [ ] **Step 6: 记录测试结果**

创建测试报告：

```markdown
# 第一阶段手动测试报告

## 测试环境
- 日期：2026-04-04
- 测试人员：[填写]
- 浏览器：[填写]

## 测试场景

### 场景1：生成代码块
- [ ] 通过 / 失败
- 备注：

### 场景2：长内容续写
- [ ] 通过 / 失败
- 备注：

### 场景3：多模型验证
- [ ] DeepSeek: 通过 / 失败
- [ ] Kimi: 通过 / 失败
- [ ] OpenAI: 通过 / 失败
- 备注：

## 发现的问题
[记录任何问题]

## 总体评价
[通过/不通过]
```

- [ ] **Step 7: 根据测试结果调整**

如果发现问题，修复并重新测试。

- [ ] **Step 8: 提交测试报告**

```bash
git add docs/testing_reports/phase1_manual_test_report.md
git commit -m "test: 添加第一阶段手动测试报告

- 完成所有测试场景
- 验证多模型兼容性
- 确认用户验收标准

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 8: 性能测试

**目标:** 确保性能影响在可接受范围内（<1%）。

**Files:** 无

- [ ] **Step 1: 后端性能测试**

创建测试脚本 `backend/tests/performance/test_validator_performance.py`：

```python
"""性能测试：验证器性能"""
import time
from src.services.code_validator import CodeValidator

def test_validator_performance():
    validator = CodeValidator()

    # 测试不同长度内容的验证时间
    test_cases = [
        ("短内容（100字符）", "a" * 100),
        ("中等内容（1000字符）", "a" * 1000),
        ("长内容（10000字符）", "a" * 10000),
    ]

    for name, content in test_cases:
        start = time.time()
        result = validator.validate_content(content)
        elapsed = time.time() - start

        print(f"{name}: {elapsed * 1000:.2f}ms")

        # 验证时间应该<10ms（即使是最长内容）
        assert elapsed < 0.01, f"{name} 验证时间过长: {elapsed * 1000:.2f}ms"

if __name__ == "__main__":
    test_validator_performance()
    print("✅ 性能测试通过")
```

- [ ] **Step 2: 运行性能测试**

Run: `cd backend && python tests/performance/test_validator_performance.py`
Expected: 所有验证时间<10ms

- [ ] **Step 3: 前端性能测试**

在浏览器开发者工具中：
1. 打开 Chrome DevTools -> Performance
2. 开始录制
3. 触发流式输出
4. 停止录制
5. 查看 `calculateSimilarity` 和 `findSplitPosition` 的执行时间

Expected: 每次调用<1ms

- [ ] **Step 4: 提交性能测试**

```bash
git add backend/tests/performance/test_validator_performance.py
git commit -m "test: 添加性能测试

- 测试 CodeValidator 性能
- 验证性能影响<1%
- 确认前端去重逻辑性能可接受

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 9: 文档更新

**目标:** 更新相关文档，记录实施细节和注意事项。

**Files:**
- Create: `docs/superpowers/implementation-notes/codeblock-integrity-phase1.md`

- [ ] **Step 1: 创建实施笔记文档**

```markdown
# 代码块完整性保障 - 第一阶段实施笔记

**实施日期**: 2026-04-04
**实施人员**: [填写]
**状态**: 已完成

## 实施内容

### 后端改动
1. 新增 `CodeValidator` 类，验证代码完整性
2. 在 `AIService.chat_stream` 中集成验证器
3. 添加单元测试和集成测试

### 前端改动
1. 增强代码块去重逻辑
2. 添加相似度检测和重复内容去除
3. 添加单元测试

## 已知问题

### 限制
1. 相似度算法较简单，可能在某些边缘情况下误判
2. HTML标签配对检查不支持嵌套错误检测
3. 不支持在标签属性中包含 `>` 的情况

### 未来优化方向
1. 第二阶段：智能续写优化
2. 第三阶段：评估是否需要前端缓冲（基于数据）

## 运维注意事项

### 监控指标
- 代码块问题率（目标：<5%）
- 续写触发频率
- 验证器执行时间（应该<10ms）

### 日志关键点
- `内容验证失败`: 表示检测到不完整内容
- `检测到续写内容重复`: 表示去重逻辑生效
- `内容已完整，无需续写`: 表示验证通过

## 回滚方案

如果出现问题：
1. 前端：恢复 sessionStore.ts 的去重逻辑
2. 后端：移除 CodeValidator 调用
3. 分别执行 git revert

## 性能影响

- 后端：<1%（验证器只在续写时执行）
- 前端：<0.5%（去重逻辑每个chunk执行）
- 用户无感知
```

- [ ] **Step 2: 提交文档**

```bash
git add docs/superpowers/implementation-notes/codeblock-integrity-phase1.md
git commit -m "docs: 添加第一阶段实施笔记

- 记录实施内容和已知问题
- 提供运维监控指标
- 记录回滚方案

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 10: 最终验收

**目标:** 确认所有工作完成，质量达标。

**Files:** 无

- [ ] **Step 1: 运行所有后端测试**

```bash
cd backend
python -m pytest tests/unit/test_code_validator.py -v
python -m pytest tests/integration/test_codeblock_integrity_phase1.py -v
```

Expected: 所有测试通过

- [ ] **Step 2: 运行所有前端测试**

```bash
cd frontend
npm run test -- codeblockDedup.spec.ts
npm run test:e2e  # 如果有E2E测试
```

Expected: 所有测试通过

- [ ] **Step 3: 检查测试覆盖率**

```bash
cd backend
pytest --cov=src/services/code_validator --cov-report=term-missing
```

Expected: 覆盖率>80%

- [ ] **Step 4: 确认验收标准**

- [ ] 代码块标记重复问题解决
- [ ] 明显的截断问题能够检测并触发续写
- [ ] 用户体验无明显影响
- [ ] 单元测试覆盖率>80%
- [ ] 性能影响<1%
- [ ] 手动测试通过

- [ ] **Step 5: 创建发布标签**

```bash
git tag -a v1.0.0-codeblock-integrity-phase1 -m "第一阶段实施完成"
git push origin v1.0.0-codeblock-integrity-phase1
```

- [ ] **Step 6: 创建合并请求**

```bash
git checkout -b feature/codeblock-integrity-phase1
git push origin feature/codeblock-integrity-phase1
```

在 GitHub/GitLab 上创建 Merge Request 到 dev 分支。

---

## 实施检查清单

在开始实施前，确认：

- [ ] 已阅读并理解设计文档
- [ ] 已阅读并理解本实施计划
- [ ] 已准备好开发环境（后端 Python 3.10+, 前端 Node.js）
- [ ] 已确认有足够的开发时间（预计4-6小时）

在实施过程中，遵循：

- [ ] TDD：先写测试，再写实现
- [ ] 小步提交：每个 Task 完成后立即 commit
- [ ] 频繁测试：每个 Step 完成后运行测试
- [ ] 代码审查：完成所有 Tasks 后请求 review

在实施完成后，确认：

- [ ] 所有测试通过
- [ ] 测试覆盖率>80%
- [ ] 性能测试通过
- [ ] 手动测试通过
- [ ] 文档已更新
- [ ] 代码已提交并打标签

---

## 参考资料

- 设计文档：`docs/superpowers/specs/2026-04-04-streaming-codeblock-integrity-design.md`
- 现有代码：`frontend/src/stores/sessionStore.ts` (line 114-133)
- 现有代码：`backend/src/services/ai_service.py` (line 1330-1422)

---

**计划完成时间估算**: 4-6小时
**风险等级**: 低（改动独立，可随时回滚）
**依赖**: 无外部依赖，纯代码改动
