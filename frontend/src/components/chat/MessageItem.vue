<template>
  <div
    class="message-item"
    :class="messageClass"
    data-testid="message-item"
    :data-role="message.role"
    @mouseenter="showToolbar = true"
    @mouseleave="showToolbar = false"
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
        :class="{ 'markdown-content': message.role === 'assistant' }"
        v-html="renderedContent"
        data-testid="message-text"
      />
      <div class="message-time" data-testid="message-time">
        {{ formattedTime }}
      </div>
    </div>

    <Transition name="fade">
      <div v-if="showToolbar" class="message-toolbar">
        <button
          class="copy-button"
          @click="handleCopy"
          title="复制"
          data-testid="copy-button"
        >
          <DocumentDuplicateIcon />
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { DocumentDuplicateIcon } from '@heroicons/vue/24/outline';
import { renderMarkdown } from '@/utils/markdownRenderer';
import { useClipboard } from '@/composables/useClipboard';
import type { Message } from '@/types';

interface Props {
  message: Message;
}

const props = defineProps<Props>();

const showToolbar = ref(false);
const { copy } = useClipboard();

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
  if (!props.message.created_at) return '';
  const date = new Date(props.message.created_at);
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  });
});

async function handleCopy() {
  await copy(props.message.content);
}
</script>

<style scoped>
@import '@/styles/markdown.css';

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease-in;
  position: relative;
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

/* Assistant messages use markdown-content class for rich formatting */
.message-assistant .message-text {
  overflow-x: auto;
}

.message-time {
  font-size: 12px;
  color: #999;
  padding: 0 4px;
}

.message-toolbar {
  position: absolute;
  top: -30px;
  right: 0;
  display: flex;
  gap: 4px;
  z-index: 10;
}

.message-user .message-toolbar {
  right: auto;
  left: 0;
}

.copy-button {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
  padding: 0;
}

.copy-button:hover {
  background: rgba(0, 0, 0, 0.9);
}

.copy-button svg {
  width: 16px;
  height: 16px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
