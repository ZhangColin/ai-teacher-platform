<template>
  <div class="preview-toolbar" data-testid="preview-toolbar">
    <button
      v-if="showMarkdownDownload"
      class="toolbar-btn"
      @click="handleDownloadMarkdown"
      data-testid="btn-download-markdown"
      title="下载 Markdown"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span class="btn-text">Markdown</span>
    </button>

    <button
      v-if="showMarkdownDownload"
      class="toolbar-btn"
      @click="handleDownloadWord"
      :disabled="isDownloadingWord"
      data-testid="btn-download-word"
      title="下载 Word"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span class="btn-text">{{ isDownloadingWord ? '转换中...' : 'Word' }}</span>
    </button>

    <button
      v-if="showMarkdownDownload"
      class="toolbar-btn"
      @click="handleDownloadPDF"
      :disabled="isDownloadingPDF"
      data-testid="btn-download-pdf"
      title="下载 PDF"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span class="btn-text">{{ isDownloadingPDF ? '生成中...' : 'PDF' }}</span>
    </button>

    <button
      v-if="showSvgDownload"
      class="toolbar-btn"
      @click="handleDownloadSvg"
      data-testid="btn-download-svg"
      title="下载 SVG"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span class="btn-text">SVG</span>
    </button>

    <button
      class="toolbar-btn"
      @click="handleToggleFullscreen"
      data-testid="btn-toggle-fullscreen"
      :title="isFullscreen ? '退出全屏' : '全屏'"
    >
      <svg v-if="!isFullscreen" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
      </svg>
      <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path>
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

interface Props {
  artifactType: string;
  isFullscreen?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isFullscreen: false,
});

const emit = defineEmits<{
  downloadMarkdown: [];
  downloadWord: [];
  downloadPDF: [];
  downloadSvg: [];
  toggleFullscreen: [];
}>();

const isDownloadingWord = ref(false);
const isDownloadingPDF = ref(false);

const showMarkdownDownload = computed(() => {
  return props.artifactType === 'markdown';
});

const showSvgDownload = computed(() => {
  return props.artifactType === 'svg';
});

const handleDownloadMarkdown = () => {
  emit('downloadMarkdown');
};

const handleDownloadWord = async () => {
  isDownloadingWord.value = true;
  try {
    emit('downloadWord');
  } finally {
    // 延迟重置状态，避免闪烁
    setTimeout(() => {
      isDownloadingWord.value = false;
    }, 1000);
  }
};

const handleDownloadPDF = async () => {
  isDownloadingPDF.value = true;
  try {
    emit('downloadPDF');
  } finally {
    setTimeout(() => {
      isDownloadingPDF.value = false;
    }, 1000);
  }
};

const handleDownloadSvg = () => {
  emit('downloadSvg');
};

const handleToggleFullscreen = () => {
  emit('toggleFullscreen');
};
</script>

<style scoped>
.preview-toolbar {
  display: flex;
  gap: 8px;
  padding: 8px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  align-items: center;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background-color: white;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}

.toolbar-btn:hover:not(:disabled) {
  background-color: #f0f0f0;
  border-color: #1890ff;
  color: #1890ff;
}

.toolbar-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-text {
  font-size: 13px;
}
</style>
