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
export function renderMarkdown(content: string, artifacts: Artifact[]): string {
  // 先渲染 Markdown
  let html = md.render(content)

  // 为可预览的代码块添加预览按钮
  // 可预览的类型：html, svg, markdown
  const previewableTypes = ['html', 'svg', 'markdown']

  artifacts.forEach((artifact) => {
    if (previewableTypes.includes(artifact.type)) {
      // 查找对应的代码块并添加预览按钮
      // 这里使用简单的字符串替换，实际应该使用 DOM 操作更安全
      const codeBlockRegex = new RegExp(
        `<pre><code class="language-${artifact.language}">([\\s\\S]*?)</code></pre>`,
        'g'
      )

      html = html.replace(codeBlockRegex, (match, codeContent) => {
        // 检查内容是否匹配（简单匹配，实际应该更精确）
        const escapedContent = escapeHtml(artifact.content)
        if (codeContent.includes(escapedContent) || match.includes(artifact.content)) {
          const artifactJson = escapeHtml(JSON.stringify(artifact))
          return `<div class="code-block-wrapper">
            <pre><code class="language-${artifact.language}">${codeContent}</code></pre>
            <button 
              class="preview-button" 
              data-artifact-type="${artifact.type}"
              data-artifact-content="${artifactJson}"
            >
              预览
            </button>
          </div>`
        }
        return match
      })
    }
  })

  return html
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

