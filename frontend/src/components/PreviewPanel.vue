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
      @coming-soon="handleComingSoon"
    />

    <!-- 简单的通知提示 -->
    <div
      v-if="notification"
      class="notification"
      :class="{ 'notification-show': notification }"
      data-testid="notification"
    >
      {{ notification }}
    </div>

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
import { ref } from 'vue';
import MarkdownPreview from './preview/MarkdownPreview.vue';
import HtmlPreview from './preview/HtmlPreview.vue';
import SvgPreview from './preview/SvgPreview.vue';
import PreviewToolbar from './preview/PreviewToolbar.vue';
import { useFileDownload } from '@/composables/useFileDownload';
import { downloadWord } from '@/utils/documentDownloader';
import type { Artifact } from '@/types';

interface Props {
  artifact: Artifact | null;
}

const props = defineProps<Props>();

const isFullscreen = ref(false);
const notification = ref('');
const notificationTimer = ref<number | null>(null);
const { downloadBlob } = useFileDownload();

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
  if (!props.artifact?.content || props.artifact.type !== 'markdown') return;

  try {
    // Generate filename from artifact title or use default
    const filename = `document-${Date.now()}.docx`;
    await downloadWord(props.artifact.content, filename);
    showNotification('Word 文档下载成功！');
  } catch (error) {
    console.error('Word 下载失败:', error);
    showNotification('Word 文档下载失败，请重试');
  }
};

const handleDownloadPDF = async () => {
  // 由 PreviewToolbar 触发 comingSoon 事件
};

const handleComingSoon = (message: string) => {
  showNotification(message);
};

const showNotification = (message: string) => {
  notification.value = message;

  // 清除之前的定时器
  if (notificationTimer.value) {
    clearTimeout(notificationTimer.value);
  }

  // 3秒后自动隐藏
  notificationTimer.value = window.setTimeout(() => {
    notification.value = '';
  }, 3000);
};

const handleDownloadSvg = () => {
  if (!props.artifact?.content) return;

  const blob = new Blob([props.artifact.content], { type: 'image/svg+xml' });
  downloadBlob(blob, 'artifact.svg');
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
  position: relative;
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

.notification {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%) translateY(20px);
  background-color: #1890ff;
  color: white;
  padding: 10px 20px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  opacity: 0;
  transition: all 0.3s ease;
  pointer-events: none;
  z-index: 100;
}

.notification-show {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
</style>
