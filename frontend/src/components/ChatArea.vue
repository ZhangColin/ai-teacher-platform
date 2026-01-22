<template>
  <div class="chat-area" :class="{ 'with-preview': showPreview, 'conversation-collapsed': conversationListCollapsed }">
    <!-- 左侧：历史对话列表 -->
    <ConversationList 
      ref="conversationListRef"
      :tool-id="toolId"
      :collapsed="conversationListCollapsed"
      class="conversation-list" 
      :class="{ collapsed: conversationListCollapsed }"
      @conversation-change="handleConversationChange"
      @new-conversation="handleNewConversation"
    />
    
    
    <!-- 中间：当前对话区域 -->
    <ChatPanel 
      :tool-id="toolId"
      :welcome-message="welcomeMessage"
      :session-id="currentSessionId ?? undefined"
      :conversation-collapsed="conversationListCollapsed"
      class="chat-panel"
      :style="showPreview ? { width: chatPanelWidth + 'px' } : {}"
      @send="handleSendMessage" 
      @preview="openPreview" 
    />
    
    <!-- 可拖拽的分隔条 -->
    <div 
      v-if="showPreview"
      class="resizer"
      @mousedown="startResize"
    >
      <div class="resizer-handle"></div>
    </div>
    
    <!-- 右侧：预览区域 -->
    <PreviewPanel 
      v-if="showPreview" 
      :artifact="currentArtifact"
      class="preview-panel"
      @close="closePreview"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import ConversationList from './ConversationList.vue'
import ChatPanel from './ChatPanel.vue'
import PreviewPanel from './PreviewPanel.vue'
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
const conversationListCollapsed = ref(false)
const conversationListRef = ref<InstanceType<typeof ConversationList> | null>(null)

// 拖拽相关
const chatPanelWidth = ref<number>(0)
const isResizing = ref(false)
const containerWidth = ref<number>(0)

// function toggleConversationList() {
//   conversationListCollapsed.value = !conversationListCollapsed.value
// }

// 监听工具切换，清空当前会话
watch(() => props.toolId, (newToolId) => {
  if (newToolId) {
    currentSessionId.value = null
    showPreview.value = false
    currentArtifact.value = null
    sessionStore.initTool(newToolId)
  }
})

// 监听 sessionStore 的 sessionId 变化（新会话创建）
watch(() => sessionStore.sessionId, async (newId, oldId) => {
  if (newId && !oldId) {
    // 新会话创建了
    console.log('检测到新会话创建:', newId)
    
    // 更新当前会话ID
    currentSessionId.value = newId
    
    // 刷新会话列表
    if (conversationListRef.value) {
      await conversationListRef.value.loadConversations()
      // 设置为当前选中的会话
      conversationListRef.value.setCurrentConversation(newId)
    }
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

function handleSendMessage(_content: string) {
  // 消息发送由 ChatPanel 通过 sessionStore 处理
  // 这里可以添加额外的处理逻辑
}

function openPreview(artifact: Artifact) {
  currentArtifact.value = artifact
  showPreview.value = true
  // 打开预览时，初始化聊天面板宽度为 1/3
  updateContainerWidth()
  chatPanelWidth.value = containerWidth.value / 3
}

function closePreview() {
  showPreview.value = false
  currentArtifact.value = null
}

// 拖拽调整宽度
function startResize(e: MouseEvent) {
  isResizing.value = true
  e.preventDefault()
  
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function handleResize(e: MouseEvent) {
  if (!isResizing.value) return
  
  const chatArea = document.querySelector('.chat-area') as HTMLElement
  if (!chatArea) return
  
  const rect = chatArea.getBoundingClientRect()
  const conversationList = document.querySelector('.conversation-list') as HTMLElement
  const conversationListWidth = conversationList?.offsetWidth || 0
  
  // 计算新的聊天面板宽度（相对于容器左边）
  let newWidth = e.clientX - rect.left - conversationListWidth
  
  // 限制最小和最大宽度
  const minChatWidth = 300 // 最小 300px
  const maxChatWidth = containerWidth.value - 400 // 至少给预览区留 400px
  
  newWidth = Math.max(minChatWidth, Math.min(newWidth, maxChatWidth))
  
  chatPanelWidth.value = newWidth
}

function stopResize() {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

function updateContainerWidth() {
  const chatArea = document.querySelector('.chat-area') as HTMLElement
  if (chatArea) {
    const conversationList = document.querySelector('.conversation-list') as HTMLElement
    const conversationListWidth = conversationList?.offsetWidth || 0
    containerWidth.value = chatArea.offsetWidth - conversationListWidth
  }
}

// 监听窗口大小变化
onMounted(() => {
  window.addEventListener('resize', updateContainerWidth)
  updateContainerWidth()
})

onUnmounted(() => {
  window.removeEventListener('resize', updateContainerWidth)
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
})

// 监听工具切换或会话切换，关闭预览
watch(() => props.toolId, () => {
  showPreview.value = false
  currentArtifact.value = null
})

watch(() => currentSessionId.value, () => {
  showPreview.value = false
  currentArtifact.value = null
})
</script>

<style scoped>
.chat-area {
  @apply flex h-full overflow-hidden bg-white;
  /* 层级2：内容层 - 白色背景，轻微阴影 */
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.04);
  position: relative;
}

.chat-panel {
  flex: 1;
  min-width: 0;
  transition: padding-left 0.3s ease;
  /* 层级2：内容层 - 白色背景 */
  position: relative;
  overflow: hidden;
}

/* 当显示预览时，聊天面板不使用 flex，而是固定宽度 */
.chat-area.with-preview .chat-panel {
  flex: 0 0 auto;
}

/* 当历史列表收起时，增加左边距，避免图标压到文字 */
.chat-area.conversation-collapsed .chat-panel :deep(.messages-area) {
  padding-left: 80px !important;
}

.chat-area.conversation-collapsed .chat-panel :deep(.input-area) {
  padding-left: 80px !important;
}

/* 可拖拽的分隔条 */
.resizer {
  @apply flex-shrink-0 bg-gray-200 cursor-col-resize relative;
  width: 4px;
  transition: background-color 0.2s;
  z-index: 10;
}

.resizer:hover {
  @apply bg-primary-400;
}

.resizer-handle {
  @apply absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-gray-400 rounded-full;
  width: 4px;
  height: 40px;
  pointer-events: none;
  transition: background-color 0.2s;
}

.resizer:hover .resizer-handle {
  @apply bg-primary-500;
}

/* 预览面板：flex 布局 */
.preview-panel {
  @apply flex flex-col bg-white overflow-hidden;
  flex: 1;
  min-width: 400px;
  /* 层级2：内容层 - 白色背景 */
}


/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .preview-panel {
    min-width: 350px;
  }
  
  .resizer {
    width: 3px;
  }
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .conversation-list {
    width: 280px;
  }
  
  /* 移动端：隐藏聊天面板，预览全屏 */
  .chat-area.with-preview .chat-panel {
    display: none;
  }
  
  .chat-area.with-preview .resizer {
    display: none;
  }
  
  .preview-panel {
    flex: 1;
    min-width: 100%;
  }
}
</style>

