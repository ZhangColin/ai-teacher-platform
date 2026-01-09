<template>
  <div class="markdown-editor-view">
    <!-- 顶部工具条 -->
    <div class="toolbar">
      <button class="toolbar-btn back-btn" @click="handleBack">
        <ArrowLeftIcon class="w-5 h-5" />
        <span>返回</span>
      </button>
      <div class="toolbar-title">
        <DocumentTextIcon class="w-5 h-5 text-blue-600" />
        <span>Markdown 编辑器</span>
      </div>
      <div class="toolbar-actions">
        <button class="toolbar-btn" @click="handleClear" title="清空内容">
          <TrashIcon class="w-4 h-4" />
          <span>清空</span>
        </button>
      </div>
    </div>

    <!-- 编辑器容器 -->
    <div class="editor-container">
      <!-- 左侧：CodeMirror 编辑器 -->
      <div class="editor-panel">
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
import { useRouter } from 'vue-router'
import { EditorView, keymap, lineNumbers, highlightActiveLineGutter, highlightActiveLine } from '@codemirror/view'
import { EditorState } from '@codemirror/state'
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands'
import { markdown } from '@codemirror/lang-markdown'
import { oneDark } from '@codemirror/theme-one-dark'
import { syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language'
import { ArrowLeftIcon, DocumentTextIcon, TrashIcon } from '@heroicons/vue/24/outline'
import PreviewPanel from '../components/PreviewPanel.vue'
import type { Artifact } from '../types'

const router = useRouter()

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
 * 返回工具列表
 */
const handleBack = () => {
  router.push('/common-tools')
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
  @apply h-full w-full overflow-hidden flex flex-col;
  background-color: theme('colors.gray.50');
}

/* 顶部工具条 */
.toolbar {
  @apply flex items-center gap-4 px-6 py-3 bg-white border-b border-gray-200;
  flex-shrink: 0;
}

.toolbar-btn {
  @apply flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all;
}

.toolbar-btn:hover {
  @apply shadow-sm;
}

.back-btn {
  @apply text-gray-600 hover:text-gray-900;
}

.toolbar-title {
  @apply flex items-center gap-2 text-lg font-semibold text-gray-900 flex-1;
}

.toolbar-actions {
  @apply flex items-center gap-2;
}

/* 编辑器容器 */
.editor-container {
  @apply flex-1 flex overflow-hidden;
}

/* 左侧编辑器 */
.editor-panel {
  @apply flex-1 flex flex-col border-r border-gray-300 bg-white;
  min-width: 400px;
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
