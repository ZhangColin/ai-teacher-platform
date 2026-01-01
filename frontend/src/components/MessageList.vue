<template>
  <div class="message-list" data-testid="message-list">
    <!-- 加载指示（打字机效果） -->
    <div v-if="showTypingIndicator" class="typing-indicator">
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    </div>
    <MessageItem
      v-for="(message, index) in messages"
      :key="`${message.role}-${index}-${message.content.slice(0, 10)}`"
      :message="message"
      @preview="handlePreview"
      @retry="handleRetry"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MessageItem from './MessageItem.vue'
import type { Message, Artifact } from '../types'

const props = defineProps<{
  messages: Message[]
  loading?: boolean
}>()

const emit = defineEmits<{
  preview: [artifact: Artifact | null]
  retry: [message: Message]
}>()

/**
 * 是否显示打字机效果（最后一条消息是用户消息且正在等待回复）
 */
const showTypingIndicator = computed(() => {
  if (!props.loading) return false
  const lastMessage = props.messages[props.messages.length - 1]
  return lastMessage?.role === 'user' && !lastMessage.error
})

/**
 * 处理预览事件
 */
function handlePreview(artifact: Artifact | null) {
  emit('preview', artifact)
}

/**
 * 处理重发事件
 */
function handleRetry(message: Message) {
  emit('retry', message)
}
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background-color: #f3f4f6;
  border-radius: 0.5rem;
  align-self: flex-start;
  max-width: 80px;
}

.typing-dot {
  width: 0.5rem;
  height: 0.5rem;
  background-color: #6b7280;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.7;
  }
  30% {
    transform: translateY(-0.5rem);
    opacity: 1;
  }
}
</style>

