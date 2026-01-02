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
  display: flex;
  height: 100%;
  overflow: hidden;
}

.conversation-list {
  width: 240px;
  flex-shrink: 0;
}

.chat-panel {
  flex: 1;
  min-width: 0;
  transition: width 0.3s ease;
}

.chat-area.with-preview .chat-panel {
  width: 50%;
  flex: 0 0 50%;
}

.preview-panel {
  width: 50%;
  flex: 0 0 50%;
  display: flex;
  flex-direction: column;
  border-left: 1px solid #e5e7eb;
  background-color: #fafafa;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background-color: #ffffff;
}

.preview-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.preview-close {
  width: 28px;
  height: 28px;
  background-color: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 20px;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.preview-close:hover {
  background-color: #f3f4f6;
  color: #1f2937;
}

.preview-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.preview-placeholder {
  text-align: center;
  color: #9ca3af;
  font-size: 14px;
  padding: 48px 24px;
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

