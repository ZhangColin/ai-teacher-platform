<template>
  <div class="chat-panel">
    <!-- 消息内容区域（包含欢迎语和消息，可滚动） -->
    <div 
      class="messages-area" 
      :class="{ 'conversation-collapsed': conversationCollapsed }"
      :style="conversationCollapsed ? { paddingLeft: '80px' } : {}"
    >
      <!-- 欢迎语（仅在没有消息时显示） -->
      <div v-if="sessionStore.messages.length === 0" class="welcome-area">
        <WelcomeMessage :welcome-message="welcomeMessage" />
      </div>
      
      <!-- 消息列表 -->
      <template v-for="(message, index) in sessionStore.messages" :key="`${message.role}-${index}-${message.content.slice(0, 10)}`">
        <!-- 用户消息：显示在聊天框里 -->
        <div v-if="message.role === 'user'" class="user-message-wrapper">
          <div class="user-message">
            <div class="user-message-content">{{ message.content }}</div>
          </div>
          <!-- 消息工具栏 -->
          <div class="message-toolbar">
            <button 
              class="toolbar-button" 
              @click="copyMessage(message.content)"
              title="复制消息"
            >
              <DocumentDuplicateIcon class="w-4 h-4" />
            </button>
          </div>
    </div>
    
        <!-- AI 消息：直接渲染 Markdown，充分利用页面 -->
        <div v-else class="assistant-message-wrapper">
      <div 
            :key="`markdown-${index}-${message.content.length}`"
            class="markdown-content prose prose-slate max-w-none"
            v-html="renderMarkdown(message.content, message.artifacts || [])"
            @click="handleMarkdownClick"
          ></div>
          <!-- AI 消息工具栏：显示在消息下方 -->
          <div class="assistant-message-toolbar">
            <button 
              class="assistant-toolbar-button" 
              @click="copyMessage(message.content)"
              title="复制消息"
            >
              <DocumentDuplicateIcon class="w-4 h-4" />
        </button>
          </div>
        </div>
      </template>
      
      <!-- 加载指示器 -->
      <div v-if="sessionStore.loading" class="loading-indicator">
        <div class="loading-typing">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <span class="loading-text">AI 正在思考...</span>
      </div>
      
      <!-- 错误提示 -->
      <div v-if="sessionStore.error" class="error-message">
        <div class="error-icon">⚠️</div>
        <div class="error-content">
          <div class="error-title">出错了</div>
          <div class="error-detail">{{ sessionStore.error }}</div>
          <button class="error-retry-btn" @click="handleRetry">重试</button>
        </div>
      </div>
    </div>
    
    <!-- 复制成功提示 -->
    <Transition name="toast">
      <div v-if="showCopyToast" class="copy-toast">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        <span>已复制到剪贴板</span>
      </div>
    </Transition>
    
    <!-- 输入框区域（固定在底部） -->
    <div 
      class="input-area" 
      :class="{ 'conversation-collapsed': conversationCollapsed }"
      :style="conversationCollapsed ? { paddingLeft: '80px' } : {}"
    >
      <ChatInput @send="handleSendMessage" :disabled="sessionStore.loading" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { DocumentDuplicateIcon } from '@heroicons/vue/24/outline'
import WelcomeMessage from './WelcomeMessage.vue'
import ChatInput from './ChatInput.vue'
import { useSessionStore } from '../stores/sessionStore'
import { renderMarkdown } from '../utils/markdownRenderer'
import type { Artifact } from '../types'

const props = defineProps<{
  toolId?: string
  welcomeMessage?: string
  sessionId?: string
  conversationCollapsed?: boolean
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
      // 恢复会话后，滚动到底部
      await nextTick()
      scrollToBottom()
    } catch (err) {
      console.error('恢复会话失败:', err)
    }
  }
}, { immediate: true })

// 监听消息变化，自动滚动到底部
watch(() => sessionStore.messages.length, async () => {
  await nextTick()
  scrollToBottom()
})

// 监听 loading 状态，显示加载提示时也滚动
watch(() => sessionStore.loading, async (isLoading) => {
  if (isLoading) {
    await nextTick()
    scrollToBottom()
  }
})

// 监听消息更新事件（收到完整回复后触发）
const handleMessageUpdated = () => {
  scrollToBottom()
}
window.addEventListener('message-updated', handleMessageUpdated)

// 组件卸载时清理事件监听
onUnmounted(() => {
  window.removeEventListener('message-updated', handleMessageUpdated)
})

async function handleSendMessage(content: string) {
  if (!props.toolId) {
    console.error('工具ID未设置，无法发送消息')
    return
  }
  
  // 确保工具已初始化（防止 watch 还未执行的情况）
  if (!sessionStore.toolId || sessionStore.toolId !== props.toolId) {
    sessionStore.initTool(props.toolId)
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
    // 滚动到底部以显示错误信息
    await nextTick()
    scrollToBottom()
  }
}

/**
 * 重试发送最后一条消息
 */
async function handleRetry() {
  const lastUserMessage = sessionStore.messages
    .slice()
    .reverse()
    .find(msg => msg.role === 'user')
  
  if (lastUserMessage && lastUserMessage.content) {
    // 移除错误状态和最后一条 AI 消息（如果有）
    sessionStore.error = null
    const lastIndex = sessionStore.messages.length - 1
    if (lastIndex >= 0 && sessionStore.messages[lastIndex]?.role === 'assistant') {
      sessionStore.messages.pop()
    }
    
    // 重新发送消息
    await handleSendMessage(lastUserMessage.content)
  }
}

/**
 * 滚动到底部（平滑滚动）
 */
function scrollToBottom() {
  const messagesArea = document.querySelector('.messages-area') as HTMLElement
  if (messagesArea) {
    // 使用 requestAnimationFrame 确保 DOM 更新完成
    requestAnimationFrame(() => {
      messagesArea.scrollTo({
        top: messagesArea.scrollHeight,
        behavior: 'smooth'
      })
    })
  }
}

/**
 * 处理 Markdown 内容中的预览按钮和复制按钮点击
 */
function handleMarkdownClick(event: Event) {
  const target = event.target as HTMLElement
  
  // 处理预览按钮点击 - 使用 closest 查找最近的按钮元素（更健壮）
  const previewButton = target.classList.contains('preview-button') 
    ? target 
    : target.closest('.preview-button') as HTMLElement
  
  if (previewButton) {
    event.preventDefault()
    event.stopPropagation()
    
    const artifactData = previewButton.getAttribute('data-artifact-content')
    if (artifactData) {
      try {
        const artifact: Artifact = JSON.parse(artifactData)
        
        // 添加视觉反馈
        previewButton.style.opacity = '0.6'
        setTimeout(() => {
          previewButton.style.opacity = '1'
        }, 150)
        
        emit('preview', artifact)
      } catch (error) {
        console.error('解析 artifact 数据失败:', error)
      }
    }
    return
  }
  
  // 处理代码块复制按钮点击
  if (target.classList.contains('copy-code-button') || target.closest('.copy-code-button')) {
    event.preventDefault()
    event.stopPropagation()
    
    const button = target.classList.contains('copy-code-button') ? target : target.closest('.copy-code-button') as HTMLElement
    const codeContent = button.getAttribute('data-code-content')
    if (codeContent) {
      copyToClipboard(unescapeHtml(codeContent))
    }
    return
  }
}

/**
 * 复制消息内容到剪贴板
 */
async function copyMessage(content: string) {
  await copyToClipboard(content)
}

// 复制成功提示状态
const showCopyToast = ref(false)
const copyToastTimer = ref<number | null>(null)

/**
 * 复制文本到剪贴板
 */
async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    showCopySuccessToast()
  } catch (err) {
    console.error('复制失败:', err)
    // 降级方案：使用传统方法
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    try {
      document.execCommand('copy')
      showCopySuccessToast()
    } catch (e) {
      console.error('复制失败:', e)
    }
    document.body.removeChild(textarea)
  }
}

/**
 * 显示复制成功提示
 */
function showCopySuccessToast() {
  showCopyToast.value = true
  // 清除之前的定时器
  if (copyToastTimer.value) {
    clearTimeout(copyToastTimer.value)
  }
  // 2秒后自动隐藏
  copyToastTimer.value = window.setTimeout(() => {
    showCopyToast.value = false
    copyToastTimer.value = null
  }, 2000)
}

// 组件卸载时清理定时器
onUnmounted(() => {
  if (copyToastTimer.value) {
    clearTimeout(copyToastTimer.value)
  }
})

/**
 * 反转义 HTML（用于提取代码块原始内容）
 */
function unescapeHtml(text: string): string {
  const map: Record<string, string> = {
    '&amp;': '&',
    '&lt;': '<',
    '&gt;': '>',
    '&quot;': '"',
    '&#039;': "'",
    '&nbsp;': ' ',
  }
  return text.replace(/&(?:amp|lt|gt|quot|#039|nbsp);/g, (m) => map[m] || m)
}

// 移除了 isShortMessage 函数，所有消息统一使用10栅格宽度，内容自然换行
</script>

<style scoped>
.chat-panel {
  @apply flex flex-col h-full overflow-hidden bg-white;
}

.messages-area {
  @apply flex-1 overflow-y-auto px-6 py-8 flex flex-col gap-8; /* 从py-6(24px)增加到py-8(32px)，gap从6增加到8 */
  scroll-behavior: smooth;
  min-height: 0; /* 确保 flex 子元素可以正确收缩 */
  transition: padding-left 0.3s ease;
}

/* 当历史列表收起时，增加左边距，避免图标压到文字 */
.messages-area.conversation-collapsed {
  padding-left: 80px !important; /* 增加左边距，为收起按钮留出空间，确保按钮和文字之间有一个字的距离 */
}

.welcome-area {
  @apply flex-1 flex items-center justify-center; /* 欢迎语居中显示 */
  min-height: 0;
}

/* 用户消息：显示在聊天框里，右侧对齐 - 参考 DeepSeek 样式 */
.user-message-wrapper {
  @apply flex justify-end mb-8 relative;
}

.user-message {
  @apply flex justify-end;
  /* 确保子元素可以自适应宽度 */
  min-width: 0;
}

.user-message-content {
  @apply text-sm leading-relaxed px-4 py-3 rounded-2xl bg-primary-500 text-white;
  /* 层级3：交互层 - 主色背景，明显阴影 */
  box-shadow: 0 2px 8px theme('colors.primary.500 / 0.3'), 0 1px 3px rgba(0, 0, 0, 0.1);
  /* 换行策略：保留用户换行，超出宽度自动换行 */
  word-break: normal;
  overflow-wrap: break-word;
  /* 保留用户输入的换行符，合并多余空格 */
  white-space: pre-line;
  /* 自适应内容宽度，但最大不超过10栅格（83.33%） */
  width: fit-content;
  max-width: clamp(200px, 83.33%, 900px);
  display: inline-block;
  /* 确保内容不会因为父容器 flex 布局而被压缩 */
  flex-shrink: 0;
}

/* AI 消息：直接渲染 Markdown，充分利用页面宽度 */
.assistant-message-wrapper {
  @apply w-full mb-8 relative;
}

.assistant-message {
  @apply w-full;
}

.markdown-content {
  @apply w-full;
  /* 使用 Tailwind Typography 插件样式 */
}

/* Markdown 内容样式优化 */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  @apply font-bold text-gray-900 mt-6 mb-4;
}

.markdown-content :deep(h1) {
  @apply text-3xl;
}

.markdown-content :deep(h2) {
  @apply text-2xl;
}

.markdown-content :deep(h3) {
  @apply text-xl;
}

.markdown-content :deep(p) {
  @apply text-gray-700 leading-7 mb-4;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  @apply mb-4 pl-6;
}

.markdown-content :deep(li) {
  @apply mb-2 text-gray-700;
}

.markdown-content :deep(blockquote) {
  @apply border-l-4 border-gray-300 pl-4 italic text-gray-600 my-4;
}

.markdown-content :deep(code) {
  @apply bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-sm font-mono;
}

.markdown-content :deep(pre) {
  @apply bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4;
}

.markdown-content :deep(pre code) {
  @apply bg-transparent text-gray-100 p-0;
}

.markdown-content :deep(a) {
  @apply text-primary-600 hover:text-primary-700 underline;
}

.markdown-content :deep(table) {
  @apply w-full border-collapse my-4;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  @apply border border-gray-300 px-4 py-2 text-left;
}

.markdown-content :deep(th) {
  @apply bg-gray-100 font-semibold;
}

.markdown-content :deep(img) {
  @apply max-w-full h-auto rounded-lg my-4;
}

/* 代码块样式 */
.markdown-content :deep(.code-block-wrapper) {
  @apply relative my-4;
  position: relative;
}

.markdown-content :deep(.code-block-wrapper pre) {
  @apply relative;
  margin: 0; /* 移除默认 margin，由 wrapper 控制 */
}

/* 代码块操作按钮组 */
.markdown-content :deep(.code-block-actions) {
  @apply absolute top-2 right-2 flex gap-1.5 opacity-70 transition-opacity duration-200 z-10;
}

.markdown-content :deep(.code-block-wrapper:hover .code-block-actions) {
  opacity: 1;
}

.markdown-content :deep(.preview-button),
.markdown-content :deep(.copy-code-button) {
  @apply w-7 h-7 flex items-center justify-center text-gray-300 hover:text-gray-100 hover:bg-gray-700 rounded cursor-pointer transition-all duration-150;
  background-color: rgba(31, 41, 55, 0.7); /* 与代码块背景色匹配，提高初始可见度 */
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.1); /* 添加边框增加可见度 */
}

.markdown-content :deep(.preview-button:hover),
.markdown-content :deep(.copy-code-button:hover) {
  background-color: rgba(31, 41, 55, 0.9);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.markdown-content :deep(.preview-button:active),
.markdown-content :deep(.copy-code-button:active) {
  transform: scale(0.95) translateY(0);
  background-color: rgba(31, 41, 55, 1);
}

/* 用户消息工具栏样式（保留原有hover效果） */
.user-message-wrapper {
  @apply relative;
  position: relative;
}

.user-message-wrapper .message-toolbar {
  @apply absolute -bottom-8 right-0 flex gap-1 opacity-60 transition-opacity duration-200 z-10;
}

.user-message-wrapper:hover .message-toolbar {
  opacity: 1;
}

.toolbar-button {
  @apply w-7 h-7 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded border border-gray-200 bg-white cursor-pointer transition-all duration-200;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.toolbar-button:hover {
  @apply bg-gray-50 border-gray-300;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toolbar-button:active {
  @apply scale-95;
}

/* AI 消息工具栏样式：显示在消息下方，低调风格 */
.assistant-message-wrapper {
  @apply relative;
  position: relative;
}

.assistant-message-toolbar {
  @apply flex justify-start mt-2 mb-1 opacity-60 transition-opacity duration-200;
}

.assistant-message-wrapper:hover .assistant-message-toolbar {
  opacity: 1;
}

.assistant-toolbar-button {
  @apply w-6 h-6 flex items-center justify-center text-gray-400 hover:text-gray-600 rounded cursor-pointer transition-all duration-200;
  background: transparent;
  border: none;
}

.assistant-toolbar-button:hover {
  @apply bg-gray-100;
}

.assistant-toolbar-button:active {
  @apply scale-95;
}

/* 加载指示器 - 参考 DeepSeek 样式 */
.loading-indicator {
  @apply flex flex-col items-center justify-center py-6 gap-3;
}

.loading-typing {
  @apply flex gap-1.5;
}

.loading-typing span {
  @apply w-2 h-2 bg-gray-400 rounded-full;
  animation: typing 1.4s infinite ease-in-out;
}

.loading-typing span:nth-child(1) {
  animation-delay: 0s;
}

.loading-typing span:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-typing span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
  transform: translateY(0);
    opacity: 0.7;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

.loading-text {
  @apply text-sm text-gray-500;
}

/* 错误提示 */
.error-message {
  @apply flex gap-4 p-4 bg-red-50 border border-red-200 rounded-lg mb-6;
}

.error-icon {
  @apply text-2xl flex-shrink-0;
}

.error-content {
  @apply flex-1;
}

.error-title {
  @apply text-sm font-semibold text-red-900 mb-1;
}

.error-detail {
  @apply text-sm text-red-700 mb-3;
}

.error-retry-btn {
  @apply px-4 py-2 bg-red-500 text-white border-none rounded-lg text-sm font-medium cursor-pointer transition-all duration-200;
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3);
}

.error-retry-btn:hover {
  @apply bg-red-600;
  box-shadow: 0 4px 8px rgba(239, 68, 68, 0.4);
}

.error-retry-btn:active {
  @apply scale-[0.98];
}

/* 复制成功提示 */
.copy-toast {
  @apply fixed bottom-6 left-1/2 transform -translate-x-1/2 flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg shadow-lg z-50;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translate(-50%, 20px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

.toast-enter-active {
  animation: slideUp 0.3s ease-out;
}

.toast-leave-active {
  animation: slideUp 0.3s ease-out reverse;
}

.input-area {
  @apply py-6 px-6 border-t border-gray-200 flex-shrink-0 bg-white;
  /* 层级2：内容层 - 白色背景，顶部边框 */
  /* 内边距保持24px (px-6)，已符合要求 */
  box-shadow: 0 -1px 3px rgba(0, 0, 0, 0.04);
  transition: padding-left 0.3s ease;
}

/* 当历史列表收起时，输入框也增加左边距 */
.input-area.conversation-collapsed {
  padding-left: 80px !important; /* 输入框也增加左边距，保持一致 */
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

