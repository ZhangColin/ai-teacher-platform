import { describe, it, expect } from 'vitest'
import { renderMarkdown } from '@/utils/markdownRenderer'

describe('markdownRenderer', () => {
  describe('Code block buttons', () => {
    it('should add preview button to code blocks', () => {
      const markdown = '```javascript\nconsole.log("test");\n```'
      const html = renderMarkdown(markdown)

      expect(html).toContain('preview-button')
      expect(html).toContain('data-artifact-content')
    })

    it('should add copy button to code blocks', () => {
      const markdown = '```javascript\nconsole.log("test");\n```'
      const html = renderMarkdown(markdown)

      expect(html).toContain('copy-code-button')
      expect(html).toContain('data-code-content')
    })

    it('should include code block wrapper', () => {
      const markdown = '```javascript\nconsole.log("test");\n```'
      const html = renderMarkdown(markdown)

      expect(html).toContain('code-block-wrapper')
    })

    it('should include language label in code block', () => {
      const markdown = '```javascript\nconsole.log("test");\n```'
      const html = renderMarkdown(markdown)

      expect(html).toContain('javascript')
    })

    it('should handle code blocks without language', () => {
      const markdown = '```\nconsole.log("test");\n```'
      const html = renderMarkdown(markdown)

      expect(html).toContain('code-block-wrapper')
      expect(html).toContain('preview-button')
      expect(html).toContain('copy-code-button')
    })

    it('should escape code content properly for data attributes', () => {
      const markdown = '```javascript\nconst html = "<div>test</div>";\n```'
      const html = renderMarkdown(markdown)

      expect(html).toContain('data-code-content=')
      expect(html).toContain('data-artifact-content=')
      // Should not contain unescaped HTML
      expect(html).not.toContain('data-code-content="<div>')
    })
  })

  describe('Basic markdown rendering', () => {
    it('should render basic markdown', () => {
      const markdown = '# Hello World\n\nThis is a test.'
      const html = renderMarkdown(markdown)

      expect(html).toContain('<h1>Hello World</h1>')
      expect(html).toContain('<p>This is a test.</p>')
    })

    it('should render code blocks', () => {
      const markdown = '```javascript\nconst x = 1;\n```'
      const html = renderMarkdown(markdown)

      expect(html).toContain('<pre>')
      expect(html).toContain('<code')
      expect(html).toContain('language-javascript')
    })

    it('should auto-detect HTML code blocks', () => {
      const markdown = '```\n<div>Hello</div>\n```'
      const html = renderMarkdown(markdown)

      expect(html).toContain('html')
    })

    it('should auto-detect SVG code blocks', () => {
      const markdown = '```\n<svg><circle cx="10" cy="10" r="5"/></svg>\n```'
      const html = renderMarkdown(markdown)

      expect(html).toContain('svg')
    })

    it('should auto-detect Markdown code blocks', () => {
      const markdown = '```\n# Heading\n- List item\n```'
      const html = renderMarkdown(markdown)

      expect(html).toContain('markdown')
    })
  })
})
