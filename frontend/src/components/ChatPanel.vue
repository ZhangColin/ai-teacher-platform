<template>
  <div class="chat-panel">
    <!-- 消息内容区域（包含欢迎语和消息，可滚动） -->
    <div class="messages-area">
      <!-- 欢迎语（仅在没有消息时显示） -->
      <div v-if="sessionStore.messages.length === 0" class="welcome-area">
        <WelcomeMessage :welcome-message="welcomeMessage" />
      </div>
      
      <!-- 消息列表 -->
      <div 
        v-for="(message, index) in sessionStore.messages" 
        :key="`${message.role}-${index}-${message.content.slice(0, 10)}`" 
        :class="['message-item', message.role]"
      >
        <div class="message-role">{{ message.role === 'user' ? '你' : 'AI' }}</div>
        <div class="message-content">{{ message.content }}</div>
        <button v-if="message.role === 'assistant' && message.artifacts && message.artifacts.length > 0" class="preview-btn" @click="handlePreview(message.artifacts[0])">
          预览
        </button>
      </div>
      
      <!-- 加载指示器 -->
      <div v-if="sessionStore.loading" class="loading-indicator">
        <div class="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
    
    <!-- 输入框区域（固定在底部） -->
    <div class="input-area">
      <ChatInput @send="handleSendMessage" :disabled="sessionStore.loading" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch, nextTick } from 'vue'
import WelcomeMessage from './WelcomeMessage.vue'
import ChatInput from './ChatInput.vue'
import { useSessionStore } from '../stores/sessionStore'
import type { Artifact } from '../types'

const props = defineProps<{
  toolId?: string
  welcomeMessage?: string
  sessionId?: string
}>()

const emit = defineEmits<{
  send: [content: string]
  preview: [artifact: Artifact]
}>()

const sessionStore = useSessionStore()

// 初始化工具
watch(() => props.toolId, (newToolId) => {
  if (newToolId) {
    sessionStore.initTool(newToolId)
  }
}, { immediate: true })

// 恢复会话
watch(() => props.sessionId, async (newSessionId) => {
  if (newSessionId) {
    try {
      await sessionStore.restoreSession(newSessionId)
    } catch (err) {
      console.error('恢复会话失败:', err)
    }
  }
}, { immediate: true })

async function handleSendMessage(content: string) {
  if (!props.toolId) {
    console.error('工具ID未设置，无法发送消息')
    return
  }
  
  try {
    await sessionStore.sendMessage(content)
    emit('send', content)
    
    // 发送成功后，滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (err) {
    console.error('发送消息失败:', err)
    // 错误已经在 sessionStore 中处理，这里只记录日志
  }
}

/**
 * 滚动到底部
 */
function scrollToBottom() {
  const messagesArea = document.querySelector('.messages-area')
  if (messagesArea) {
    messagesArea.scrollTop = messagesArea.scrollHeight
  }
}

function handlePreview(artifact: Artifact) {
  emit('preview', artifact)
}
</script>

<style scoped>
.chat-panel {
  @apply flex flex-col h-full overflow-hidden bg-white;
}

.messages-area {
  @apply flex-1 overflow-y-auto px-6 py-8 flex flex-col gap-8; /* 从py-6(24px)增加到py-8(32px)，gap从6增加到8 */
  scroll-behavior: smooth;
  min-height: 0; /* 确保 flex 子元素可以正确收缩 */
}

.welcome-area {
  @apply flex-1 flex items-center justify-center; /* 欢迎语居中显示 */
  min-height: 0;
}

.message-item {
  @apply flex flex-col gap-2 max-w-full;
}

.message-item.user {
  @apply items-end;
}

.message-item.assistant {
  @apply items-start;
}

.message-role {
  @apply text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1 px-1;
}

.message-content {
  @apply text-sm leading-relaxed break-words px-4 py-3 rounded-2xl max-w-[85%];
  /* 层级3：交互层 - 明显的阴影和背景 */
}

.message-item.user .message-content {
  @apply bg-primary-500 text-white;
  /* 层级3：交互层 - 主色背景，明显阴影 */
  box-shadow: 0 2px 8px theme('colors.primary.500 / 0.3'), 0 1px 3px rgba(0, 0, 0, 0.1);
}

.message-item.assistant .message-content {
  @apply bg-white text-gray-900;
  /* 层级2：内容层 - 白色背景，更柔和的边框和阴影 */
  border: 1px solid theme('colors.gray.200');
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.message-item.assistant .message-content:hover {
  border-color: theme('colors.gray.300');
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.06);
}

.preview-btn {
  @apply px-3.5 py-1.5 bg-white text-gray-700 border border-gray-300 rounded-md text-xs font-medium cursor-pointer transition-all duration-200 self-start;
  /* 层级3：交互层 - 白色背景，轻微阴影，更柔和的边框 */
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  border-color: theme('colors.gray.300');
}

.preview-btn:hover {
  @apply bg-gray-50;
  border-color: theme('colors.gray.400');
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.preview-btn:active {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.loading-indicator {
  @apply flex items-center justify-center py-4;
}

.loading-dots {
  @apply flex gap-2;
}

.loading-dots span {
  @apply w-2 h-2 bg-gray-400 rounded-full animate-pulse;
}

.loading-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

.input-area {
  @apply py-6 px-6 border-t border-gray-200 flex-shrink-0 bg-white;
  /* 层级2：内容层 - 白色背景，顶部边框 */
  /* 内边距保持24px (px-6)，已符合要求 */
  box-shadow: 0 -1px 3px rgba(0, 0, 0, 0.04);
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .welcome-area {
    padding: 40px 20px;
  }
  
  .messages-area {
    padding: 20px;
  }
  
  .input-area {
    padding: 18px 20px;
  }
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .welcome-area {
    padding: 32px 16px;
  }
  
  .messages-area {
    padding: 16px;
    gap: 20px;
  }
  
  .input-area {
    padding: 16px;
  }
}
</style>

