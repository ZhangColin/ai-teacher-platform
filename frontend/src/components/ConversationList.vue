<template>
  <div class="conversation-list">
    <div class="conversation-header">
      <button class="new-conversation-btn" @click="handleNewConversation">
        + 新建对话
      </button>
    </div>
    <div class="conversation-items">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <span class="loading-text">加载对话列表...</span>
      </div>
      
      <!-- 错误状态 -->
      <div v-else-if="error" class="error-state">
        <span class="error-text">{{ error }}</span>
      </div>
      
      <!-- 空状态 -->
      <div v-else-if="conversations.length === 0" class="empty-state">
        <span class="empty-text">暂无对话</span>
      </div>
      
      <!-- 对话列表 -->
      <div
        v-else
        v-for="conversation in conversations"
        :key="conversation.session_id"
        :class="['conversation-item', { active: currentConversationId === conversation.session_id }]"
        @click="handleConversationClick(conversation.session_id)"
      >
        <div class="conversation-title">{{ conversation.title }}</div>
        <div class="conversation-time">{{ formatTime(conversation.updated_at) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { ApiService } from '../services/apiClient'
import type { ConversationListItem } from '../types'

const props = defineProps<{
  toolId?: string
}>()

const emit = defineEmits<{
  'conversation-change': [sessionId: string]
  'new-conversation': []
}>()

const conversations = ref<ConversationListItem[]>([])
const currentConversationId = ref<string | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// 加载历史对话列表
async function loadConversations() {
  if (!props.toolId) {
    conversations.value = []
    return
  }

  loading.value = true
  error.value = null

  try {
    const response = await ApiService.getConversations(props.toolId)
    conversations.value = response.conversations
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载对话列表失败'
    console.error('加载对话列表失败:', err)
  } finally {
    loading.value = false
  }
}

// 监听工具切换，重新加载对话列表
watch(() => props.toolId, (newToolId) => {
  if (newToolId) {
    currentConversationId.value = null
    loadConversations()
  } else {
    conversations.value = []
  }
}, { immediate: true })

function handleConversationClick(sessionId: string) {
  currentConversationId.value = sessionId
  emit('conversation-change', sessionId)
}

function handleNewConversation() {
  currentConversationId.value = null
  emit('new-conversation')
}

/**
 * 格式化时间
 */
function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    // 今天：显示时间
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    })
  } else if (days === 1) {
    // 昨天
    return '昨天'
  } else if (days < 7) {
    // 一周内：显示星期
    return date.toLocaleDateString('zh-CN', { weekday: 'short' })
  } else {
    // 更早：显示日期
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
    })
  }
}

// 暴露刷新方法，供外部调用
defineExpose({
  refresh: loadConversations,
})
</script>

<style scoped>
.conversation-list {
  @apply flex flex-col h-full border-r border-gray-200;
  /* 层级1：容器层 - 浅灰背景，右侧阴影 */
  background-color: theme('colors.gray.50');
  border-right-width: 1px;
  box-shadow: 2px 0 4px rgba(0, 0, 0, 0.04);
}

.conversation-header {
  @apply p-4 border-b border-gray-200; /* 从p-3(12px)增加到p-4(16px)，更宽松 */
}

.new-conversation-btn {
  @apply w-full px-3 py-2.5 bg-primary-500 text-white border-none rounded-lg text-sm font-medium cursor-pointer transition-all duration-200;
  box-shadow: 0 2px 4px theme('colors.primary.500 / 0.25');
}

.new-conversation-btn:hover {
  @apply bg-primary-600;
  box-shadow: 0 4px 8px theme('colors.primary.500 / 0.35');
}

.new-conversation-btn:active {
  @apply scale-[0.98];
}

.conversation-items {
  @apply flex-1 overflow-y-auto p-3; /* 从p-2(8px)增加到p-3(12px)，更宽松 */
}

.conversation-item {
  @apply px-4 py-3 mb-2 rounded-lg cursor-pointer transition-all duration-200;
  /* 添加更柔和的hover效果 */
}

.conversation-item:hover {
  @apply bg-gray-100;
  transform: translateX(2px);
}

.conversation-item.active {
  @apply bg-primary-50 border-primary-600 pl-2.5;
  border-left-width: 3px;
  /* 激活状态添加更明显的视觉反馈 */
  box-shadow: inset 0 0 0 1px theme('colors.primary.100');
}

.conversation-title {
  @apply text-sm font-medium text-gray-800 mb-1;
  line-height: 1.4;
}

.conversation-time {
  @apply text-xs text-gray-400;
  line-height: 1.4;
}

.loading-state,
.error-state,
.empty-state {
  @apply flex flex-col items-center justify-center py-8;
}

.loading-spinner {
  @apply w-6 h-6 border-[3px] border-gray-200 border-t-primary-500 rounded-full animate-spin mb-2;
}

.loading-text,
.error-text,
.empty-text {
  @apply text-sm text-gray-500;
}

.error-text {
  @apply text-red-500;
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .conversation-list {
    width: 200px;
  }
  
  .conversation-header {
    padding: 10px;
  }
  
  .new-conversation-btn {
    padding: 8px 10px;
    font-size: 13px;
  }
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .conversation-list {
    position: absolute;
    left: 0;
    top: 0;
    width: 280px;
    height: 100%;
    z-index: 50;
    transform: translateX(-100%);
    transition: transform 0.3s;
  }
  
  .conversation-list.open {
    transform: translateX(0);
  }
}
</style>

