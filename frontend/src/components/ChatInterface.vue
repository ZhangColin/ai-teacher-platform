<template>
  <div class="chat-interface" :class="{ 'with-preview': showPreview }">
    <!-- 左侧：对话区 -->
    <div class="chat-panel">
      <div class="chat-header">
        <h2 class="chat-title">对话</h2>
        <button v-if="sessionStore.hasSession" class="clear-button" @click="handleClearSession">
          清空会话
        </button>
      </div>
      <MessageList
        :messages="sessionStore.messages"
        :loading="sessionStore.loading"
        @preview="handlePreview"
        @retry="handleRetry"
      />
      <InputArea
        :loading="sessionStore.loading"
        :disabled="sessionStore.loading"
        @send="handleSendMessage"
      />
    </div>

    <!-- 右侧：预览区 -->
    <PreviewPanel
      v-if="showPreview"
      :artifact="sessionStore.currentPreviewArtifact"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useSessionStore } from '../stores/sessionStore'
import { saveSession, updateSession, restoreSession, deleteSession } from '../utils/sessionStorage'
import MessageList from './MessageList.vue'
import InputArea from './InputArea.vue'
import PreviewPanel from './PreviewPanel.vue'
import type { Artifact, Message } from '../types'

const props = defineProps<{
  agentId: string
}>()

const sessionStore = useSessionStore()

const showPreview = computed(() => sessionStore.showPreview)

/**
 * 初始化会话
 */
async function initSession() {
  // 先尝试恢复会话
  const savedSession = restoreSession(props.agentId)
  
  if (savedSession && savedSession.sessionId) {
    // 恢复会话状态
    sessionStore.sessionId = savedSession.sessionId
    sessionStore.agentId = savedSession.agentId
    sessionStore.messages = savedSession.messages
    // 注意：uiConfig 需要从后端获取，这里使用默认配置
    // 如果需要完整的 uiConfig，应该重新创建会话或从后端获取
    if (!sessionStore.uiConfig) {
      sessionStore.uiConfig = {
        show_preview: true,
        preview_types: ['markdown', 'html', 'svg'],
      }
    }
  } else {
    // 创建新会话
    try {
      await sessionStore.createSession(props.agentId)
      // 保存会话
      if (sessionStore.sessionId && sessionStore.agentId) {
        saveSession(
          sessionStore.agentId,
          sessionStore.sessionId,
          sessionStore.messages
        )
      }
    } catch (error) {
      console.error('创建会话失败:', error)
    }
  }
}

/**
 * 处理发送消息
 */
async function handleSendMessage(content: string) {
  try {
    await sessionStore.sendMessage(content)
    // 更新会话存储
    if (sessionStore.sessionId && sessionStore.agentId) {
      updateSession(sessionStore.agentId, sessionStore.messages)
    }
  } catch (error) {
    // 错误已经在 store 中处理，这里不需要额外处理
    // 但需要更新会话存储（保存失败的消息）
    if (sessionStore.sessionId && sessionStore.agentId) {
      updateSession(sessionStore.agentId, sessionStore.messages)
    }
  }
}

/**
 * 处理重发消息
 */
async function handleRetry(message: Message) {
  // 移除错误状态，重新发送
  const messageIndex = sessionStore.messages.findIndex((m) => m === message)
  if (messageIndex !== -1) {
    // 移除错误消息
    sessionStore.messages.splice(messageIndex, 1)
    // 重新发送
    await handleSendMessage(message.content)
  }
}

/**
 * 处理清空会话
 */
function handleClearSession() {
  if (confirm('确定要清空当前会话吗？清空后对话历史和预览内容都将被删除。')) {
    sessionStore.clearSession()
    // 删除本地存储
    if (props.agentId) {
      deleteSession(props.agentId)
    }
    // 重新初始化会话
    initSession()
  }
}

/**
 * 处理预览
 */
function handlePreview(artifact: Artifact | null) {
  sessionStore.setPreviewArtifact(artifact)
}

/**
 * 监听 agentId 变化，重新初始化会话
 */
watch(
  () => props.agentId,
  () => {
    initSession()
  },
  { immediate: false }
)

onMounted(() => {
  initSession()
})
</script>

<style scoped>
.chat-interface {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.chat-interface.with-preview {
  display: grid;
  grid-template-columns: 1fr 1fr;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  background-color: white;
}

.chat-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.clear-button {
  padding: 0.5rem 1rem;
  background-color: #ef4444;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-button:hover {
  background-color: #dc2626;
}

.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  border-right: 1px solid #e5e7eb;
}

.chat-interface:not(.with-preview) .chat-panel {
  width: 100%;
  border-right: none;
}
</style>

