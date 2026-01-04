import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PreviewPanel from '../../src/components/PreviewPanel.vue'
import type { Artifact } from '../../src/types'

describe('PreviewPanel', () => {
  describe('preview-4: HTML 预览', () => {
    it('应该使用 iframe sandbox 安全执行 HTML 内容', async () => {
      const htmlArtifact: Artifact = {
        type: 'html',
        content: '<div><h1>Test HTML</h1><script>alert("test")</script></div>',
        language: 'html',
      }

      const wrapper = mount(PreviewPanel, {
        props: {
          artifact: htmlArtifact,
        },
      })

      await wrapper.vm.$nextTick()

      // 检查是否渲染了 iframe
      const iframe = wrapper.find('iframe')
      expect(iframe.exists()).toBe(true)

      // 检查 sandbox 属性是否正确设置（不包含 allow-same-origin，增强安全性）
      expect(iframe.attributes('sandbox')).toBe('allow-scripts')

      // 检查是否有 srcdoc 属性
      expect(iframe.attributes('srcdoc')).toBeTruthy()
    })

    it('应该将不完整的 HTML 片段包装成完整文档', async () => {
      const htmlArtifact: Artifact = {
        type: 'html',
        content: '<div>Simple content</div>',
        language: 'html',
      }

      const wrapper = mount(PreviewPanel, {
        props: {
          artifact: htmlArtifact,
        },
      })

      await wrapper.vm.$nextTick()

      const iframe = wrapper.find('iframe')
      const srcdoc = iframe.attributes('srcdoc')

      // 检查是否包含完整的 HTML 文档结构
      expect(srcdoc).toContain('<!DOCTYPE html>')
      expect(srcdoc).toContain('<html>')
      expect(srcdoc).toContain('<head>')
      expect(srcdoc).toContain('<body>')
      expect(srcdoc).toContain('<div>Simple content</div>')
    })

    it('应该处理 HTML 加载错误', async () => {
      const wrapper = mount(PreviewPanel, {
        props: {
          artifact: {
            type: 'html',
            content: '',
            language: 'html',
          },
        },
      })

      await wrapper.vm.$nextTick()

      // 检查错误提示
      expect(wrapper.find('.preview-error').exists() || wrapper.find('.preview-empty').exists()).toBe(true)
    })
  })

  describe('preview-5: SVG 预览', () => {
    it('应该直接渲染 SVG 内容', async () => {
      const svgArtifact: Artifact = {
        type: 'svg',
        content: '<svg width="100" height="100"><circle cx="50" cy="50" r="40" fill="red" /></svg>',
        language: 'svg',
      }

      const wrapper = mount(PreviewPanel, {
        props: {
          artifact: svgArtifact,
        },
      })

      await wrapper.vm.$nextTick()

      // 检查是否使用 div 渲染 SVG（不是 iframe）
      const svgContainer = wrapper.find('.preview-svg')
      expect(svgContainer.exists()).toBe(true)

      // 检查 SVG 内容是否存在
      expect(svgContainer.html()).toContain('<svg')
      expect(svgContainer.html()).toContain('<circle')
    })

    it('应该移除 SVG 中的危险脚本标签', async () => {
      const svgArtifact: Artifact = {
        type: 'svg',
        content: '<svg><script>alert("xss")</script><circle cx="50" cy="50" r="40" /></svg>',
        language: 'svg',
      }

      const wrapper = mount(PreviewPanel, {
        props: {
          artifact: svgArtifact,
        },
      })

      await wrapper.vm.$nextTick()

      const svgContainer = wrapper.find('.preview-svg')
      
      // 检查脚本标签是否被移除
      expect(svgContainer.html()).not.toContain('<script')
      expect(svgContainer.html()).not.toContain('alert')
      
      // 检查 SVG 元素仍然存在
      expect(svgContainer.html()).toContain('<circle')
    })

    it('应该处理无效的 SVG 内容', async () => {
      const wrapper = mount(PreviewPanel, {
        props: {
          artifact: {
            type: 'svg',
            content: '<div>Not an SVG</div>',
            language: 'svg',
          },
        },
      })

      await wrapper.vm.$nextTick()

      // 检查错误提示
      expect(wrapper.find('.preview-error').exists()).toBe(true)
      expect(wrapper.text()).toContain('无效的 SVG 内容')
    })
  })

  describe('preview-6: 预览关闭功能', () => {
    it('应该在点击关闭按钮时触发 close 事件', async () => {
      const wrapper = mount(PreviewPanel, {
        props: {
          artifact: {
            type: 'markdown',
            content: '# Test',
            language: 'markdown',
          },
        },
      })

      await wrapper.vm.$nextTick()

      // 查找关闭按钮
      const closeButton = wrapper.find('.preview-close')
      expect(closeButton.exists()).toBe(true)

      // 点击关闭按钮
      await closeButton.trigger('click')

      // 检查是否触发了 close 事件
      expect(wrapper.emitted('close')).toBeTruthy()
      expect(wrapper.emitted('close')).toHaveLength(1)
    })

    it('应该显示关闭按钮的正确样式和提示', () => {
      const wrapper = mount(PreviewPanel, {
        props: {
          artifact: {
            type: 'markdown',
            content: '# Test',
            language: 'markdown',
          },
        },
      })

      const closeButton = wrapper.find('.preview-close')
      
      // 检查关闭按钮的标题属性
      expect(closeButton.attributes('title')).toBe('关闭预览')
      
      // 检查关闭按钮的文本内容
      expect(closeButton.text()).toBe('×')
    })
  })

  describe('通用预览功能', () => {
    it('应该在没有 artifact 时显示空状态', () => {
      const wrapper = mount(PreviewPanel, {
        props: {
          artifact: null,
        },
      })

      const emptyState = wrapper.find('.preview-empty')
      expect(emptyState.exists()).toBe(true)
      expect(emptyState.text()).toContain('点击代码块上的"预览"按钮查看内容')
    })

    it('应该正确处理 Markdown 类型', async () => {
      const wrapper = mount(PreviewPanel, {
        props: {
          artifact: {
            type: 'markdown',
            content: '# Heading\n\nParagraph',
            language: 'markdown',
          },
        },
      })

      await wrapper.vm.$nextTick()

      const markdownContainer = wrapper.find('.preview-markdown')
      expect(markdownContainer.exists()).toBe(true)
      expect(markdownContainer.html()).toContain('<h1')
      expect(markdownContainer.html()).toContain('Heading')
    })

    it('应该为其他类型显示原始代码', async () => {
      const wrapper = mount(PreviewPanel, {
        props: {
          artifact: {
            type: 'javascript',
            content: 'console.log("test")',
            language: 'javascript',
          },
        },
      })

      await wrapper.vm.$nextTick()

      const codeContainer = wrapper.find('.preview-code')
      expect(codeContainer.exists()).toBe(true)
      expect(codeContainer.text()).toContain('console.log("test")')
    })
  })
})

