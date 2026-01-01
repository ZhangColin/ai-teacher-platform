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
 * 处理预览按钮点击
 */
function handlePreviewClick(event: Event) {
  const target = event.target as HTMLElement
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

.markdown-content :deep(.code-block-wrapper) {
  position: relative;
  margin: 1rem 0;
}

.markdown-content :deep(.preview-button) {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  padding: 0.375rem 0.75rem;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  z-index: 10;
}

.markdown-content :deep(.preview-button:hover) {
  background-color: #2563eb;
}

.markdown-content :deep(.preview-button:active) {
  background-color: #1d4ed8;
}

.message-error {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background-color: #fee2e2;
  border: 1px solid #fca5a5;
  border-radius: 0.375rem;
  color: #991b1b;
}

.error-text {
  flex: 1;
  font-size: 0.875rem;
}

.retry-button {
  padding: 0.375rem 0.75rem;
  background-color: #dc2626;
  color: white;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-button:hover {
  background-color: #b91c1c;
}

.message-pending {
  padding: 0.75rem;
  color: #6b7280;
  font-size: 0.875rem;
  font-style: italic;
}
</style>

