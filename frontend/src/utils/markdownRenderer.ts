/** Markdown 渲染工具 */
import MarkdownIt from 'markdown-it'
import type { Artifact } from '../types'

// 创建 markdown-it 实例，配置安全选项
const md = new MarkdownIt({
  html: false, // 禁用 HTML 标签，防止 XSS
  linkify: true, // 自动识别链接
  typographer: true, // 启用排版功能
})

/**
 * 渲染 Markdown 内容，并为可预览的代码块添加预览按钮
 */
export function renderMarkdown(content: string, artifacts: Artifact[] = []): string {
  // 【最后防线】清理可能的重复代码块标记
  // 模式1：```结束后紧接着又开始```（中间可能有空白）
  // 例如：```\n```html\n 或 ```\n\n```python\n
  let cleanedContent = content.replace(/```\s*\n\s*```(\w+)?\s*\n/g, '\n')
  
  // 模式2：代码块内部出现的```标记（非常规情况）
  // 这种情况比较复杂，暂时不处理，因为可能是用户真实需要的内容
  
  // 先渲染 Markdown
  let html = md.render(cleanedContent)

  // 匹配所有代码块的正则表达式
  const codeBlockRegex = /<pre><code(?:\s+class="language-([^"]+)")?>([\s\S]*?)<\/code><\/pre>/gi

  html = html.replace(codeBlockRegex, (_match, language, codeContent) => {
    // 获取语言标识（去除可能的空格）
    let lang = (language || '').trim().toLowerCase()
    
    // 从 codeContent 中提取原始内容（去除 HTML 转义）
    const rawContent = unescapeHtml(codeContent.trim())
    
    // 如果没有语言标识，尝试智能识别
    if (!lang) {
      lang = detectLanguageByContent(rawContent)
    }
    
    // 所有代码块都使用相同的类型标识
    let artifactType = lang || 'text'
    
    // 尝试从 artifacts 中查找匹配的 artifact
    let artifact: Artifact | null = null
    if (artifacts && artifacts.length > 0) {
      artifact = artifacts.find(a => 
        a.language === lang && 
        a.content.trim() === rawContent
      ) || null
    }

    // 如果没有找到匹配的 artifact，从代码块内容创建
    if (!artifact) {
      artifact = {
        type: artifactType,
        content: rawContent,
        language: lang,
        timestamp: new Date().toISOString()
      }
    }

    // 创建 artifact JSON（转义后用于 data 属性）
          const artifactJson = escapeHtml(JSON.stringify(artifact))
    // 代码内容（用于复制）
    const codeContentForCopy = escapeHtml(rawContent)
    
    // 返回带预览和复制按钮的代码块
    return `<div class="code-block-wrapper">
      <div class="code-block-header">
        <span class="code-language">${escapeHtml(lang)}</span>
        <div class="code-block-actions">
          <button
            class="preview-button"
            data-artifact-type="${artifactType}"
            data-artifact-content="${artifactJson}"
            title="预览 ${artifactType.toUpperCase()} 内容"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
              <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
            </svg>
          </button>
          <button
            class="copy-code-button"
            data-code-content="${codeContentForCopy}"
            title="复制代码"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
              <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"/>
              <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"/>
            </svg>
          </button>
        </div>
      </div>
      <pre><code class="language-${lang}">${codeContent}</code></pre>
    </div>`
  })

  return html
}

/**
 * 反转义 HTML（将 HTML 实体转换回原始字符）
 */
function unescapeHtml(text: string): string {
  const map: Record<string, string> = {
    '&amp;': '&',
    '&lt;': '<',
    '&gt;': '>',
    '&quot;': '"',
    '&#039;': "'",
    '&nbsp;': ' ',
  }
  return text.replace(/&(?:amp|lt|gt|quot|#039|nbsp);/g, (m) => map[m] || m)
}

/**
 * 根据内容特征智能识别代码块类型（前端兜底识别）
 * 与后端识别逻辑保持一致
 */
function detectLanguageByContent(content: string): string {
  const contentLower = content.toLowerCase().trim()
  
  // HTML 特征检测
  const htmlTags = ['<html', '<div', '<script', '<style', '<body', '<head', 
                    '<title', '<meta', '<link', '<button', '<input', '<form']
  if (htmlTags.some(tag => contentLower.includes(tag))) {
    return 'html'
  }
  
  // SVG 特征检测
  const svgTags = ['<svg', '<path', '<circle', '<rect', '<line', '<polygon',
                   '<polyline', '<ellipse', '<text', '<g ', '<defs', '<use']
  if (svgTags.some(tag => contentLower.includes(tag))) {
    return 'svg'
  }
  
  // Markdown 特征检测
  // 1. 标题：以 # 开头
  if (/^#+\s+/m.test(content)) {
    return 'markdown'
  }
  
  // 2. 列表：以 - 或 * 开头
  if (/^[\s]*[-*+]\s+/m.test(content)) {
    return 'markdown'
  }
  
  // 3. 粗体/斜体：包含 ** 或 * 或 __ 或 _
  if (/\*\*.*?\*\*|__.*?__|\*.*?\*|_.*?_/.test(content)) {
    return 'markdown'
  }
  
  // 4. 链接：包含 [text](url) 格式
  if (/\[.*?\]\(.*?\)/.test(content)) {
    return 'markdown'
  }
  
  // 5. 代码块：包含 `代码` 或 ```代码块```
  if (/`[^`]+`|```/.test(content)) {
    return 'markdown'
  }
  
  // 默认返回 text
  return 'text'
}

/**
 * 转义正则表达式特殊字符
 * 注意：虽然当前未使用，但保留用于未来功能
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
// @ts-expect-error - Reserved for future functionality
function _escapeRegex(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * 转义 HTML（不使用 DOM，避免 SSR 问题）
 */
function escapeHtml(text: string): string {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  }
  return text.replace(/[&<>"']/g, (m) => map[m] || m)
}

