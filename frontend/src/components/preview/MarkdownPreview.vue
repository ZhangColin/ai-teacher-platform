<template>
  <div
    id="markdown-preview-content"
    class="markdown-preview"
    v-html="renderedHtml"
    data-testid="markdown-preview"
  />
  <div v-if="hasError" class="markdown-error" data-testid="markdown-error">
    Markdown 渲染失败，请检查内容格式
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { renderMarkdown } from '@/utils/markdownRenderer';

interface Props {
  content: string;
}

const props = defineProps<Props>();
const hasError = ref(false);

const renderedHtml = computed(() => {
  if (!props.content) return '';

  try {
    const result = renderMarkdown(props.content);
    hasError.value = false;
    return result;
  } catch (error) {
    console.error('Markdown rendering failed:', error);
    hasError.value = true;
    return '';
  }
});
</script>

<style scoped>
.markdown-preview {
  line-height: 1.6;
  color: #333;
}

.markdown-preview :deep(h1) {
  font-size: 2em;
  font-weight: bold;
  margin: 0.67em 0;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.3em;
}

.markdown-preview :deep(h2) {
  font-size: 1.5em;
  font-weight: bold;
  margin: 0.75em 0;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.3em;
}

.markdown-preview :deep(p) {
  margin: 1em 0;
}

.markdown-preview :deep(code) {
  background-color: #f4f4f4;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
}

.markdown-preview :deep(pre) {
  background-color: #f4f4f4;
  padding: 1em;
  border-radius: 5px;
  overflow-x: auto;
}

.markdown-preview :deep(pre code) {
  background-color: transparent;
  padding: 0;
}
</style>
