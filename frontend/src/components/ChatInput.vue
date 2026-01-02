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
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.input-textarea {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #d1d5db;
  border-radius: 12px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  min-height: 44px;
  max-height: 200px;
  line-height: 1.6;
  background-color: #ffffff;
  transition: all 0.2s;
}

.input-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-textarea::placeholder {
  color: #9ca3af;
}

.send-button {
  padding: 12px 24px;
  background-color: #3b82f6;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  box-shadow: 0 1px 2px rgba(59, 130, 246, 0.2);
}

.send-button:hover:not(:disabled) {
  background-color: #2563eb;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.send-button:active:not(:disabled) {
  transform: scale(0.98);
}

.send-button:disabled {
  background-color: #d1d5db;
  cursor: not-allowed;
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

