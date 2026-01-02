<template>
  <div class="chat-panel">
    <!-- 欢迎语区域（仅在没有消息时显示） -->
    <div v-if="messages.length === 0" class="welcome-area">
      <WelcomeMessage />
    </div>
    
    <!-- 对话内容区域 -->
    <div v-if="messages.length > 0" class="messages-area">
      <div 
        v-for="message in messages" 
        :key="message.id" 
        :class="['message-item', message.role]"
      >
        <div class="message-role">{{ message.role === 'user' ? '你' : 'AI' }}</div>
        <div class="message-content">{{ message.content }}</div>
        <button v-if="message.role === 'assistant'" class="preview-btn" @click="handlePreview">
          预览
        </button>
      </div>
    </div>
    
    <!-- 输入框区域 -->
    <div class="input-area">
      <ChatInput @send="handleSendMessage" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import WelcomeMessage from './WelcomeMessage.vue'
import ChatInput from './ChatInput.vue'

const props = defineProps<{
  conversationId?: string
}>()

const emit = defineEmits<{
  send: [content: string]
  preview: []
}>()

// 写死的对话数据（根据conversationId切换）
const conversationMessages: Record<string, Array<{ id: string; role: string; content: string }>> = {
  'conv-1': [
    {
      id: 'msg-1',
      role: 'assistant',
      content: '你好！我是AI助手，可以帮助你处理各种任务。',
    },
    {
      id: 'msg-2',
      role: 'user',
      content: '请帮我优化一下提示词',
    },
  ],
  'conv-2': [
    {
      id: 'msg-3',
      role: 'assistant',
      content: '关于产品设计，我们可以从用户体验的角度来思考...',
    },
  ],
  'conv-3': [
    {
      id: 'msg-4',
      role: 'assistant',
      content: '前端架构的选择需要考虑多个因素...',
    },
  ],
  'conv-4': [
    {
      id: 'msg-5',
      role: 'assistant',
      content: '代码重构是一个渐进的过程...',
    },
  ],
}

const messages = ref<Array<{ id: string; role: string; content: string }>>(
  conversationMessages[props.conversationId || 'conv-1'] || []
)

// 监听对话切换
watch(() => props.conversationId, (newId) => {
  if (newId) {
    messages.value = conversationMessages[newId] || []
  }
}, { immediate: true })

function handleSendMessage(content: string) {
  // 添加用户消息
  messages.value.push({
    id: `msg-${Date.now()}`,
    role: 'user',
    content,
  })
  emit('send', content)
  // 当前迭代不添加AI回复，后续实现
}

function handlePreview() {
  emit('preview')
}
</script>

<style scoped>
.chat-panel {
  @apply flex flex-col h-full overflow-hidden bg-white;
}

.welcome-area {
  @apply py-16 px-6 flex-shrink-0; /* 从py-12(48px)增加到py-16(64px)，更大气 */
}

.messages-area {
  @apply flex-1 overflow-y-auto px-6 py-8 flex flex-col gap-8; /* 从py-6(24px)增加到py-8(32px)，gap从6增加到8 */
  scroll-behavior: smooth;
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

