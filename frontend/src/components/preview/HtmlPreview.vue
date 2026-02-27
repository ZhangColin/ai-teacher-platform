<template>
  <div class="html-preview-wrapper">
    <iframe
      v-if="sanitizedHtml"
      :srcdoc="sanitizedHtml"
      class="html-preview-iframe"
      sandbox="allow-scripts allow-same-origin"
      data-testid="html-preview-iframe"
    />
    <div v-else class="html-preview-empty" data-testid="html-preview-empty">
      No HTML content
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import DOMPurify from 'dompurify';

interface Props {
  content: string;
}

const props = defineProps<Props>();

const sanitizedHtml = computed(() => {
  if (!props.content) return '';

  // 使用DOMPurify清理HTML，防止XSS攻击
  return DOMPurify.sanitize(props.content, {
    // 允许的标签
    ALLOWED_TAGS: [
      'a', 'b', 'br', 'div', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'hr', 'i', 'img', 'li', 'ol', 'p', 'span', 'strong', 'ul',
      'table', 'thead', 'tbody', 'tr', 'td', 'th',
    ],
    // 允许的属性
    ALLOWED_ATTR: ['href', 'src', 'alt', 'class', 'id', 'style'],
    // 允许的URI协议
    ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i,
  });
});
</script>

<style scoped>
.html-preview-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.html-preview-iframe {
  width: 100%;
  height: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: #fff;
}

.html-preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-style: italic;
}
</style>
