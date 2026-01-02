<template>
  <div class="chat-panel">
    <!-- 欢迎语区域（仅在没有消息时显示） -->
    <div v-if="messages.length === 0" class="welcome-area">
      <WelcomeMessage />
    </div>
    
    <!-- 对话内容区域 -->
    <div v-if="messages.length > 0" class="messages-area">
      <div v-for="message in messages" :key="message.id" class="message-item">
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
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background-color: #ffffff;
}

.welcome-area {
  padding: 48px 24px;
  flex-shrink: 0;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  scroll-behavior: smooth;
}

.message-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 100%;
}

.message-role {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.message-content {
  font-size: 14px;
  color: #1f2937;
  line-height: 1.7;
  margin-bottom: 8px;
  word-wrap: break-word;
}

.preview-btn {
  padding: 6px 14px;
  background-color: #f3f4f6;
  color: #1f2937;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  align-self: flex-start;
}

.preview-btn:hover {
  background-color: #e5e7eb;
  border-color: #9ca3af;
  color: #111827;
}

.input-area {
  padding: 20px 24px;
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
  background-color: #ffffff;
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

