<template>
  <div class="preview-panel" data-testid="preview-panel">
    <div class="preview-header">
      <span class="preview-title">预览</span>
      <button class="preview-close" @click="handleClose" title="关闭预览">×</button>
    </div>
    <div v-if="!artifact" class="preview-empty">
      <p>点击代码块上的"预览"按钮查看内容</p>
    </div>
    <div v-else-if="previewError" class="preview-error">
      <p class="error-title">预览失败</p>
      <p class="error-message">{{ previewError }}</p>
      <p class="error-hint">请尝试点击其他代码块进行预览</p>
    </div>
    <div v-else class="preview-content">
      <!-- HTML 预览 - 使用严格的 sandbox 安全策略 -->
      <iframe
        v-if="artifact.type === 'html'"
        ref="htmlIframeRef"
        :srcdoc="sanitizedHtmlContent"
        sandbox="allow-scripts"
        class="preview-iframe"
        @load="handleIframeLoad"
        @error="handleIframeError"
      ></iframe>

      <!-- SVG 预览 - 直接渲染 SVG 内容 -->
      <div
        v-else-if="artifact.type === 'svg'"
        class="preview-svg"
        v-html="sanitizedSvgContent"
      ></div>

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

const emit = defineEmits<{
  close: []
}>()

function handleClose() {
  emit('close')
}

const previewError = ref<string | null>(null)
const htmlIframeRef = ref<HTMLIFrameElement | null>(null)

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
 * 清理和处理 HTML 内容
 * 确保 HTML 在安全的 sandbox 环境中执行
 */
const sanitizedHtmlContent = computed(() => {
  if (props.artifact?.type === 'html') {
    try {
      previewError.value = null
      let content = props.artifact.content.trim()
      
      // 如果不是完整的 HTML 文档，包装成完整文档
      if (!content.toLowerCase().includes('<!doctype') && !content.toLowerCase().includes('<html')) {
        content = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body { margin: 16px; font-family: system-ui, -apple-system, sans-serif; }
  </style>
</head>
<body>
${content}
</body>
</html>`
      }
      
      return content
    } catch (error) {
      previewError.value = 'HTML 内容处理失败'
      return ''
    }
  }
  return ''
})

/**
 * 清理和处理 SVG 内容
 * 确保 SVG 安全渲染
 */
const sanitizedSvgContent = computed(() => {
  if (props.artifact?.type === 'svg') {
    try {
      previewError.value = null
      let content = props.artifact.content.trim()
      
      // 确保内容是有效的 SVG
      if (!content.toLowerCase().includes('<svg')) {
        previewError.value = '无效的 SVG 内容'
        return ''
      }
      
      // 移除潜在的危险脚本标签
      content = content.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      
      return content
    } catch (error) {
      previewError.value = 'SVG 内容处理失败'
      return ''
    }
  }
  return ''
})

/**
 * 处理 iframe 加载
 */
function handleIframeLoad() {
  // 检查 iframe 内容是否加载成功
  try {
    // 注意：由于使用了 sandbox（没有 allow-same-origin），
    // 我们无法访问 iframe.contentDocument，这是正常的安全限制
    // 如果 load 事件触发，说明内容已成功加载
    previewError.value = null
    console.log('HTML 预览加载成功')
  } catch (error) {
    console.error('HTML 预览加载出错:', error)
    previewError.value = '预览内容加载失败，可能是内容格式错误'
  }
}

/**
 * 处理 iframe 错误
 */
function handleIframeError(event: Event) {
  console.error('HTML 预览错误:', event)
  previewError.value = 'HTML 预览加载失败'
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

    // 对于 HTML，等待 iframe 加载后检查
    if (newArtifact.type === 'html') {
      await nextTick()
      // 设置超时检查，如果 2 秒后 iframe 还没加载，可能有问题
      setTimeout(() => {
        if (htmlIframeRef.value && previewError.value === null) {
          // 如果 2 秒后没有错误，说明加载正常
          console.log('HTML 预览超时检查：正常')
        }
      }, 2000)
    }
    
    // 对于 SVG，直接渲染，无需额外检查
    if (newArtifact.type === 'svg') {
      await nextTick()
      // SVG 内容已通过 v-html 渲染，检查是否有错误
      if (!previewError.value) {
        console.log('SVG 预览渲染成功')
      }
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.preview-panel {
  @apply flex flex-col h-full bg-white overflow-hidden;
  border-left: 1px solid #e5e7eb;
}

.preview-header {
  @apply flex items-center justify-between px-4 py-3 border-b border-gray-200 flex-shrink-0;
}

.preview-title {
  @apply text-sm font-semibold text-gray-900;
}

.preview-close {
  @apply w-6 h-6 flex items-center justify-center text-gray-400 hover:text-gray-600 cursor-pointer transition-colors duration-200;
  font-size: 20px;
  line-height: 1;
}

.preview-close:hover {
  @apply bg-gray-100 rounded;
}

.preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6b7280;
  text-align: center;
  padding: 2rem 2rem 2rem 2rem; /* 确保右侧内边距充足 */
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
  @apply flex-1;
  box-sizing: border-box;
  max-width: 100%;
  width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
  overflow-y: auto;
  overflow-x: hidden; /* 防止水平溢出 */
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  box-sizing: border-box;
  max-width: 100%;
  overflow: hidden;
}

.preview-svg {
  @apply p-6 flex items-center justify-center;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  overflow: auto;
}

.preview-svg :deep(svg) {
  max-width: 100%;
  max-height: 100%;
  height: auto;
  display: block;
  margin: 0 auto;
}

.preview-markdown {
  padding: 1.5rem 2rem 1.5rem 1.5rem; /* 右侧增加到 2rem，防止文字贴边 */
  line-height: 1.6;
  max-width: 100%;
  width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
  box-sizing: border-box;
  overflow-x: hidden; /* 防止水平溢出 */
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
  max-width: 100%;
  box-sizing: border-box;
}

.preview-markdown :deep(pre code) {
  background-color: transparent;
  color: inherit;
  padding: 0;
}

.preview-code {
  padding: 1.5rem 2rem 1.5rem 1.5rem; /* 右侧增加到 2rem */
  background-color: #1f2937;
  color: #f9fafb;
  overflow-x: auto;
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.5;
  max-width: 100%;
  box-sizing: border-box;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: pre-wrap; /* 允许代码换行 */
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

