<template>
  <div class="conversation-list">
    <div class="conversation-header">
      <button class="new-conversation-btn" @click="handleNewConversation">
        + 新建对话
      </button>
    </div>
    <div class="conversation-items">
      <div
        v-for="conversation in conversations"
        :key="conversation.id"
        :class="['conversation-item', { active: currentConversationId === conversation.id }]"
        @click="handleConversationClick(conversation.id)"
      >
        <div class="conversation-title">{{ conversation.title }}</div>
        <div v-if="conversation.preview" class="conversation-preview">
          {{ conversation.preview }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface ConversationItem {
  id: string
  title: string
  preview?: string
  timestamp?: number
}

const emit = defineEmits<{
  'conversation-change': [conversationId: string]
}>()

// 写死的对话列表数据
const conversations: ConversationItem[] = [
  {
    id: 'conv-1',
    title: '提示词优化讨论',
    preview: '如何优化AI提示词的效果？',
  },
  {
    id: 'conv-2',
    title: '产品设计思路',
    preview: '关于新功能的用户体验设计...',
  },
  {
    id: 'conv-3',
    title: '技术方案讨论',
    preview: '前端架构的选择和优化方向',
  },
  {
    id: 'conv-4',
    title: '代码重构计划',
    preview: '如何重构现有代码结构...',
  },
]

const currentConversationId = ref<string>('conv-1')

function handleConversationClick(conversationId: string) {
  currentConversationId.value = conversationId
  emit('conversation-change', conversationId)
}

function handleNewConversation() {
  // 当前迭代仅占位，后续实现
  console.log('新建对话')
}
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

.conversation-preview {
  @apply text-xs text-gray-500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
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

