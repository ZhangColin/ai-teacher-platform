<template>
  <div class="chat-input">
    <textarea
      v-model="inputText"
      class="input-textarea"
      placeholder="输入消息..."
      rows="1"
      @keydown="handleKeyDown"
    ></textarea>
    <button class="send-button" :disabled="!inputText.trim()" @click="handleSend">
      发送
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  send: [content: string]
}>()

const inputText = ref('')

function handleKeyDown(event: KeyboardEvent) {
  // Enter发送，Shift+Enter换行
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSend()
  }
  // Shift+Enter 允许默认行为（换行）
}

function handleSend() {
  if (inputText.value.trim()) {
    emit('send', inputText.value.trim())
    inputText.value = ''
  }
}
</script>

<style scoped>
.chat-input {
  @apply flex items-end gap-3;
}

.input-textarea {
  @apply flex-1 px-4 py-3 border border-gray-300 rounded-xl text-sm resize-none min-h-[44px] max-h-[200px] leading-relaxed bg-white transition-all duration-200;
  /* 层级3：交互层 - 白色背景，轻微阴影，更柔和的边框 */
  font-family: inherit;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  border-color: theme('colors.gray.300');
}

.input-textarea:hover {
  border-color: theme('colors.gray.400');
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.input-textarea:focus {
  @apply outline-none border-primary-500;
  box-shadow: 0 0 0 3px theme('colors.primary.500 / 0.1'), 0 2px 4px rgba(0, 0, 0, 0.08);
}

.input-textarea::placeholder {
  @apply text-gray-400;
}

.send-button {
  @apply px-6 py-3 bg-primary-500 text-white border-none rounded-xl text-sm font-medium cursor-pointer transition-all duration-200 flex-shrink-0;
  /* 层级3：交互层 - 主色背景，明显阴影，添加hover提升效果 */
  box-shadow: 0 2px 4px theme('colors.primary.500 / 0.3'), 0 1px 2px rgba(0, 0, 0, 0.1);
}

.send-button:hover:not(:disabled) {
  @apply bg-primary-600;
  box-shadow: 0 4px 8px theme('colors.primary.500 / 0.4'), 0 2px 4px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.send-button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 4px theme('colors.primary.500 / 0.3'), 0 1px 2px rgba(0, 0, 0, 0.1);
}

.send-button:active:not(:disabled) {
  @apply scale-[0.98];
}

.send-button:disabled {
  @apply bg-gray-300 cursor-not-allowed;
  box-shadow: none;
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .chat-input {
    gap: 10px;
  }
  
  .input-textarea {
    padding: 11px 15px;
    font-size: 14px;
  }
  
  .send-button {
    padding: 11px 22px;
    font-size: 14px;
  }
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .chat-input {
    gap: 8px;
  }
  
  .input-textarea {
    padding: 10px 14px;
    font-size: 14px;
    min-height: 40px;
  }
  
  .send-button {
    padding: 10px 20px;
    font-size: 13px;
  }
}
</style>

