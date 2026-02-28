<template>
  <div
    class="message-item message-assistant streaming"
    data-testid="streaming-message"
  >
    <div class="message-avatar">
      <img
        src="/images/ai-avatar.png"
        alt="AI"
        class="avatar-image"
      />
    </div>

    <div class="message-content">
      <div
        class="message-text markdown-content"
        v-html="renderedContent"
        data-testid="streaming-text"
      />
      <div class="streaming-indicator" data-testid="streaming-indicator">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { renderMarkdown } from '@/utils/markdownRenderer';

interface Props {
  content: string;
}

const props = defineProps<Props>();

const renderedContent = computed(() => {
  if (!props.content) return '';
  return renderMarkdown(props.content);
});
</script>

<style scoped>
@import '@/styles/markdown.css';

.message-item.streaming {
  opacity: 0.9;
}

.streaming-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
  align-items: center;
}

.dot {
  width: 6px;
  height: 6px;
  background-color: #1890ff;
  border-radius: 50%;
  animation: pulse 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes pulse {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
