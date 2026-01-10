<template>
  <div class="preview-panel" data-testid="preview-panel">
    <div class="preview-header">
      <span class="preview-title">预览</span>
      <div class="preview-actions">
        <button 
          v-if="artifact?.type === 'markdown'"
          class="preview-action-btn" 
          @click="handleDownloadMarkdown" 
          title="下载 Markdown"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          <span>下载 Markdown</span>
        </button>
        <button 
          v-if="artifact?.type === 'markdown'"
          class="preview-action-btn" 
          @click="handleDownloadWord" 
          title="下载 Word"
          :disabled="isDownloadingWord"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          <span>{{ isDownloadingWord ? '转换中...' : '下载 Word' }}</span>
        </button>
        <button 
          v-if="artifact?.type === 'markdown'"
          class="preview-action-btn" 
          @click="handleDownloadPDF" 
          title="下载 PDF"
          :disabled="isDownloadingPDF"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          <span>{{ isDownloadingPDF ? '生成中...' : '下载 PDF' }}</span>
        </button>
        <!-- SVG 操作按钮 -->
        <button 
          v-if="artifact?.type === 'svg'"
          class="preview-action-btn" 
          @click="handleFullscreen" 
          title="全屏预览"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
          </svg>
          <span>全屏</span>
        </button>
        <button 
          v-if="artifact?.type === 'svg'"
          class="preview-action-btn" 
          @click="handleDownloadSVG" 
          title="下载 SVG"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          <span>下载 SVG</span>
        </button>
        <!-- HTML 操作按钮 -->
        <button 
          v-if="artifact?.type === 'html'"
          class="preview-action-btn" 
          @click="handleFullscreen" 
          title="全屏预览"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
          </svg>
          <span>全屏</span>
        </button>
        <button 
          v-if="artifact?.type === 'html'"
          class="preview-action-btn" 
          @click="handleDownloadHTML" 
          title="下载 HTML"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          <span>下载 HTML</span>
        </button>
        <button class="preview-close" @click="handleClose" title="关闭预览">×</button>
      </div>
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
      >
        <div ref="markdownContentRef" class="markdown-content" v-html="renderedMarkdown"></div>
      </div>

      <!-- 其他类型：显示原始内容 -->
      <pre v-else class="preview-code"><code>{{ artifact.content }}</code></pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
// @ts-ignore - @traptitech/markdown-it-katex 没有类型定义
import markdownItKatex from '@traptitech/markdown-it-katex'
// @ts-ignore - html2pdf.js 没有类型定义
import html2pdf from 'html2pdf.js'
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

/**
 * 下载 Markdown 文件
 */
function handleDownloadMarkdown() {
  if (!props.artifact || props.artifact.type !== 'markdown') {
    return
  }

  const content = props.artifact.content
  
  // 生成文件名：优先使用时间戳（因为当前没有会话标题信息）
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')
  const filename = `markdown_${timestamp[0]}_${timestamp[1].split('-').slice(0, 3).join('')}.md`
  
  // 创建 Blob 对象（UTF-8 编码，支持中文）
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  
  // 创建下载链接并触发下载
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  
  // 清理
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 下载 Word 文件（调用后端 API 转换）
 */
async function handleDownloadWord() {
  if (!props.artifact || props.artifact.type !== 'markdown') {
    return
  }

  if (isDownloadingWord.value) {
    return // 防止重复点击
  }

  try {
    isDownloadingWord.value = true
    previewError.value = null

    const content = props.artifact.content
    
    // 生成文件名（不含扩展名）
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')
    const filename = `markdown_${timestamp[0]}_${timestamp[1].split('-').slice(0, 3).join('')}`

    // 调用后端 API
    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
    if (!token) {
      throw new Error('未登录，请先登录')
    }

    const response = await fetch('/api/v1/convert/markdown-to-word', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        content: content,
        filename: filename
      })
    })

    if (!response.ok) {
      if (response.status === 503) {
        throw new Error('文档转换服务暂时不可用，请稍后重试')
      } else if (response.status === 401) {
        throw new Error('登录已过期，请重新登录')
      } else {
        const errorData = await response.json().catch(() => ({ detail: '未知错误' }))
        throw new Error(errorData.detail || '转换失败')
      }
    }

    // 获取文件名（从响应头）
    const contentDisposition = response.headers.get('Content-Disposition')
    let downloadFilename = `${filename}.docx`
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
      if (filenameMatch) {
        downloadFilename = filenameMatch[1]
      }
    }

    // 下载文件
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = downloadFilename
    document.body.appendChild(link)
    link.click()
    
    // 清理
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

  } catch (error) {
    console.error('下载 Word 失败:', error)
    previewError.value = error instanceof Error ? error.message : '下载失败，请稍后重试'
  } finally {
    isDownloadingWord.value = false
  }
}

/**
 * 下载 PDF 文件（纯前端方案，使用 html2pdf.js）
 */
async function handleDownloadPDF() {
  if (!props.artifact || props.artifact.type !== 'markdown') {
    return
  }

  if (isDownloadingPDF.value) {
    return // 防止重复点击
  }

  try {
    isDownloadingPDF.value = true
    previewError.value = null

    // 等待 DOM 完全渲染，包括 KaTeX 公式
    await nextTick()
    // 等待 KaTeX 完成渲染
    await new Promise(resolve => setTimeout(resolve, 500))

    // 获取预览面板中已渲染的 Markdown 内容 DOM
    const element = markdownContentRef.value
    if (!element) {
      throw new Error('预览内容未找到')
    }

    // 生成文件名
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')
    const filename = `markdown_${timestamp[0]}_${timestamp[1].split('-').slice(0, 3).join('')}.pdf`

    // 配置 html2pdf 选项
    const opt = {
      margin: [10, 10, 10, 10], // [top, left, bottom, right] in mm
      filename: filename,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { 
        scale: 3, // 提高到3倍，改善渲染质量
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff',
        scrollY: -window.scrollY, // 重要：抵消滚动偏移
        scrollX: -window.scrollX,
        windowWidth: element.scrollWidth,
        windowHeight: element.scrollHeight,
        onclone: (clonedDoc: Document) => {
          // 在克隆的文档上调整样式，确保与预览一致
          const clonedElement = clonedDoc.querySelector('.markdown-content') as HTMLElement
          if (clonedElement) {
            // 确保所有元素使用与预览相同的渲染方式
            clonedElement.style.transform = 'translateZ(0)' // 强制硬件加速
            clonedElement.style.webkitFontSmoothing = 'antialiased'
          }
        }
      },
      jsPDF: { 
        unit: 'mm', 
        format: 'a4', 
        orientation: 'portrait',
        compress: true
      },
      pagebreak: { 
        mode: ['avoid-all', 'css', 'legacy']
      }
    }

    // 生成并下载 PDF
    await html2pdf().set(opt).from(element).save()

  } catch (error) {
    console.error('下载 PDF 失败:', error)
    previewError.value = error instanceof Error ? error.message : '生成 PDF 失败，请稍后重试'
  } finally {
    isDownloadingPDF.value = false
  }
}

/**
 * 下载 SVG 文件
 */
function handleDownloadSVG() {
  if (!props.artifact || props.artifact.type !== 'svg') {
    return
  }

  const content = props.artifact.content
  
  // 生成文件名
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')
  const filename = `svg_${timestamp[0]}_${timestamp[1].split('-').slice(0, 3).join('')}.svg`
  
  // 创建 Blob 对象（UTF-8 编码）
  const blob = new Blob([content], { type: 'image/svg+xml;charset=utf-8' })
  
  // 创建下载链接并触发下载
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  
  // 清理
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 下载 HTML 文件
 */
function handleDownloadHTML() {
  if (!props.artifact || props.artifact.type !== 'html') {
    return
  }

  const content = props.artifact.content
  
  // 生成文件名
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')
  const filename = `html_${timestamp[0]}_${timestamp[1].split('-').slice(0, 3).join('')}.html`
  
  // 创建 Blob 对象（UTF-8 编码）
  const blob = new Blob([content], { type: 'text/html;charset=utf-8' })
  
  // 创建下载链接并触发下载
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  
  // 清理
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 全屏预览（HTML 和 SVG 通用）
 */
function handleFullscreen() {
  // 获取预览内容区域
  const previewContent = document.querySelector('.preview-content') as HTMLElement
  if (!previewContent) {
    return
  }

  // 检查浏览器是否支持全屏 API
  if (!document.fullscreenEnabled) {
    previewError.value = '您的浏览器不支持全屏功能'
    return
  }

  // 进入全屏
  previewContent.requestFullscreen().catch((error) => {
    console.error('全屏失败:', error)
    previewError.value = '全屏失败，请稍后重试'
  })
}

const previewError = ref<string | null>(null)
const htmlIframeRef = ref<HTMLIFrameElement | null>(null)
const markdownContentRef = ref<HTMLDivElement | null>(null)
const isDownloadingWord = ref<boolean>(false)
const isDownloadingPDF = ref<boolean>(false)

// 创建 markdown-it 实例（仅用于预览，不添加预览按钮）
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
})

// 添加 KaTeX 插件支持数学公式渲染
// @traptitech/markdown-it-katex 支持 $...$ (行内公式) 和 $$...$$ (块级公式)
md.use(markdownItKatex, {
  throwOnError: false,
  errorColor: '#cc0000',
  strict: false, // 宽松模式，避免公式解析错误
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
      console.error('Markdown 渲染错误:', error)
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

.preview-actions {
  @apply flex items-center gap-2;
}

.preview-action-btn {
  @apply flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded cursor-pointer transition-colors duration-200;
}

.preview-action-btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}

.preview-action-btn:disabled:hover {
  @apply text-gray-700 bg-transparent;
}

.preview-action-btn svg {
  @apply w-4 h-4;
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
  @apply p-6 overflow-y-auto;
}

/* Markdown 内容样式 - 不使用 prose，避免与 KaTeX 冲突 */
.markdown-content {
  font-size: 16px;
  line-height: 1.6;
  color: #374151;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  font-weight: 600;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  line-height: 1.25;
  color: #111827;
}

.markdown-content :deep(h1) {
  font-size: 2em;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 0.6em; /* 增加间距，让分隔线往下 */
}

.markdown-content :deep(h2) {
  font-size: 1.5em;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 0.6em; /* 增加间距，让分隔线往下 */
}

.markdown-content :deep(h3) {
  font-size: 1.25em;
}

.markdown-content :deep(h4) {
  font-size: 1.1em;
}

.markdown-content :deep(p) {
  margin-bottom: 1em;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin-bottom: 1em;
  padding-left: 2em;
}

.markdown-content :deep(li) {
  margin-bottom: 0.25em;
}

.markdown-content :deep(code) {
  background-color: #f3f4f6;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-size: 0.875em;
  font-family: 'Courier New', Courier, monospace;
}

.markdown-content :deep(pre) {
  background-color: #1f2937;
  color: #f9fafb;
  padding: 1em;
  border-radius: 6px;
  overflow-x: auto;
  margin-bottom: 1em;
}

.markdown-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid #e5e7eb;
  padding-left: 1em;
  margin: 1em 0;
  color: #6b7280;
}

.markdown-content :deep(a) {
  color: #3b82f6;
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 1em;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 0.5em;
  text-align: left;
}

.markdown-content :deep(th) {
  background-color: #f3f4f6;
  font-weight: 600;
}

/* KaTeX 公式样式 - 确保完整显示 */
.markdown-content :deep(.katex-display) {
  margin: 1.5em 0;
  overflow-x: auto;
  overflow-y: hidden;
  line-height: 2.2 !important; /* 足够的行高，确保分数线、根号显示完整 */
  padding: 0.5em 0; /* 上下内边距，防止裁剪 */
  display: block !important;
}

.markdown-content :deep(.katex) {
  line-height: 1.8 !important; /* 行内公式行高 */
}

/* PDF 生成优化：确保完整显示 */
.markdown-content :deep(.katex-display) {
  page-break-inside: avoid;
  overflow: visible !important;
}

.markdown-content :deep(.katex) {
  page-break-inside: avoid;
  overflow: visible !important;
}

/* 微调：让分数线、根号等往下移动 */
.markdown-content :deep(.katex .frac-line) {
  transform: translateY(4px); /* 分数线往下4px */
}

.markdown-content :deep(.katex .sqrt-line) {
  transform: translateY(4px); /* 根号线往下4px */
}

.markdown-content :deep(.katex .sqrt .hide-tail) {
  transform: translateY(4px); /* 根号顶部往下4px */
}

.markdown-content :deep(.katex-display > .katex) {
  transform: translateY(4px); /* 整个公式块往下4px */
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  page-break-after: avoid; /* 避免标题后立即分页 */
}

.markdown-content :deep(p) {
  orphans: 3; /* 段落至少3行才分页 */
  widows: 3; /* 段落末尾至少3行 */
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

