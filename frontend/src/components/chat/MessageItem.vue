<template>
  <div
    class="message-item"
    :class="messageClass"
    data-testid="message-item"
  >
    <div class="message-avatar">
      <img
        :src="avatarUrl"
        :alt="message.role"
        class="avatar-image"
        data-testid="message-avatar"
      />
    </div>

    <div class="message-content">
      <div
        class="message-text"
        v-html="renderedContent"
        data-testid="message-text"
      />
      <div class="message-time" data-testid="message-time">
        {{ formattedTime }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { renderMarkdown } from '@/utils/markdownRenderer';
import type { Message } from '@/types';

interface Props {
  message: Message;
}

const props = defineProps<Props>();

const messageClass = computed(() => {
  return `message-${props.message.role}`;
});

const avatarUrl = computed(() => {
  return props.message.role === 'user'
    ? '/images/user-avatar.png'
    : '/images/ai-avatar.png';
});

const renderedContent = computed(() => {
  if (props.message.role === 'assistant') {
    return renderMarkdown(props.message.content);
  }
  return props.message.content;
});

const formattedTime = computed(() => {
  const date = new Date(props.message.created_at);
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  });
});
</script>

<style scoped>
.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.avatar-image {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 70%;
}

.message-user .message-content {
  align-items: flex-end;
}

.message-text {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

.message-user .message-text {
  background-color: #1890ff;
  color: white;
}

.message-assistant .message-text {
  background-color: #f5f5f5;
  color: #333;
}

.message-text :deep(p) {
  margin: 0;
}

.message-text :deep(pre) {
  background-color: #2d2d2d;
  color: #ccc;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.message-time {
  font-size: 12px;
  color: #999;
  padding: 0 4px;
}
</style>
