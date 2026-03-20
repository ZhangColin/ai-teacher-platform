<template>
  <div class="markdown-editor" :class="{ 'is-fullscreen': fullscreen }">
    <!-- 编辑器容器 -->
    <div class="editor-container">
      <!-- 左侧：CodeMirror 编辑器 -->
      <div class="editor-panel" :style="{ width: `${editorWidth}%` }">
        <div ref="editorRef" class="editor-content"></div>
      </div>

      <!-- 可拖动分隔条 -->
      <div
        v-if="!fullscreen"
        class="resizer"
        @mousedown="startResize"
        @touchstart="startResize"
      >
        <div class="resizer-line"></div>
      </div>

      <!-- 右侧：预览面板 -->
      <div class="preview-container" :style="{ width: fullscreen ? '100%' : `${100 - editorWidth}%` }">
        <PreviewPanel :artifact="previewArtifact" @close="handleClosePreview" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { EditorView, keymap, lineNumbers, highlightActiveLineGutter, highlightActiveLine } from '@codemirror/view'
import { EditorState } from '@codemirror/state'
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands'
import { markdown } from '@codemirror/lang-markdown'
import { oneDark } from '@codemirror/theme-one-dark'
import { syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language'
import PreviewPanel from '../PreviewPanel.vue'
import type { Artifact } from '../../types'

interface Props {
  modelValue: string
  fullscreen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  fullscreen: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

// 编辑器引用
const editorRef = ref<HTMLElement | null>(null)
let editorView: EditorView | null = null

// 分隔条宽度（百分比）
const editorWidth = ref(50)
const isResizing = ref(false)

// 预览成果物
const previewArtifact = computed<Artifact>(() => ({
  type: 'markdown',
  content: props.modelValue,
  language: 'markdown',
  timestamp: new Date().toISOString(),
}))

/**
 * 初始化 CodeMirror 编辑器
 */
const initEditor = () => {
  if (!editorRef.value) return

  const startState = EditorState.create({
    doc: props.modelValue,
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
          const newContent = update.state.doc.toString()
          emit('update:modelValue', newContent)
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
 * 关闭预览（占位符，预览始终显示）
 */
const handleClosePreview = () => {
  // Markdown编辑器中预览始终显示，不关闭
}

/**
 * 开始调整大小
 */
const startResize = (e: MouseEvent | TouchEvent) => {
  isResizing.value = true
  e.preventDefault()

  // 添加全局监听
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.addEventListener('touchmove', handleResize)
  document.addEventListener('touchend', stopResize)

  // 添加样式防止文本选择
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

/**
 * 调整大小中
 */
const handleResize = (e: MouseEvent | TouchEvent) => {
  if (!isResizing.value) return

  // 获取容器宽度
  const container = document.querySelector('.editor-container') as HTMLElement
  if (!container) return

  const containerRect = container.getBoundingClientRect()
  const clientX = 'touches' in e ? (e.touches[0]?.clientX ?? 0) : e.clientX

  // 计算新宽度（百分比）
  const newWidth = ((clientX - containerRect.left) / containerRect.width) * 100

  // 限制在 30% - 70% 之间
  editorWidth.value = Math.max(30, Math.min(70, newWidth))
}

/**
 * 停止调整大小
 */
const stopResize = () => {
  isResizing.value = false

  // 移除全局监听
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.removeEventListener('touchmove', handleResize)
  document.removeEventListener('touchend', stopResize)

  // 恢复样式
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

/**
 * 更新编辑器内容（从外部更新时）
 */
watch(
  () => props.modelValue,
  (newValue) => {
    if (editorView && editorView.state.doc.toString() !== newValue) {
      const transaction = editorView.state.update({
        changes: { from: 0, to: editorView.state.doc.length, insert: newValue },
      })
      editorView.dispatch(transaction)
    }
  }
)

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
.markdown-editor {
  @apply h-full w-full overflow-hidden flex flex-col;
  background-color: theme('colors.gray.50');
}

.markdown-editor.is-fullscreen {
  @apply fixed inset-0 z-50;
}

/* 编辑器容器 */
.editor-container {
  @apply flex-1 flex overflow-hidden relative;
}

/* 左侧编辑器 */
.editor-panel {
  @apply flex flex-col border-r border-gray-200 bg-white;
  min-width: 30%;
  max-width: 70%;
}

.is-fullscreen .editor-panel {
  @apply border-r-0;
  max-width: 100%;
}

/* 可拖动分隔条 */
.resizer {
  @apply flex-shrink-0 w-1 bg-gray-200 hover:bg-blue-400 cursor-col-resize relative transition-colors;
  z-index: 10;
}

.resizer:hover .resizer-line {
  @apply opacity-100;
}

.resizer-line {
  @apply absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-1 h-12 bg-blue-500 rounded-full opacity-0 transition-opacity;
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
  @apply flex flex-col bg-white;
  min-width: 30%;
  max-width: 70%;
}

.is-fullscreen .preview-container {
  max-width: 100%;
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  /* 平板端样式 */
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .editor-container {
    @apply flex-col;
  }

  .editor-panel,
  .preview-container {
    @apply w-full;
    min-width: unset;
    max-width: unset;
    height: 50%;
  }

  .editor-panel {
    @apply border-r-0 border-b border-gray-200;
  }

  .resizer {
    @apply hidden;
  }
}
</style>
