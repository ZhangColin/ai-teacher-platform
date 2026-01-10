<template>
  <div
    class="message-item"
    :class="`message-${message.role}`"
    data-testid="message-item"
  >
    <div class="message-header">
      <span class="message-role">{{ message.role === 'user' ? '用户' : 'AI' }}</span>
      <span v-if="message.timestamp" class="message-time">
        {{ formatTime(message.timestamp) }}
      </span>
    </div>
    <div class="message-content">
      <!-- 错误提示 -->
      <div v-if="message.error" class="message-error">
        <span class="error-text">{{ message.error }}</span>
        <button v-if="message.role === 'user'" class="retry-button" @click="handleRetry">
          重发
        </button>
      </div>
      <!-- 加载状态 -->
      <div v-else-if="message.pending" class="message-pending">
        <span class="pending-text">发送中...</span>
      </div>
      <!-- 正常内容 -->
      <template v-else>
        <div
          v-if="message.role === 'assistant'"
          ref="contentRef"
          class="markdown-content"
          v-html="renderedContent"
        ></div>
        <div v-else class="text-content">{{ message.content }}</div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { renderMarkdown } from '../utils/markdownRenderer'
import type { Message, Artifact } from '../types'

const props = defineProps<{
  message: Message
  messageIndex?: number
}>()

const emit = defineEmits<{
  preview: [artifact: Artifact | null]
  retry: [message: Message]
}>()

const contentRef = ref<HTMLElement | null>(null)

/**
 * 渲染 Markdown 内容
 */
const renderedContent = computed(() => {
  if (props.message.role === 'assistant') {
    return renderMarkdown(props.message.content, props.message.artifacts || [])
  }
  return ''
})

/**
 * 处理按钮点击（预览、复制）
 */
function handlePreviewClick(event: Event) {
  let target = event.target as HTMLElement
  
  // 如果点击的是按钮内的SVG或其他子元素，向上查找按钮元素
  while (target && !target.classList.contains('preview-button') && !target.classList.contains('copy-code-button')) {
    target = target.parentElement as HTMLElement
    if (!target || target === contentRef.value) break
  }
  
  if (!target) return
  
  // 处理预览按钮
  if (target.classList.contains('preview-button')) {
    const artifactData = target.getAttribute('data-artifact-content')
    if (artifactData) {
      try {
        const artifact: Artifact = JSON.parse(artifactData)
        emit('preview', artifact)
      } catch (error) {
        console.error('解析 artifact 数据失败:', error)
      }
    }
  }
  
  // 处理复制代码按钮
  if (target.classList.contains('copy-code-button')) {
    const codeContent = target.getAttribute('data-code-content')
    if (codeContent) {
      // 反转义 HTML
      const decodedContent = unescapeHtml(codeContent)
      navigator.clipboard.writeText(decodedContent).then(() => {
        // 显示复制成功提示
        const originalHTML = target.innerHTML
        target.innerHTML = '<span style="color: #10b981;">✓ 已复制</span>'
        setTimeout(() => {
          target.innerHTML = originalHTML
        }, 2000)
      }).catch((error) => {
        console.error('复制失败:', error)
      })
    }
  }
}

/**
 * 反转义 HTML
 */
function unescapeHtml(text: string): string {
  const map: Record<string, string> = {
    '&amp;': '&',
    '&lt;': '<',
    '&gt;': '>',
    '&quot;': '"',
    '&#039;': "'",
    '&nbsp;': ' ',
  }
  return text.replace(/&(?:amp|lt|gt|quot|#039|nbsp);/g, (m) => map[m] || m)
}

/**
 * 处理重发
 */
function handleRetry() {
  emit('retry', props.message)
}

/**
 * 格式化时间
 */
function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  // 监听预览按钮点击事件
  if (contentRef.value) {
    contentRef.value.addEventListener('click', handlePreviewClick)
  }
})

onUnmounted(() => {
  // 清理事件监听
  if (contentRef.value) {
    contentRef.value.removeEventListener('click', handlePreviewClick)
  }
})
</script>

<style scoped>
.message-item {
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.message-user {
  background-color: #3b82f6;
  color: white;
  align-self: flex-end;
  max-width: 80%;
  margin-left: auto;
}

.message-assistant {
  background-color: #f3f4f6;
  color: #1f2937;
  align-self: flex-start;
  max-width: 80%;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  opacity: 0.8;
}

.message-role {
  font-weight: 600;
}

.message-time {
  font-size: 0.75rem;
}

.message-content {
  line-height: 1.6;
}

.text-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.markdown-content {
  word-break: break-word;
}

.markdown-content :deep(pre) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.75rem;
  border-radius: 0.25rem;
  overflow-x: auto;
}

.markdown-content :deep(code) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.125rem 0.25rem;
  border-radius: 0.125rem;
  font-size: 0.875em;
}

/* 代码块样式 - 直接复制自 ChatPanel.vue（已验证） */
.markdown-content :deep(.code-block-wrapper) {
  @apply relative my-4;
  position: relative;
}

.markdown-content :deep(.code-block-wrapper pre) {
  @apply relative;
  margin: 0; /* 移除默认 margin，由 wrapper 控制 */
}

/* 代码块操作按钮组 */
.markdown-content :deep(.code-block-actions) {
  @apply absolute top-2 right-2 flex gap-1.5 opacity-70 transition-opacity duration-200 z-10;
}

.markdown-content :deep(.code-block-wrapper:hover .code-block-actions) {
  opacity: 1;
}

.markdown-content :deep(.preview-button),
.markdown-content :deep(.copy-code-button) {
  @apply w-7 h-7 flex items-center justify-center text-gray-300 hover:text-gray-100 hover:bg-gray-700 rounded cursor-pointer transition-all duration-150;
  background-color: rgba(31, 41, 55, 0.7); /* 与代码块背景色匹配，提高初始可见度 */
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.1); /* 添加边框增加可见度 */
}

.markdown-content :deep(.preview-button:hover),
.markdown-content :deep(.copy-code-button:hover) {
  background-color: rgba(31, 41, 55, 0.9);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.markdown-content :deep(.preview-button:active),
.markdown-content :deep(.copy-code-button:active) {
  transform: scale(0.95) translateY(0);
  background-color: rgba(31, 41, 55, 1);
}

.message-error {
  @apply flex items-center gap-3 p-3 rounded-md;
  background-color: theme('colors.error.100');
  border: 1px solid theme('colors.error.300');
  color: theme('colors.error.800');
}

.error-text {
  @apply flex-1 text-sm;
}

.retry-button {
  @apply px-3 py-1.5 bg-error-600 text-white border-none rounded text-sm font-medium cursor-pointer transition-all duration-200;
}

.retry-button:hover {
  @apply bg-error-700;
}

.message-pending {
  padding: 0.75rem;
  color: #6b7280;
  font-size: 0.875rem;
  font-style: italic;
}
</style>

