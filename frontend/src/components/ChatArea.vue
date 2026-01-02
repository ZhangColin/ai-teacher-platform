<template>
  <div class="chat-area" :class="{ 'with-preview': showPreview }">
    <!-- 左侧：历史对话列表 -->
    <ConversationList class="conversation-list" @conversation-change="handleConversationChange" />
    
    <!-- 中间：当前对话区域 -->
    <ChatPanel :conversation-id="currentConversationId" class="chat-panel" @send="handleSendMessage" @preview="openPreview" />
    
    <!-- 右侧：预览区域 -->
    <div v-if="showPreview" class="preview-panel">
      <div class="preview-header">
        <span class="preview-title">预览</span>
        <button class="preview-close" @click="closePreview">×</button>
      </div>
      <div class="preview-content">
        <div class="preview-placeholder">预览内容区域</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ConversationList from './ConversationList.vue'
import ChatPanel from './ChatPanel.vue'

const currentConversationId = ref<string>('conv-1')
const showPreview = ref(false)

function handleConversationChange(conversationId: string) {
  currentConversationId.value = conversationId
}

function handleSendMessage(content: string) {
  // 当前迭代仅占位，后续实现
  console.log('发送消息:', content)
  // 模拟触发预览（后续从消息中检测预览按钮）
  // showPreview.value = true
}

function closePreview() {
  showPreview.value = false
}

// 临时：添加一个方法用于测试预览功能
function openPreview() {
  showPreview.value = true
}

// 暴露给外部调用（后续从消息中检测预览按钮时使用）
defineExpose({
  openPreview,
})
</script>

<style scoped>
.chat-area {
  @apply flex h-full overflow-hidden bg-white;
  /* 层级2：内容层 - 白色背景，轻微阴影 */
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.04);
}

.conversation-list {
  width: 280px;
  flex-shrink: 0;
  /* 层级1：容器层 - 浅灰背景，右侧阴影 */
}

.chat-panel {
  flex: 1;
  min-width: 0;
  transition: width 0.3s ease;
  /* 层级2：内容层 - 白色背景 */
}

.chat-area.with-preview .chat-panel {
  width: 50%;
  flex: 0 0 50%;
}

.preview-panel {
  @apply flex flex-col border-l border-gray-200 bg-white;
  width: 50%;
  flex-shrink: 0;
  /* 层级2：内容层 - 白色背景，左侧边框 */
  box-shadow: -2px 0 4px rgba(0, 0, 0, 0.04);
}

.preview-header {
  @apply flex items-center justify-between px-4 py-3 border-b border-gray-200;
  /* 层级2：内容层 - 白色背景，底部边框 */
}

.preview-title {
  @apply text-sm font-semibold text-gray-900;
}

.preview-close {
  @apply w-6 h-6 flex items-center justify-center text-gray-400 hover:text-gray-600 cursor-pointer transition-colors duration-200;
  font-size: 20px;
  line-height: 1;
}

.preview-close:hover {
  @apply bg-gray-100 rounded;
}

.preview-content {
  @apply flex-1 overflow-y-auto p-4;
}

.preview-placeholder {
  @apply text-sm text-gray-400 text-center py-8;
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .conversation-list {
    width: 200px;
  }
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .conversation-list {
    width: 280px;
  }
  
  .chat-area.with-preview .chat-panel {
    width: 0;
    flex: 0 0 0;
    overflow: hidden;
  }
  
  .chat-area.with-preview .preview-panel {
    width: 100%;
    flex: 1;
  }
}
</style>

