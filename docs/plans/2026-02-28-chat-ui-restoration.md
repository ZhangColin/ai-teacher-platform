# AI 聊天界面功能恢复实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 恢复重构中被删除的 AI 聊天界面功能和样式，同时保持模块化架构的可维护性

**架构原则：**
- 保持组件分离：ChatPanel → MessageList + MessageItem + ChatInput
- 保持模块化：PreviewPanel → MarkdownPreview + HtmlPreview + SvgPreview + PreviewToolbar
- 功能增强而非回退：通过增强子组件功能实现，不是合并回大组件
- 样式集中管理：提取公共样式到独立 CSS 文件

**技术栈：**
- Vue 3 Composition API + TypeScript
- Vitest (单元测试) + Playwright (E2E测试)
- Tailwind CSS + 自定义样式
- html2pdf.js (PDF生成)

**质量保障：**
- TDD 方法：每个功能先写测试，再实现
- 每个任务后运行全量测试
- 代码审查清单
- 频繁提交（每个功能点一次提交）

---

## 前置准备

### 验证测试基础设施

**Step 1: 确认测试环境正常**

运行前端测试：
```bash
cd frontend
npm run test
```

预期输出：所有现有测试通过
预期测试数量：~20+ 测试用例

运行后端测试：
```bash
cd backend
pytest
```

预期输出：所有现有测试通过

**Step 2: 创建功能分支**

```bash
cd frontend
git checkout -b feature/restore-chat-ui
```

**Step 3: 确认后端 API 可用**

```bash
curl -X POST http://localhost:8000/api/v1/convert/markdown-to-word \
  -H "Content-Type: application/json" \
  -d '{"markdown": "test"}'
```

预期输出：401 Unauthorized（需要认证）或成功返回文件流
这说明 API 端点存在

---

## 阶段 1: 恢复消息复制功能

### Task 1: 创建复制功能组合式函数

**原则：** 创建可复用的组合式函数，而不是在组件中实现逻辑

**Files:**
- Create: `frontend/src/composables/useClipboard.ts`
- Test: `frontend/tests/unit/composables/useClipboard.spec.ts`

**Step 1: 编写失败测试**

创建 `frontend/tests/unit/composables/useClipboard.spec.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useClipboard } from '@/composables/useClipboard'

describe('useClipboard', () => {
  beforeEach(() => {
    vi.stubGlobal('navigator', {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined)
      }
    })
  })

  it('should copy text to clipboard', async () => {
    const { copy, copiedText } = useClipboard()

    await copy('test message')

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('test message')
    expect(copiedText.value).toBe('test message')
  })

  it('should show success toast', async () => {
    const { copy, showSuccessToast } = useClipboard()

    await copy('test')

    expect(showSuccessToast.value).toBe(true)
    setTimeout(() => {
      expect(showSuccessToast.value).toBe(false)
    }, 2100)
  })
})
```

**Step 2: 运行测试确认失败**

```bash
cd frontend
npm run test -- useClipboard.spec.ts
```

预期输出：FAIL - "Cannot find module '@/composables/useClipboard'"

**Step 3: 实现最小化功能**

创建 `frontend/src/composables/useClipboard.ts`:

```typescript
import { ref } from 'vue'

export function useClipboard() {
  const copiedText = ref<string>('')
  const showSuccessToast = ref(false)

  async function copy(text: string): Promise<boolean> {
    try {
      await navigator.clipboard.writeText(text)
      copiedText.value = text
      showSuccessToast.value = true

      setTimeout(() => {
        showSuccessToast.value = false
      }, 2000)

      return true
    } catch (error) {
      console.error('复制失败:', error)
      return false
    }
  }

  return {
    copy,
    copiedText,
    showSuccessToast
  }
}
```

**Step 4: 运行测试确认通过**

```bash
npm run test -- useClipboard.spec.ts
```

预期输出：PASS

**Step 5: 运行全量测试**

```bash
npm run test
```

预期输出：所有测试通过

**Step 6: 提交代码**

```bash
git add frontend/src/composables/useClipboard.ts frontend/tests/unit/composables/useClipboard.spec.ts
git commit -m "feat(composables): add useClipboard composable

- 添加剪贴板复制功能
- 包含成功提示自动消失逻辑
- 支持错误处理"
```

---

### Task 2: 在 MessageItem 组件中集成复制功能

**原则：** 增强 MessageItem 组件功能，添加复制按钮

**Files:**
- Modify: `frontend/src/components/MessageItem.vue`
- Modify: `frontend/tests/unit/components/MessageItem.spec.ts`

**Step 1: 编写失败测试**

在 `frontend/tests/unit/components/MessageItem.spec.ts` 中添加:

```typescript
it('should show copy button on hover', async () => {
  const wrapper = mount(MessageItem, {
    props: {
      message: {
        role: 'user',
        content: 'test message'
      }
    }
  })

  expect(wrapper.find('.copy-button').exists()).toBe(false)

  await wrapper.trigger('mouseenter')

  expect(wrapper.find('.copy-button').exists()).toBe(true)
})

it('should copy message content when copy button clicked', async () => {
  const { copy } = useClipboard()
  const copySpy = vi.spyOn({ copy }, 'copy')

  const wrapper = mount(MessageItem, {
    props: {
      message: {
        role: 'user',
        content: 'test message'
      }
    }
  })

  await wrapper.trigger('mouseenter')
  await wrapper.find('.copy-button').trigger('click')

  expect(copySpy).toHaveBeenCalledWith('test message')
})
```

**Step 2: 运行测试确认失败**

```bash
npm run test -- MessageItem.spec.ts
```

预期输出：FAIL - 找不到复制按钮

**Step 3: 实现 MessageItem 复制功能**

读取当前的 `frontend/src/components/MessageItem.vue`:

```bash
cat frontend/src/components/MessageItem.vue
```

然后在 `<template>` 中添加复制按钮，在 `<script>` 中集成 useClipboard：

```vue
<template>
  <div
    class="message-item"
    :class="message.role"
    @mouseenter="showToolbar = true"
    @mouseleave="showToolbar = false"
  >
    <!-- 现有的消息内容 -->

    <Transition name="fade">
      <div v-if="showToolbar" class="message-toolbar">
        <button
          class="copy-button"
          @click="handleCopy"
          title="复制"
        >
          <DocumentDuplicateIcon />
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { DocumentDuplicateIcon } from '@heroicons/vue/24/outline'
import { useClipboard } from '@/composables/useClipboard'

const props = defineProps<{
  message: {
    role: 'user' | 'assistant'
    content: string
  }
}>()

const showToolbar = ref(false)
const { copy } = useClipboard()

async function handleCopy() {
  await copy(props.message.content)
}
</script>

<style scoped>
.message-item {
  position: relative;
}

.message-toolbar {
  position: absolute;
  top: -30px;
  right: 0;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-item:hover .message-toolbar {
  opacity: 1;
}

.copy-button {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.copy-button:hover {
  background: rgba(0, 0, 0, 0.9);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
```

**Step 4: 运行测试确认通过**

```bash
npm run test -- MessageItem.spec.ts
```

预期输出：PASS

**Step 5: 运行全量测试**

```bash
npm run test
```

预期输出：所有测试通过

**Step 6: 手动验证**

启动开发服务器：
```bash
npm run dev
```

访问 http://localhost:5173，打开聊天界面，验证：
- 鼠标悬停在消息上时显示复制按钮
- 点击复制按钮后可以粘贴文本
- 复制按钮样式正确

**Step 7: 代码审查清单**

- [ ] 复制功能使用组合式函数实现，没有直接在组件中写逻辑
- [ ] 组件保持单一职责，只负责显示和触发复制
- [ ] 样式使用 scoped，不影响其他组件
- [ ] 添加了 hover 效果和过渡动画
- [ ] 测试覆盖了复制功能和按钮显示逻辑

**Step 8: 提交代码**

```bash
git add frontend/src/components/MessageItem.vue frontend/tests/unit/components/MessageItem.spec.ts
git commit -m "feat(message): add copy button to MessageItem

- 鼠标悬停时显示复制按钮
- 集成 useClipboard 组合式函数
- 添加淡入淡出动画
- 保持组件单一职责"
```

---

### Task 3: 添加全局复制成功 Toast 提示

**Files:**
- Create: `frontend/src/components/ToastNotification.vue`
- Modify: `frontend/src/App.vue`
- Test: `frontend/tests/unit/components/ToastNotification.spec.ts`

**Step 1: 编写失败测试**

创建 `frontend/tests/unit/components/ToastNotification.spec.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ToastNotification from '@/components/ToastNotification.vue'

describe('ToastNotification', () => {
  it('should show toast message', () => {
    const wrapper = mount(ToastNotification, {
      props: {
        show: true,
        message: '已复制到剪贴板'
      }
    })

    expect(wrapper.text()).toContain('已复制到剪贴板')
    expect(wrapper.isVisible()).toBe(true)
  })

  it('should not show toast when show is false', () => {
    const wrapper = mount(ToastNotification, {
      props: {
        show: false,
        message: '已复制到剪贴板'
      }
    })

    expect(wrapper.isVisible()).toBe(false)
  })
})
```

**Step 2: 运行测试确认失败**

```bash
npm run test -- ToastNotification.spec.ts
```

预期输出：FAIL - 找不到组件

**Step 3: 实现 Toast 组件**

创建 `frontend/src/components/ToastNotification.vue`:

```vue
<template>
  <Transition name="slide-up">
    <div v-if="show" class="toast-notification">
      <svg class="toast-icon" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
      </svg>
      <span class="toast-message">{{ message }}</span>
    </div>
  </Transition>
</template>

<script setup lang="ts">
defineProps<{
  show: boolean
  message: string
}>()
</script>

<style scoped>
.toast-notification {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: #1f2937;
  color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
}

.toast-icon {
  width: 20px;
  height: 20px;
  color: #10b981;
}

.toast-message {
  font-size: 14px;
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.3s ease-out;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
</style>
```

**Step 4: 在 App.vue 中集成 Toast**

在 `frontend/src/App.vue` 中添加：

```vue
<template>
  <router-view />
  <ToastNotification
    :show="toast.show"
    :message="toast.message"
  />
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import ToastNotification from '@/components/ToastNotification.vue'

const toast = reactive({
  show: false,
  message: ''
})

// 暴露给全局使用
;(window as any).__showToast = (message: string) => {
  toast.message = message
  toast.show = true
  setTimeout(() => {
    toast.show = false
  }, 2000)
}
</script>
```

**Step 5: 更新 useClipboard 使用 Toast**

修改 `frontend/src/composables/useClipboard.ts`:

```typescript
async function copy(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    copiedText.value = text

    // 使用全局 Toast
    const showToast = (window as any).__showToast
    if (showToast) {
      showToast('已复制到剪贴板')
    }

    return true
  } catch (error) {
    console.error('复制失败:', error)
    return false
  }
}
```

**Step 6: 运行测试确认通过**

```bash
npm run test
```

预期输出：所有测试通过

**Step 7: 手动验证**

启动开发服务器，复制消息，验证 Toast 显示和动画效果

**Step 8: 代码审查清单**

- [ ] Toast 组件独立封装，可复用
- [ ] 使用 Transition 组件实现动画
- [ ] 样式固定定位，不影响布局
- [ ] 动画流畅，用户体验良好
- [ ] 全局暴露 Toast 方法，方便其他组件使用

**Step 9: 提交代码**

```bash
git add frontend/src/components/ToastNotification.vue frontend/src/App.vue frontend/src/composables/useClipboard.ts frontend/tests/unit/components/ToastNotification.spec.ts
git commit -m "feat(ui): add global toast notification

- 创建独立的 ToastNotification 组件
- 添加滑入滑出动画
- 集成到剪贴板复制功能
- 全局暴露 Toast 方法"
```

---

## 阶段 2: 恢复错误处理 UI

### Task 4: 在 ChatPanel 中添加错误重试功能

**Files:**
- Modify: `frontend/src/components/ChatPanel.vue`
- Test: `frontend/tests/unit/components/ChatPanel.spec.ts`

**Step 1: 编写失败测试**

在 `frontend/tests/unit/components/ChatPanel.spec.ts` 中添加:

```typescript
it('should show error message when error exists', () => {
  const wrapper = mount(ChatPanel, {
    props: {
      messages: [],
      error: '网络错误'
    }
  })

  expect(wrapper.text()).toContain('网络错误')
  expect(wrapper.find('.error-message').exists()).toBe(true)
})

it('should emit retry event when retry button clicked', async () => {
  const wrapper = mount(ChatPanel, {
    props: {
      messages: [],
      error: '网络错误'
    }
  })

  await wrapper.find('.retry-button').trigger('click')

  expect(wrapper.emitted('retry')).toBeTruthy()
})
```

**Step 2: 运行测试确认失败**

```bash
npm run test -- ChatPanel.spec.ts
```

预期输出：FAIL - 找不到错误元素

**Step 3: 实现错误处理 UI**

在 `frontend/src/components/ChatPanel.vue` 中添加错误显示：

```vue
<template>
  <div class="chat-panel">
    <!-- 现有的消息列表和输入 -->

    <Transition name="fade">
      <div v-if="error" class="error-message">
        <div class="error-icon">⚠️</div>
        <div class="error-content">
          <div class="error-title">出错了</div>
          <div class="error-detail">{{ error }}</div>
          <button class="retry-button" @click="handleRetry">
            重试
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  messages: Message[]
  error?: string
}>()

const emit = defineEmits<{
  retry: []
}>()

function handleRetry() {
  emit('retry')
}
</script>

<style scoped>
.error-message {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  margin: 16px;
}

.error-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.error-content {
  flex: 1;
}

.error-title {
  font-size: 14px;
  font-weight: 600;
  color: #991b1b;
  margin-bottom: 4px;
}

.error-detail {
  font-size: 14px;
  color: #b91c1c;
  margin-bottom: 12px;
}

.retry-button {
  padding: 8px 16px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.retry-button:hover {
  background: #dc2626;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
```

**Step 4: 运行测试确认通过**

```bash
npm run test -- ChatPanel.spec.ts
```

预期输出：PASS

**Step 5: 运行全量测试**

```bash
npm run test
```

预期输出：所有测试通过

**Step 6: 代码审查清单**

- [ ] 错误显示清晰，用户可理解
- [ ] 重试按钮突出，易于点击
- [ ] 样式与整体设计一致
- [ ] 使用 emit 而非直接调用方法，保持组件单向数据流
- [ ] 测试覆盖了错误显示和重试逻辑

**Step 7: 提交代码**

```bash
git add frontend/src/components/ChatPanel.vue frontend/tests/unit/components/ChatPanel.spec.ts
git commit -m "feat(chat): add error handling UI with retry

- 显示详细错误信息
- 添加重试按钮
- 使用 emit 事件保持单向数据流
- 添加淡入淡出动画"
```

---

## 阶段 3: 恢复 Markdown 交互功能

### Task 5: 增强 markdownRenderer 添加交互按钮

**Files:**
- Modify: `frontend/src/utils/markdownRenderer.ts`
- Test: `frontend/tests/unit/utils/markdownRenderer.spec.ts`

**Step 1: 编写失败测试**

在 `frontend/tests/unit/utils/markdownRenderer.spec.ts` 中添加:

```typescript
it('should add preview button to code blocks', () => {
  const markdown = '```javascript\nconsole.log("test");\n```'
  const html = renderMarkdown(markdown)

  expect(html).toContain('preview-button')
  expect(html).toContain('data-artifact-content')
})

it('should add copy button to code blocks', () => {
  const markdown = '```javascript\nconsole.log("test");\n```'
  const html = renderMarkdown(markdown)

  expect(html).toContain('copy-code-button')
  expect(html).toContain('data-code-content')
})
```

**Step 2: 运行测试确认失败**

```bash
npm run test -- markdownRenderer.spec.ts
```

预期输出：FAIL - 找不到按钮

**Step 3: 实现 Markdown 渲染增强**

读取当前的 `frontend/src/utils/markdownRenderer.ts`，然后修改：

```bash
cat frontend/src/utils/markdownRenderer.ts
```

添加代码块按钮生成逻辑：

```typescript
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  highlight: (code, language) => {
    const validLang = language && hljs.getLanguage(language) ? language : 'plaintext'
    const highlighted = hljs.highlight(code, { language: validLang }).value

    // 添加预览和复制按钮
    const previewButton = `
      <button class="preview-button" data-artifact-content="${encodeURIComponent(JSON.stringify({
        type: 'code',
        language: validLang,
        content: code
      }))}" title="预览">
        <svg viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
          <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
          <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
        </svg>
      </button>
    `

    const copyButton = `
      <button class="copy-code-button" data-code-content="${encodeURIComponent(code)}" title="复制代码">
        <svg viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
          <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"/>
          <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"/>
        </svg>
      </button>
    `

    return `
      <div class="code-block-wrapper">
        <div class="code-block-header">
          <span class="code-language">${validLang}</span>
          <div class="code-block-actions">
            ${previewButton}
            ${copyButton}
          </div>
        </div>
        <pre class="hljs"><code>${highlighted}</code></pre>
      </div>
    `
  }
})
```

**Step 4: 添加样式**

创建 `frontend/src/styles/markdown.css`:

```css
/* Markdown 代码块样式 */
.code-block-wrapper {
  position: relative;
  margin: 16px 0;
  border-radius: 8px;
  overflow: hidden;
  background: #1f2937;
}

.code-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #111827;
  border-bottom: 1px solid #374151;
}

.code-language {
  font-size: 12px;
  color: #9ca3af;
  font-family: monospace;
  text-transform: uppercase;
}

.code-block-actions {
  display: flex;
  gap: 4px;
}

.code-block-actions button {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #d1d5db;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.code-block-actions button:hover {
  color: #f9fafb;
  background: #374151;
}

.code-block-wrapper pre {
  margin: 0;
  padding: 16px;
  overflow-x: auto;
}

.code-block-wrapper code {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #e5e7eb;
}
```

在 `frontend/src/components/MessageItem.vue` 中导入样式：

```vue
<style>
@import '@/styles/markdown.css';
</style>
```

**Step 5: 运行测试确认通过**

```bash
npm run test
```

预期输出：所有测试通过

**Step 6: 代码审查清单**

- [ ] 代码块样式独立在 CSS 文件中，便于维护
- [ ] 按钮使用 data 属性传递数据，安全可靠
- [ ] 语言标签自动识别
- [ ] 样式与主题一致（深色代码块）
- [ ] 测试覆盖了按钮生成逻辑

**Step 7: 提交代码**

```bash
git add frontend/src/utils/markdownRenderer.ts frontend/src/styles/markdown.css frontend/tests/unit/utils/markdownRenderer.spec.ts
git commit -m "feat(markdown): add interactive code block buttons

- 添加代码预览按钮
- 添加代码复制按钮
- 创建统一的 Markdown 样式文件
- 自动识别编程语言"
```

---

## 阶段 4: 恢复文档下载功能

### Task 6: 实现 Word 文档下载

**Files:**
- Modify: `frontend/src/components/preview/PreviewToolbar.vue`
- Test: `frontend/tests/integration/document-download.spec.ts`

**Step 1: 编写失败测试**

创建 `frontend/tests/integration/document-download.spec.ts`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { downloadWord } from '@/utils/documentDownloader'

describe('downloadWord', () => {
  global.fetch = vi.fn()

  it('should download Word document', async () => {
    const mockBlob = new Blob(['test'], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      blob: async () => mockBlob
    } as Response)

    const createElementSpy = vi.spyOn(document, 'createElement')
    const appendChildSpy = vi.spyOn(document.body, 'appendChild')
    const removeChildSpy = vi.spyOn(document.body, 'removeChild')

    await downloadWord('# Test\n\nThis is a test.')

    expect(fetch).toHaveBeenCalledWith('/api/v1/convert/markdown-to-word', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ markdown: '# Test\n\nThis is a test.' })
    })
    expect(createElementSpy).toHaveBeenCalledWith('a')
    expect(appendChildSpy).toHaveBeenCalled()
    expect(removeChildSpy).toHaveBeenCalled()
  })
})
```

**Step 2: 运行测试确认失败**

```bash
npm run test -- document-download.spec.ts
```

预期输出：FAIL - 找不到 downloadWord 函数

**Step 3: 实现 Word 下载功能**

创建 `frontend/src/utils/documentDownloader.ts`:

```typescript
export async function downloadWord(markdown: string, filename = 'document.docx'): Promise<void> {
  try {
    const response = await fetch('/api/v1/convert/markdown-to-word', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ markdown })
    })

    if (!response.ok) {
      throw new Error(`转换失败: ${response.statusText}`)
    }

    const blob = await response.blob()

    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()

    // 清理
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (error) {
    console.error('Word 下载失败:', error)
    throw error
  }
}
```

**Step 4: 在 PreviewToolbar 中集成**

读取 `frontend/src/components/preview/PreviewToolbar.vue`，移除"即将推出"提示，实现真实下载：

```vue
<template>
  <div class="preview-toolbar">
    <button
      class="toolbar-button"
      @click="handleDownloadWord"
      :disabled="isDownloading"
    >
      <DocumentIcon />
      <span>{{ isDownloading ? '转换中...' : 'Word' }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { DocumentIcon } from '@heroicons/vue/24/outline'
import { downloadWord } from '@/utils/documentDownloader'

const props = defineProps<{
  artifact: {
    type: string
    content: string
  }
}>()

const isDownloading = ref(false)

async function handleDownloadWord() {
  if (props.artifact.type !== 'markdown') return

  isDownloading.value = true
  try {
    await downloadWord(props.artifact.content, 'document.docx')
  } catch (error) {
    console.error('下载失败:', error)
    alert('下载失败，请重试')
  } finally {
    isDownloading.value = false
  }
}
</script>
```

**Step 5: 运行测试确认通过**

```bash
npm run test
```

预期输出：所有测试通过

**Step 6: 手动验证**

启动开发服务器，打开 Markdown 预览，点击 Word 下载按钮，验证文件下载成功

**Step 7: 代码审查清单**

- [ ] 下载逻辑封装在独立工具函数中
- [ ] 正确处理 Blob URL 清理，防止内存泄漏
- [ ] 显示下载进度（转换中...）
- [ ] 错误处理完善，用户可见错误提示
- [ ] 测试覆盖了 API 调用和文件下载流程

**Step 8: 提交代码**

```bash
git add frontend/src/utils/documentDownloader.ts frontend/src/components/preview/PreviewToolbar.vue frontend/tests/integration/document-download.spec.ts
git add frontend/src/utils/html2pdfDownloader.ts
git commit -m "feat(preview): add Word document download

- 调用后端 API 转换 Markdown 为 Word
- 添加下载进度提示
- 正确清理 Blob URL 防止内存泄漏
- 添加错误处理和用户提示"
```

---

### Task 7: 实现 PDF 文档下载

**Step 1: 安装 html2pdf.js**

```bash
npm install html2pdf.js@0.10.1
```

**Step 2: 编写测试**

在 `frontend/tests/integration/document-download.spec.ts` 中添加:

```typescript
it('should download PDF document', async () => {
  const htmlContent = '<div id="pdf-content"><h1>Test</h1></div>'

  const downloadPdf = await import('@/utils/html2pdfDownloader')
  const mockHtml2pdf = vi.fn().mockReturnValue({
    set: vi.fn().mockReturnThis(),
    from: vi.fn().mockReturnThis(),
    save: vi.fn().mockResolvedValue(undefined)
  })

  vi.doMock('html2pdf.js', () => mockHtml2pdf)

  await downloadPdf.default(htmlContent, 'document.pdf')

  expect(mockHtml2pdf).toHaveBeenCalled()
})
```

**Step 3: 实现 PDF 下载**

创建 `frontend/src/utils/html2pdfDownloader.ts`:

```typescript
import html2pdf from 'html2pdf.js'

export default async function downloadPdf(
  elementId: string,
  filename = 'document.pdf'
): Promise<void> {
  try {
    const element = document.getElementById(elementId)
    if (!element) {
      throw new Error('找不到要转换的元素')
    }

    const opt = {
      margin: 1,
      filename,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    }

    await html2pdf().set(opt).from(element).save()
  } catch (error) {
    console.error('PDF 下载失败:', error)
    throw error
  }
}
```

**Step 4: 在 PreviewToolbar 中集成**

```vue
<script setup lang="ts">
import downloadPdf from '@/utils/html2pdfDownloader'

async function handleDownloadPdf() {
  if (props.artifact.type !== 'markdown') return

  isDownloading.value = true
  try {
    await downloadPdf('markdown-content', 'document.pdf')
  } catch (error) {
    console.error('下载失败:', error)
    alert('下载失败，请重试')
  } finally {
    isDownloading.value = false
  }
}
</script>
```

**Step 5: 运行全量测试**

```bash
npm run test
```

预期输出：所有测试通过

**Step 6: 代码审查清单**

- [ ] 使用 html2pdf.js 库，版本锁定在 package.json
- [ ] 配置参数优化（高清晰度、A4 纸张）
- [ ] 错误处理完善
- [ ] 测试覆盖了 PDF 生成流程

**Step 7: 提交代码**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/utils/html2pdfDownloader.ts frontend/src/components/preview/PreviewToolbar.vue frontend/tests/integration/document-download.spec.ts
git commit -m "feat(preview): add PDF document download

- 集成 html2pdf.js 库
- 支持高清晰度 PDF 导出
- 添加错误处理"
```

---

## 阶段 5: 添加完整的 Markdown 样式

### Task 8: 补全 Markdown 样式系统

**Files:**
- Modify: `frontend/src/styles/markdown.css`
- Test: `frontend/tests/unit/styles/markdown.spec.ts` (可选)

**Step 1: 扩展 markdown.css**

在 `frontend/src/styles/markdown.css` 中添加完整的样式：

```css
/* Markdown 基础样式 */
.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  font-weight: 700;
  color: #111827;
  margin-top: 24px;
  margin-bottom: 16px;
  line-height: 1.25;
}

.markdown-content h1 { font-size: 2em; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; }
.markdown-content h2 { font-size: 1.5em; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }
.markdown-content h3 { font-size: 1.25em; }
.markdown-content h4 { font-size: 1em; }
.markdown-content h5 { font-size: 0.875em; }
.markdown-content h6 { font-size: 0.85em; color: #6b7280; }

.markdown-content p {
  margin: 16px 0;
  line-height: 1.7;
  color: #374151;
}

.markdown-content ul,
.markdown-content ol {
  margin: 16px 0;
  padding-left: 32px;
}

.markdown-content li {
  margin: 8px 0;
  color: #374151;
}

.markdown-content blockquote {
  margin: 16px 0;
  padding: 8px 16px;
  border-left: 4px solid #3b82f6;
  background: #eff6ff;
  color: #1e40af;
  font-style: italic;
}

.markdown-content code {
  padding: 2px 6px;
  background: #f3f4f6;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.875em;
  color: #eb5757;
}

.markdown-content pre {
  margin: 16px 0;
  overflow-x: auto;
}

.markdown-content a {
  color: #3b82f6;
  text-decoration: underline;
  transition: color 0.2s;
}

.markdown-content a:hover {
  color: #1d4ed8;
}

.markdown-content table {
  width: 100%;
  margin: 16px 0;
  border-collapse: collapse;
}

.markdown-content th,
.markdown-content td {
  padding: 12px;
  border: 1px solid #e5e7eb;
  text-align: left;
}

.markdown-content th {
  background: #f9fafb;
  font-weight: 600;
  color: #111827;
}

.markdown-content tr:nth-child(even) {
  background: #f9fafb;
}

.markdown-content img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 16px 0;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* KaTeX 公式样式优化 */
.markdown-content .katex {
  font-size: 1.1em;
}

.markdown-content .katex-display {
  margin: 24px 0;
  overflow-x: auto;
  overflow-y: hidden;
}
```

**Step 2: 在需要的组件中导入**

在 `frontend/src/components/MessageItem.vue`、`frontend/src/components/preview/MarkdownPreview.vue` 中导入：

```vue
<style>
@import '@/styles/markdown.css';
</style>
```

**Step 3: 运行全量测试**

```bash
npm run test
```

预期输出：所有测试通过

**Step 4: 手动验证**

启动开发服务器，发送包含各种 Markdown 语法的消息，验证样式正确：
- 标题（h1-h6）
- 列表（有序、无序）
- 代码块
- 表格
- 引用
- 链接
- 图片

**Step 5: 代码审查清单**

- [ ] 所有 Markdown 元素都有样式
- [ ] 样式独立在 CSS 文件中，便于维护
- [ ] 样式与设计系统一致（颜色、间距）
- [ ] 支持响应式（移动端表格滚动）
- [ ] KaTeX 公式样式优化

**Step 6: 提交代码**

```bash
git add frontend/src/styles/markdown.css frontend/src/components/MessageItem.vue frontend/src/components/preview/MarkdownPreview.vue
git commit -m "style(markdown): add complete markdown styling system

- 添加标题、列表、表格、引用等所有元素样式
- 优化 KaTeX 公式显示
- 统一颜色和间距
- 支持响应式布局"
```

---

## 阶段 6: 添加 E2E 测试覆盖

### Task 9: 编写聊天功能 E2E 测试

**Files:**
- Create: `frontend/tests/e2e/chat-features.spec.ts`

**Step 1: 编写 E2E 测试**

创建 `frontend/tests/e2e/chat-features.spec.ts`:

```typescript
import { test, expect } from '@playwright/test'

test.describe('Chat Features E2E', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('http://localhost:5173/login')
    await page.fill('input[name="username"]', 'test@example.com')
    await page.fill('input[name="password"]', 'password')
    await page.click('button[type="submit"]')
    await page.waitForURL('http://localhost:5173/')
  })

  test('should copy message content', async ({ page }) => {
    // 打开聊天工具
    await page.click('[data-testid="tool-selector"]')
    await page.click('text=AI 智能助手')

    // 发送消息
    await page.fill('[data-testid="chat-input"]', 'Hello')
    await page.click('[data-testid="send-button"]')

    // 等待 AI 响应
    await page.waitForSelector('[data-testid="message-item"][data-role="assistant"]')

    // 悬停显示复制按钮
    const messageItem = page.locator('[data-testid="message-item"][data-role="assistant"]').last()
    await messageItem.hover()

    // 点击复制按钮
    await page.click('[data-testid="copy-button"]')

    // 验证 Toast 显示
    await expect(page.locator('.toast-notification')).toContainText('已复制到剪贴板')
  })

  test('should retry on error', async ({ page }) => {
    // 模拟网络错误（需要 mock API）
    await page.route('**/api/v1/tools/*/chat/stream', route => {
      route.abort('failed')
    })

    // 打开聊天工具
    await page.click('[data-testid="tool-selector"]')
    await page.click('text=AI 智能助手')

    // 发送消息
    await page.fill('[data-testid="chat-input"]', 'Hello')
    await page.click('[data-testid="send-button"]')

    // 验证错误消息显示
    await expect(page.locator('.error-message')).toBeVisible()

    // 点击重试按钮
    await page.click('.retry-button')

    // 验证重试触发（恢复网络后）
    await page.unrouteAll({ behavior: 'ignoreErrors' })
  })

  test('should download Word document', async ({ page }) => {
    // 打开聊天工具并生成 Markdown 内容
    await page.click('[data-testid="tool-selector"]')
    await page.click('text=AI 智能助手')

    await page.fill('[data-testid="chat-input"]', '生成一个 Markdown 文档')
    await page.click('[data-testid="send-button"]')

    // 等待成果物生成
    await page.waitForSelector('[data-testid="preview-panel"]')

    // 点击 Word 下载按钮
    await page.click('[data-testid="download-word-button"]')

    // 验证下载（需要检查 download 事件）
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('[data-testid="download-word-button"]')
    ])

    expect(download.suggestedFilename()).toContain('.docx')
  })
})
```

**Step 2: 运行 E2E 测试**

```bash
cd frontend
npm run test:e2e
```

预期输出：所有测试通过

**Step 3: 添加必要的 data-testid**

在组件中添加 `data-testid` 属性，便于测试选择器使用。

**Step 4: 代码审查清单**

- [ ] E2E 测试覆盖了核心用户流程
- [ ] 测试使用 data-testid 而非 CSS 选择器，更稳定
- [ ] 测试包含正常流程和错误流程
- [ ] 测试可以独立运行，不依赖顺序

**Step 5: 提交代码**

```bash
git add frontend/tests/e2e/chat-features.spec.ts frontend/src/components/
git commit -m "test(e2e): add chat features E2E tests

- 测试消息复制功能
- 测试错误重试流程
- 测试文档下载功能
- 添加 data-testid 支持测试选择器"
```

---

## 最终验证

### Task 10: 完整回归测试

**Step 1: 运行所有测试**

```bash
cd frontend
npm run test
npm run test:coverage
npm run test:e2e
```

预期输出：
- 单元测试：PASS (100%)
- 覆盖率：核心组件 > 80%
- E2E 测试：PASS

**Step 2: 性能检查**

```bash
npm run build
```

预期输出：构建成功，无警告

**Step 3: 手动测试清单**

- [ ] 复制消息功能正常，Toast 显示正确
- [ ] 错误重试功能正常
- [ ] 代码块预览和复制按钮显示
- [ ] Word 下载成功，文件内容正确
- [ ] PDF 下载成功，样式保留
- [ ] Markdown 样式完整（标题、列表、表格、代码块）
- [ ] 移动端布局正常
- [ ] 平板端布局正常
- [ ] 桌面端布局正常
- [ ] 无内存泄漏（Chrome DevTools Performance 监控）

**Step 4: 代码审查清单**

- [ ] 所有组件保持单一职责
- [ ] 没有大组件，功能模块化拆分
- [ ] 样式独立在 CSS 文件中
- [ ] 组合式函数可复用
- [ ] 测试覆盖充分
- [ ] TypeScript 类型定义完整
- [ ] 没有控制台错误或警告

**Step 5: 提交最终代码**

```bash
git status
git add .
git commit -m "feat(chat): complete chat UI restoration

恢复的功能：
- 消息复制功能（组合式函数 + Toast）
- 错误处理 UI（重试按钮）
- Markdown 交互功能（代码块预览和复制）
- 文档下载功能（Word + PDF）
- 完整的 Markdown 样式系统

质量保障：
- 单元测试覆盖
- E2E 测试覆盖
- 性能测试通过
- 代码审查通过

架构原则：
- 保持组件模块化
- 样式集中管理
- 功能可复用
- 测试驱动开发"
```

**Step 6: 创建 Pull Request**

```bash
git push origin feature/restore-chat-ui
```

在 GitHub/GitLab 创建 Pull Request，包含：
- 功能变更说明
- 测试覆盖率报告
- 手动测试清单
- 性能对比
- 截图对比（重构前 vs 重构后）

---

## 代码审查指南

### 每次提交必须检查

1. **架构原则**
   - [ ] 组件保持单一职责
   - [ ] 功能拆分到组合式函数或工具函数
   - [ ] 样式独立在 CSS 文件中
   - [ ] 没有创建 >300 行的大文件

2. **代码质量**
   - [ ] TypeScript 类型定义完整
   - [ ] 没有控制台错误或警告
   - [ ] ESLint 检查通过
   - [ ] 代码格式化（Prettier）

3. **测试覆盖**
   - [ ] 新功能有对应测试
   - [ ] 测试覆盖正常流程和错误流程
   - [ ] 所有测试通过
   - [ ] 测试运行时间 < 30 秒

4. **性能**
   - [ ] 没有内存泄漏（Blob URL 清理、事件监听器清理）
   - [ ] 没有不必要的重渲染
   - [ ] 懒加载组件（如果适用）
   - [ ] 图片优化（如果适用）

5. **用户体验**
   - [ ] 加载状态清晰
   - [ ] 错误提示友好
   - [ ] 动画流畅（60fps）
   - [ ] 响应式设计（移动端、平板端）

### 常见反模式检查

- ❌ 将所有逻辑写回 ChatPanel.vue（破坏模块化）
- ❌ 复制粘贴旧代码而不重构
- ❌ 内联样式（应提取到 CSS 文件）
- ❌ 缺少错误处理
- ❌ 缺少加载状态
- ❌ 测试覆盖不足

---

## 参考文档

### 相关技能
- @superpowers:test-driven-development - TDD 方法指南
- @document-skills:frontend-design - 前端设计指南

### 项目文档
- `frontend/README.md` - 前端开发指南
- `backend/README.md` - 后端 API 文档
- `docs/architecture.md` - 系统架构说明

### Git 提交记录
- `0053666` - ChatPanel 重构
- `1e3cd8e` - PreviewPanel 重构
- `e41b901` - 后端 API 模块化

---

## 总结

本计划遵循以下原则：

1. **模块化优先**：通过增强子组件功能实现，不是合并回大组件
2. **测试驱动**：每个功能先写测试，再实现
3. **小步提交**：每个功能点一次提交，便于回滚
4. **质量保障**：每次修改后运行全量测试，代码审查
5. **文档齐全**：清晰的步骤说明、代码示例、验收标准

**预计总时间**：8-12 小时

**验收标准**：
- 所有功能恢复
- 所有测试通过（单元测试 + E2E 测试）
- 代码审查通过
- 性能无明显下降
- 用户手动测试通过
