import { describe, it, expect } from 'vitest'
import { renderMarkdown } from '@/utils/markdownRenderer'

describe('markdownRenderer - 代码运行按钮', () => {
  it('python 代码块显示运行按钮', () => {
    const html = renderMarkdown('```python\nprint("Hello, World!")\n```')
    expect(html).toMatch(/运行.*代码|运行.*python/i)
    expect(html).toContain('data-artifact-content')
    expect(html).toContain('preview-button')
  })

  it('javascript 代码块显示运行按钮', () => {
    const html = renderMarkdown('```javascript\nconsole.log("Hello!");\n```')
    expect(html).toMatch(/运行.*代码|运行.*javascript/i)
    expect(html).toContain('data-artifact-content')
  })

  it('js 代码块显示运行按钮且类型规范化为 javascript', () => {
    const html = renderMarkdown('```js\nconsole.log("Hello!");\n```')
    expect(html).toMatch(/运行.*代码|运行.*js/i)
    // 验证 artifact type 已被规范化为 javascript
    expect(html).toMatch(/data-artifact-type="javascript"/)
  })

  it('html 代码块显示预览按钮（而非运行）', () => {
    const html = renderMarkdown('```html\n<div>Hello</div>\n```')
    expect(html).toMatch(/预览.*HTML|预览.*html/i)
    expect(html).not.toMatch(/运行.*代码/i)
  })

  it('svg 代码块显示预览按钮（而非运行）', () => {
    const html = renderMarkdown('```svg\n<svg></svg>\n```')
    expect(html).toMatch(/预览.*SVG|预览.*svg/i)
    expect(html).not.toMatch(/运行.*代码/i)
  })

  it('markdown 代码块显示预览按钮（而非运行）', () => {
    const html = renderMarkdown('```markdown\n# 标题\n```')
    expect(html).toMatch(/预览.*MARKDOWN|预览.*markdown/i)
    expect(html).not.toMatch(/运行.*代码/i)
  })

  it('可运行语言的按钮使用播放图标（包含圆形路径）', () => {
    const html = renderMarkdown('```python\nprint(1)\n```')
    // 播放图标包含圆形路径 (M10 18a8)
    expect(html).toMatch(/M10\s*18a8/)
  })

  it('不可运行语言的按钮使用眼睛图标（包含眼睛路径）', () => {
    const html = renderMarkdown('```html\n<div></div>\n```')
    // 眼睛图标包含特定的路径
    expect(html).toMatch(/M10\s*12a2/)
  })

  it('未识别语言不显示运行按钮', () => {
    const html = renderMarkdown('```\nunknown content\n```')
    expect(html).not.toMatch(/运行.*代码/i)
  })
})
