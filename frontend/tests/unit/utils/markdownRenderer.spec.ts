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

  describe('Content preservation with LaTeX formulas', () => {
    it('should convert LaTeX delimiters to dollar signs', () => {
      const markdown = 'Formula: \\[ x + y = z \\]'
      const html = renderMarkdown(markdown)

      // After conversion, should contain $$ delimiters
      expect(html).toContain('$$')
    })

    it('should not lose content after LaTeX conversion', () => {
      const markdown = `### Section 3

1. **Answer**: B
   **Analysis**: Substitute points to get: \\[ \\begin{cases} k + b = 3 \\\\-k + b = -1 \\end{cases} \\]

2. **Answer**: C
   **Analysis**: Some analysis here.

3. **Answer**: Test content 3

End of section.`

      const html = renderMarkdown(markdown)

      // Verify section title exists
      expect(html).toContain('Section 3')

      // Verify all content exists
      expect(html).toContain('Answer')
      expect(html).toContain('Analysis')
      expect(html).toContain('Test content 3')
      expect(html).toContain('End of section')

      // Count occurrences
      const answerMatches = html.match(/Answer/g)
      expect(answerMatches).toBeTruthy()
      expect(answerMatches.length).toBeGreaterThanOrEqual(3)
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

  describe('Content preservation with LaTeX formulas', () => {
    it('should not lose content after LaTeX conversion', () => {
      const markdown = `### Section 3

1. **Answer**: B
   **Analysis**: Substitute points to get: \\[ \\begin{cases} k + b = 3 \\\\-k + b = -1 \\end{cases} \\]

2. **Answer**: C
   **Analysis**: Some analysis here.

3. **Answer**: Test content 3

End of section.`

      const html = renderMarkdown(markdown)

      // Verify section title exists
      expect(html).toContain('Section 3')

      // Verify all content exists
      expect(html).toContain('Answer')
      expect(html).toContain('Analysis')
      expect(html).toContain('Test content 3')
      expect(html).toContain('End of section')

      // Count occurrences
      const answerMatches = html.match(/Answer/g)
      expect(answerMatches).toBeTruthy()
      expect(answerMatches.length).toBeGreaterThanOrEqual(3)
    })
  })

  describe('XSS security', () => {
    it('should escape HTML in language labels', () => {
      const markdown = '```<script>alert(1)</script>\nconsole.log("test");\n```'
      const html = renderMarkdown(markdown)

      // Should not contain unescaped script tags
      expect(html).not.toContain('<script>alert(1)</script>')
      // Should contain escaped version (note: & is also escaped to &amp;)
      expect(html).toContain('&amp;lt;script&amp;gt;alert(1)&amp;lt;/script&amp;gt;')
    })

    it('should escape HTML in language labels with known language', () => {
      const markdown = '```javascript<img src=x onerror=alert(1)>\nconsole.log("test");\n```'
      const html = renderMarkdown(markdown)

      // Should not contain unescaped HTML
      expect(html).not.toContain('<img src=x')
      // Should contain escaped version (note: & is also escaped to &amp;)
      expect(html).toContain('&amp;lt;img')
    })

    it('should escape complex XSS payloads in language labels', () => {
      const markdown = '```<svg onload=alert(1)>\nconsole.log("test");\n```'
      const html = renderMarkdown(markdown)

      // Should not contain unescaped SVG onload
      expect(html).not.toContain('<svg onload=')
      // Should contain escaped version (note: & is also escaped to &amp;)
      expect(html).toContain('&amp;lt;svg')
    })
  })
})
