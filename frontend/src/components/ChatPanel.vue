<template>
  <div class="chat-panel" data-testid="chat-panel">
    <MessageList
      ref="messageListRef"
      :messages="messages"
      :streaming-content="streamingContent"
      :auto-scroll="autoScroll"
    />

    <ChatInput
      ref="chatInputRef"
      :disabled="disabled"
      :is-loading="isLoading"
      @send="handleSend"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import MessageList from './chat/MessageList.vue';
import ChatInput from './chat/ChatInput.vue';
import type { Message } from '@/types';

interface Props {
  messages?: Message[];
  streamingContent?: string;
  disabled?: boolean;
  isLoading?: boolean;
  autoScroll?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  messages: () => [],
  streamingContent: '',
  disabled: false,
  isLoading: false,
  autoScroll: true,
});

const emit = defineEmits<{
  send: [content: string];
}>();

const messageListRef = ref<InstanceType<typeof MessageList>>();
const chatInputRef = ref<InstanceType<typeof ChatInput>>();

const handleSend = (content: string) => {
  emit('send', content);
};

// 聚焦输入框
const focusInput = () => {
  chatInputRef.value?.focus();
};

// 滚动到底部
const scrollToBottom = () => {
  messageListRef.value?.scrollToBottom();
};

defineExpose({
  focusInput,
  scrollToBottom,
});
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f5f5f5;
}
</style>
