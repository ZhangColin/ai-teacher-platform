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
  display: flex;
  flex-direction: column;
  height: 100%;
  border-right: 1px solid #e5e7eb;
  background-color: #f9fafb;
}

.conversation-header {
  padding: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.new-conversation-btn {
  width: 100%;
  padding: 10px 12px;
  background-color: #3b82f6;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 2px rgba(59, 130, 246, 0.2);
}

.new-conversation-btn:hover {
  background-color: #2563eb;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.new-conversation-btn:active {
  transform: scale(0.98);
}

.conversation-items {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conversation-item {
  padding: 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.conversation-item:hover {
  background-color: #f3f4f6;
}

.conversation-item.active {
  background-color: #eff6ff;
  border-left: 3px solid #2563eb;
  padding-left: 9px;
}

.conversation-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
  line-height: 1.4;
}

.conversation-preview {
  font-size: 12px;
  color: #6b7280;
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

