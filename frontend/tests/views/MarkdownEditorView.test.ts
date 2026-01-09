/**
 * @vitest-environment jsdom
 * MarkdownEditorView 组件测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import MarkdownEditorView from '../../src/views/MarkdownEditorView.vue'
import PreviewPanel from '../../src/components/PreviewPanel.vue'

// Mock window.confirm
const mockConfirm = vi.spyOn(window, 'confirm')

describe('MarkdownEditorView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该正确渲染编辑器和预览面板', () => {
    const wrapper = mount(MarkdownEditorView, {
      global: {
        stubs: {
          PreviewPanel: true, // Stub PreviewPanel to simplify testing
        },
      },
    })

    // 验证编辑器头部
    expect(wrapper.find('.editor-header').exists()).toBe(true)
    expect(wrapper.find('.editor-title').text()).toBe('Markdown 编辑器')

    // 验证清空按钮存在
    expect(wrapper.find('.editor-action-btn').exists()).toBe(true)
    expect(wrapper.find('.editor-action-btn').text()).toContain('清空')

    // 验证编辑器内容区域
    expect(wrapper.find('.editor-content').exists()).toBe(true)

    // 验证预览容器
    expect(wrapper.find('.preview-container').exists()).toBe(true)
  })

  it('应该包含PreviewPanel组件', () => {
    const wrapper = mount(MarkdownEditorView)

    // 验证PreviewPanel组件存在
    const previewPanel = wrapper.findComponent(PreviewPanel)
    expect(previewPanel.exists()).toBe(true)
  })

  it('应该将编辑器内容传递给PreviewPanel', async () => {
    const wrapper = mount(MarkdownEditorView)

    const previewPanel = wrapper.findComponent(PreviewPanel)
    const artifact = previewPanel.props('artifact')

    // 验证artifact存在并且是Markdown类型
    expect(artifact).toBeTruthy()
    expect(artifact.type).toBe('markdown')
    expect(artifact.language).toBe('markdown')
    expect(artifact.content).toContain('# 欢迎使用 Markdown 编辑器')
  })

  it('清空按钮应该弹出确认对话框', async () => {
    mockConfirm.mockReturnValue(false) // 用户取消

    const wrapper = mount(MarkdownEditorView, {
      global: {
        stubs: {
          PreviewPanel: true,
        },
      },
    })

    const clearButton = wrapper.find('.editor-action-btn')
    await clearButton.trigger('click')

    // 验证confirm被调用
    expect(mockConfirm).toHaveBeenCalledWith('确定要清空所有内容吗？此操作不可撤销。')
  })

  it('应该有默认的欢迎内容', () => {
    const wrapper = mount(MarkdownEditorView)

    const previewPanel = wrapper.findComponent(PreviewPanel)
    const artifact = previewPanel.props('artifact')

    // 验证默认内容
    expect(artifact.content).toContain('# 欢迎使用 Markdown 编辑器')
    expect(artifact.content).toContain('## 功能特性')
    expect(artifact.content).toContain('实时预览')
    expect(artifact.content).toContain('数学公式')
  })

  it('应该有响应式布局类名', () => {
    const wrapper = mount(MarkdownEditorView, {
      global: {
        stubs: {
          PreviewPanel: true,
        },
      },
    })

    // 验证响应式容器类名
    expect(wrapper.find('.editor-container').exists()).toBe(true)
    expect(wrapper.find('.editor-panel').exists()).toBe(true)
    expect(wrapper.find('.preview-container').exists()).toBe(true)
  })
})
