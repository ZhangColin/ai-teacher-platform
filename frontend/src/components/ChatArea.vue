<template>
  <div class="chat-area" :class="{ 'with-preview': showPreview }">
    <!-- 左侧：历史对话列表 -->
    <ConversationList 
      :tool-id="toolId"
      class="conversation-list" 
      @conversation-change="handleConversationChange"
      @new-conversation="handleNewConversation"
    />
    
    <!-- 中间：当前对话区域 -->
    <ChatPanel 
      :tool-id="toolId"
      :welcome-message="welcomeMessage"
      :session-id="currentSessionId"
      class="chat-panel" 
      @send="handleSendMessage" 
      @preview="openPreview" 
    />
    
    <!-- 右侧：预览区域 -->
    <div v-if="showPreview && currentArtifact" class="preview-panel">
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
import { ref, watch } from 'vue'
import ConversationList from './ConversationList.vue'
import ChatPanel from './ChatPanel.vue'
import { useSessionStore } from '../stores/sessionStore'
import type { Artifact } from '../types'

const props = defineProps<{
  toolId?: string
  welcomeMessage?: string
}>()

const sessionStore = useSessionStore()
const currentSessionId = ref<string | null>(null)
const showPreview = ref(false)
const currentArtifact = ref<Artifact | null>(null)

// 监听工具切换，清空当前会话
watch(() => props.toolId, (newToolId) => {
  if (newToolId) {
    currentSessionId.value = null
    showPreview.value = false
    currentArtifact.value = null
    sessionStore.initTool(newToolId)
  }
})

function handleConversationChange(sessionId: string) {
  currentSessionId.value = sessionId
  showPreview.value = false
  currentArtifact.value = null
}

function handleNewConversation() {
  currentSessionId.value = null
  showPreview.value = false
  currentArtifact.value = null
  sessionStore.clearSession()
}

function handleSendMessage(content: string) {
  // 消息发送由 ChatPanel 通过 sessionStore 处理
  // 这里可以添加额外的处理逻辑
}

function openPreview(artifact: Artifact) {
  currentArtifact.value = artifact
  showPreview.value = true
}

function closePreview() {
  showPreview.value = false
  currentArtifact.value = null
}
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

