<template>
  <div class="preview-panel" data-testid="preview-panel">
    <div v-if="!artifact" class="preview-empty">
      <p>点击代码块上的"预览"按钮查看内容</p>
    </div>
    <div v-else-if="previewError" class="preview-error">
      <p class="error-title">预览失败</p>
      <p class="error-message">{{ previewError }}</p>
      <p class="error-hint">请尝试点击其他代码块进行预览</p>
    </div>
    <div v-else class="preview-content">
      <!-- HTML 预览 -->
      <iframe
        v-if="artifact.type === 'html'"
        ref="htmlIframeRef"
        :srcdoc="artifact.content"
        sandbox="allow-scripts allow-same-origin"
        class="preview-iframe"
        @load="handleIframeLoad"
      ></iframe>

      <!-- SVG 预览 -->
      <iframe
        v-else-if="artifact.type === 'svg'"
        ref="svgIframeRef"
        :srcdoc="artifact.content"
        sandbox="allow-scripts allow-same-origin"
        class="preview-iframe"
        @load="handleIframeLoad"
      ></iframe>

      <!-- Markdown 预览 -->
      <div
        v-else-if="artifact.type === 'markdown'"
        class="preview-markdown"
        v-html="renderedMarkdown"
      ></div>

      <!-- 其他类型：显示原始内容 -->
      <pre v-else class="preview-code"><code>{{ artifact.content }}</code></pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
import type { Artifact } from '../types'

const props = defineProps<{
  artifact: Artifact | null
}>()

const previewError = ref<string | null>(null)
const htmlIframeRef = ref<HTMLIFrameElement | null>(null)
const svgIframeRef = ref<HTMLIFrameElement | null>(null)

// 创建 markdown-it 实例（仅用于预览，不添加预览按钮）
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
})

/**
 * 渲染 Markdown 内容
 */
const renderedMarkdown = computed(() => {
  if (props.artifact?.type === 'markdown') {
    try {
      previewError.value = null
      return md.render(props.artifact.content)
    } catch (error) {
      previewError.value = 'Markdown 渲染失败'
      return ''
    }
  }
  return ''
})

/**
 * 处理 iframe 加载
 */
function handleIframeLoad(event: Event) {
  const iframe = event.target as HTMLIFrameElement
  // 检查 iframe 内容是否加载成功
  try {
    // 尝试访问 iframe 内容，如果失败说明有错误
    if (iframe.contentDocument) {
      // 内容加载成功
      previewError.value = null
    }
  } catch (error) {
    // 跨域或其他错误
    previewError.value = '预览内容加载失败，可能是内容格式错误'
  }
}

/**
 * 监听 artifact 变化，重置错误状态并验证内容
 */
watch(
  () => props.artifact,
  async (newArtifact) => {
    previewError.value = null
    
    if (!newArtifact) {
      return
    }

    // 验证内容
    if (!newArtifact.content || newArtifact.content.trim().length === 0) {
      previewError.value = '预览内容为空'
      return
    }

    // 对于 HTML 和 SVG，等待 iframe 加载后检查
    if (newArtifact.type === 'html' || newArtifact.type === 'svg') {
      await nextTick()
      // 设置超时检查，如果 2 秒后 iframe 还没加载，可能有问题
      setTimeout(() => {
        const iframe = newArtifact.type === 'html' ? htmlIframeRef.value : svgIframeRef.value
        if (iframe && !iframe.contentDocument) {
          previewError.value = '预览内容加载超时，请检查内容格式'
        }
      }, 2000)
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.preview-panel {
  height: 100%;
  overflow: auto;
  background-color: white;
  border-left: 1px solid #e5e7eb;
}

.preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6b7280;
  text-align: center;
  padding: 2rem;
}

.preview-error {
  @apply flex flex-col items-center justify-center h-full p-8 text-center;
  color: theme('colors.error.800');
  background-color: theme('colors.error.100');
}

.error-title {
  @apply text-xl font-semibold mb-2;
  color: theme('colors.error.800');
}

.error-message {
  @apply text-sm mb-2;
  color: theme('colors.error.600');
}

.error-hint {
  @apply text-xs text-gray-500 mt-4;
}

.preview-content {
  height: 100%;
  overflow: auto;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.preview-markdown {
  padding: 1.5rem;
  line-height: 1.6;
}

.preview-markdown :deep(h1),
.preview-markdown :deep(h2),
.preview-markdown :deep(h3) {
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  font-weight: 600;
}

.preview-markdown :deep(p) {
  margin-bottom: 1rem;
}

.preview-markdown :deep(code) {
  background-color: #f3f4f6;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
}

.preview-markdown :deep(pre) {
  background-color: #1f2937;
  color: #f9fafb;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin-bottom: 1rem;
}

.preview-markdown :deep(pre code) {
  background-color: transparent;
  color: inherit;
  padding: 0;
}

.preview-code {
  padding: 1.5rem;
  background-color: #1f2937;
  color: #f9fafb;
  overflow-x: auto;
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.5;
}

.preview-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 2rem;
  text-align: center;
  color: theme('colors.error.800');
}

.error-title {
  @apply text-xl font-semibold mb-2;
  color: theme('colors.error.800');
}

.error-message {
  @apply text-sm mb-4;
  color: theme('colors.error.600');
}

.error-hint {
  @apply text-sm text-gray-500 italic;
}
</style>

