<template>
  <div class="markdown-editor-view">
    <!-- 编辑器容器 -->
    <div class="editor-container">
      <!-- 左侧：CodeMirror 编辑器 -->
      <div class="editor-panel">
        <div class="editor-header">
          <span class="editor-title">Markdown 编辑器</span>
          <div class="editor-actions">
            <button class="editor-action-btn" @click="handleClear" title="清空内容">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              <span>清空</span>
            </button>
          </div>
        </div>
        <div ref="editorRef" class="editor-content"></div>
      </div>

      <!-- 右侧：预览面板 -->
      <div class="preview-container">
        <PreviewPanel :artifact="previewArtifact" @close="handleClosePreview" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { EditorView, keymap, lineNumbers, highlightActiveLineGutter, highlightActiveLine } from '@codemirror/view'
import { EditorState } from '@codemirror/state'
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands'
import { markdown } from '@codemirror/lang-markdown'
import { oneDark } from '@codemirror/theme-one-dark'
import { syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language'
import PreviewPanel from '../components/PreviewPanel.vue'
import type { Artifact } from '../types'

// 编辑器引用
const editorRef = ref<HTMLElement | null>(null)
let editorView: EditorView | null = null

// 编辑器内容
const editorContent = ref(`# 欢迎使用 Markdown 编辑器

这是一个功能强大的在线 Markdown 编辑器，支持实时预览。

## 功能特性

- ✅ 实时预览
- ✅ 语法高亮
- ✅ 支持数学公式（KaTeX）
- ✅ 导出为 Markdown、Word、PDF

## 数学公式示例

行内公式：$E = mc^2$

块级公式：

$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$

## 代码示例

\`\`\`javascript
function hello() {
  console.log('Hello, Markdown!');
}
\`\`\`

## 表格示例

| 功能 | 状态 |
|------|------|
| 编辑 | ✅ |
| 预览 | ✅ |
| 导出 | ✅ |

---

开始编辑你的内容吧！
`)

// 预览成果物
const previewArtifact = computed<Artifact>(() => ({
  type: 'markdown',
  content: editorContent.value,
  language: 'markdown',
  timestamp: new Date().toISOString(),
}))

/**
 * 初始化 CodeMirror 编辑器
 */
const initEditor = () => {
  if (!editorRef.value) return

  const startState = EditorState.create({
    doc: editorContent.value,
    extensions: [
      lineNumbers(),
      highlightActiveLineGutter(),
      highlightActiveLine(),
      history(),
      keymap.of([...defaultKeymap, ...historyKeymap]),
      markdown(),
      syntaxHighlighting(defaultHighlightStyle),
      oneDark,
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          editorContent.value = update.state.doc.toString()
        }
      }),
      EditorView.lineWrapping, // 自动换行
    ],
  })

  editorView = new EditorView({
    state: startState,
    parent: editorRef.value,
  })
}

/**
 * 清空编辑器内容
 */
const handleClear = () => {
  if (!editorView) return
  
  if (confirm('确定要清空所有内容吗？此操作不可撤销。')) {
    const transaction = editorView.state.update({
      changes: { from: 0, to: editorView.state.doc.length, insert: '' },
    })
    editorView.dispatch(transaction)
    editorContent.value = ''
  }
}

/**
 * 关闭预览（占位符，预览始终显示）
 */
const handleClosePreview = () => {
  // Markdown编辑器中预览始终显示，不关闭
}

// 组件挂载时初始化编辑器
onMounted(() => {
  initEditor()
})

// 组件卸载时销毁编辑器
onBeforeUnmount(() => {
  if (editorView) {
    editorView.destroy()
    editorView = null
  }
})
</script>

<style scoped>
.markdown-editor-view {
  @apply h-full w-full overflow-hidden;
  background-color: theme('colors.gray.50');
}

.editor-container {
  @apply h-full flex;
}

/* 左侧编辑器 */
.editor-panel {
  @apply flex-1 flex flex-col border-r border-gray-300;
  min-width: 400px;
}

.editor-header {
  @apply flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200;
}

.editor-title {
  @apply text-sm font-semibold text-gray-900;
}

.editor-actions {
  @apply flex gap-2;
}

.editor-action-btn {
  @apply flex items-center gap-1 px-3 py-1.5 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors;
}

.editor-action-btn:hover {
  @apply bg-gray-100;
}

.editor-content {
  @apply flex-1 overflow-auto;
}

/* CodeMirror 样式覆盖 */
.editor-content :deep(.cm-editor) {
  @apply h-full;
  font-size: 14px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
}

.editor-content :deep(.cm-scroller) {
  @apply overflow-auto;
}

.editor-content :deep(.cm-content) {
  @apply p-4;
}

.editor-content :deep(.cm-line) {
  padding-left: 8px;
  padding-right: 8px;
}

/* 右侧预览 */
.preview-container {
  @apply flex-1 flex flex-col;
  min-width: 400px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .editor-container {
    @apply flex-col;
  }

  .editor-panel,
  .preview-container {
    @apply w-full;
    min-width: unset;
    height: 50%;
  }

  .editor-panel {
    @apply border-r-0 border-b border-gray-300;
  }
}

@media (max-width: 768px) {
  .editor-header {
    @apply px-3 py-2;
  }

  .editor-title {
    @apply text-xs;
  }

  .editor-action-btn {
    @apply px-2 py-1 text-xs;
  }

  .editor-action-btn span {
    @apply hidden;
  }
}
</style>
