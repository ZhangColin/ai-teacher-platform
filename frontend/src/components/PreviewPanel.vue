<template>
  <div class="preview-panel" :class="{ 'is-fullscreen': isFullscreen }" data-testid="preview-panel">
    <PreviewToolbar
      :artifact-type="artifact?.type || ''"
      :is-fullscreen="isFullscreen"
      @download-markdown="handleDownloadMarkdown"
      @download-word="handleDownloadWord"
      @download-pdf="handleDownloadPDF"
      @download-svg="handleDownloadSvg"
      @toggle-fullscreen="toggleFullscreen"
    />

    <div class="preview-content" data-testid="preview-content">
      <MarkdownPreview
        v-if="artifact?.type === 'markdown'"
        :content="artifact.content"
      />

      <HtmlPreview
        v-else-if="artifact?.type === 'html'"
        :content="artifact.content"
      />

      <SvgPreview
        v-else-if="isSvgArtifact(artifact)"
        :content="artifact.content"
        :filename="artifact.filename || 'artifact.svg'"
      />

      <div v-else class="preview-empty" data-testid="preview-empty">
        暂无预览内容
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import MarkdownPreview from './preview/MarkdownPreview.vue';
import HtmlPreview from './preview/HtmlPreview.vue';
import SvgPreview from './preview/SvgPreview.vue';
import PreviewToolbar from './preview/PreviewToolbar.vue';
import type { Artifact } from '@/types';

interface Props {
  artifact: Artifact | null;
}

const props = defineProps<Props>();

const isFullscreen = ref(false);

const isSvgArtifact = (artifact: Artifact | null): boolean => {
  return artifact?.type === 'svg' || artifact?.type === 'image/svg+xml';
};

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};

const handleDownloadMarkdown = () => {
  if (!props.artifact?.content) return;

  const blob = new Blob([props.artifact.content], { type: 'text/markdown' });
  downloadBlob(blob, 'artifact.md');
};

const handleDownloadWord = async () => {
  // TODO: 实现Word转换逻辑
  console.log('Download Word - to be implemented');
};

const handleDownloadPDF = async () => {
  // TODO: 实现PDF生成逻辑
  console.log('Download PDF - to be implemented');
};

const handleDownloadSvg = () => {
  if (!props.artifact?.content) return;

  const blob = new Blob([props.artifact.content], { type: 'image/svg+xml' });
  downloadBlob(blob, 'artifact.svg');
};

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};
</script>

<style scoped>
.preview-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.preview-panel.is-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  border-radius: 0;
}

.preview-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-style: italic;
}
</style>
