/**
 * @vitest-environment jsdom
 * MarkdownEditorView 组件测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import MarkdownEditorView from '../../src/views/MarkdownEditorView.vue'
import MarkdownEditor from '../../src/components/editor/MarkdownEditor.vue'

// Mock window.confirm
const mockConfirm = vi.spyOn(window, 'confirm')

// Mock vue-router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

describe('MarkdownEditorView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该正确渲染工具栏和编辑器', () => {
    const wrapper = mount(MarkdownEditorView, {
      global: {
        stubs: {
          MarkdownEditor: true,
        },
      },
    })

    // 验证工具栏
    expect(wrapper.find('.toolbar').exists()).toBe(true)
    expect(wrapper.find('.toolbar-title').exists()).toBe(true)
    expect(wrapper.find('.toolbar-title').text()).toContain('Markdown 编辑器')

    // 验证清空按钮存在
    expect(wrapper.find('.toolbar-btn').exists()).toBe(true)
  })

  it('应该包含MarkdownEditor组件', () => {
    const wrapper = mount(MarkdownEditorView)

    const markdownEditor = wrapper.findComponent(MarkdownEditor)
    expect(markdownEditor.exists()).toBe(true)
  })

  it('应该将编辑器内容传递给MarkdownEditor', () => {
    const wrapper = mount(MarkdownEditorView)

    const markdownEditor = wrapper.findComponent(MarkdownEditor)
    const content = markdownEditor.props('modelValue')

    // 验证内容存在并且包含默认欢迎信息
    expect(content).toBeTruthy()
    expect(content).toContain('# 欢迎使用 Markdown 编辑器')
  })

  it('清空按钮应该弹出确认对话框', async () => {
    mockConfirm.mockReturnValue(false) // 用户取消

    const wrapper = mount(MarkdownEditorView, {
      global: {
        stubs: {
          MarkdownEditor: true,
        },
      },
    })

    // 找到清空按钮（通过title属性）
    const clearButtons = wrapper.findAll('.toolbar-btn')
    const clearButton = clearButtons.find(btn => btn.text().includes('清空'))

    expect(clearButton).toBeDefined()
    if (clearButton) {
      await clearButton.trigger('click')

      // 验证confirm被调用
      expect(mockConfirm).toHaveBeenCalledWith('确定要清空所有内容吗？此操作不可撤销。')
    }
  })

  it('应该有默认的欢迎内容', () => {
    const wrapper = mount(MarkdownEditorView)

    const markdownEditor = wrapper.findComponent(MarkdownEditor)
    const content = markdownEditor.props('modelValue')

    // 验证默认内容
    expect(content).toContain('# 欢迎使用 Markdown 编辑器')
    expect(content).toContain('## 功能特性')
    expect(content).toContain('实时预览')
    expect(content).toContain('数学公式')
  })

  it('返回按钮应该导航到/common-tools', async () => {
    const wrapper = mount(MarkdownEditorView, {
      global: {
        stubs: {
          MarkdownEditor: true,
        },
      },
    })

    // 找到返回按钮
    const backButtons = wrapper.findAll('.toolbar-btn')
    const backButton = backButtons.find(btn => btn.text().includes('返回'))

    expect(backButton).toBeDefined()
    if (backButton) {
      await backButton.trigger('click')

      // 验证路由跳转
      expect(mockPush).toHaveBeenCalledWith('/common-tools')
    }
  })

  it('清空按钮确认后应该清空内容', async () => {
    mockConfirm.mockReturnValue(true) // 用户确认

    const wrapper = mount(MarkdownEditorView, {
      global: {
        stubs: {
          MarkdownEditor: true,
        },
      },
    })

    // 等待编辑器初始化
    await nextTick()

    // 找到清空按钮
    const clearButtons = wrapper.findAll('.toolbar-btn')
    const clearButton = clearButtons.find(btn => btn.text().includes('清空'))

    expect(clearButton).toBeDefined()
    if (clearButton) {
      await clearButton.trigger('click')

      // 验证confirm被调用
      expect(mockConfirm).toHaveBeenCalledWith('确定要清空所有内容吗？此操作不可撤销。')

      // 等待清空操作完成
      await nextTick()

      // 验证内容被清空
      const markdownEditor = wrapper.findComponent(MarkdownEditor)
      const content = markdownEditor.props('modelValue')
      expect(content).toBe('')
    }
  })

  it('清空按钮取消后不应清空内容', async () => {
    mockConfirm.mockReturnValue(false) // 用户取消

    const wrapper = mount(MarkdownEditorView, {
      global: {
        stubs: {
          MarkdownEditor: true,
        },
      },
    })

    // 等待编辑器初始化
    await nextTick()

    // 获取初始内容
    const markdownEditor = wrapper.findComponent(MarkdownEditor)
    const initialContent = markdownEditor.props('modelValue')

    // 找到清空按钮
    const clearButtons = wrapper.findAll('.toolbar-btn')
    const clearButton = clearButtons.find(btn => btn.text().includes('清空'))

    if (clearButton) {
      await clearButton.trigger('click')

      // 等待操作完成
      await nextTick()

      // 验证内容没有变化
      const newContent = markdownEditor.props('modelValue')
      expect(newContent).toBe(initialContent)
      expect(newContent).toContain('# 欢迎使用 Markdown 编辑器')
    }
  })

  it('MarkdownEditor应该响应v-model更新', async () => {
    const wrapper = mount(MarkdownEditorView)

    const markdownEditor = wrapper.findComponent(MarkdownEditor)

    // 触发input事件模拟用户输入
    const newContent = '# 新内容\n\n这是测试内容'
    await markdownEditor.vm.$emit('update:modelValue', newContent)

    // 等待更新
    await nextTick()

    // 验证编辑器接收到新内容
    expect(markdownEditor.props('modelValue')).toBe(newContent)
  })

  it('工具栏应该有正确的类名和样式', () => {
    const wrapper = mount(MarkdownEditorView, {
      global: {
        stubs: {
          MarkdownEditor: true,
        },
      },
    })

    // 验证工具栏容器
    const toolbar = wrapper.find('.toolbar')
    expect(toolbar.exists()).toBe(true)

    // 验证工具栏标题
    const toolbarTitle = wrapper.find('.toolbar-title')
    expect(toolbarTitle.exists()).toBe(true)

    // 验证工具栏操作区
    const toolbarActions = wrapper.find('.toolbar-actions')
    expect(toolbarActions.exists()).toBe(true)
  })

  it('应该有响应式布局类名', () => {
    const wrapper = mount(MarkdownEditorView, {
      global: {
        stubs: {
          MarkdownEditor: true,
        },
      },
    })

    // 验证主容器类名
    expect(wrapper.find('.markdown-editor-view').exists()).toBe(true)
  })

  describe('边界情况', () => {
    it('应该处理空的编辑器内容', async () => {
      const wrapper = mount(MarkdownEditorView)

      const markdownEditor = wrapper.findComponent(MarkdownEditor)

      // 设置空内容
      await markdownEditor.vm.$emit('update:modelValue', '')

      await nextTick()

      expect(markdownEditor.props('modelValue')).toBe('')
    })

    it('应该处理包含特殊字符的内容', async () => {
      const wrapper = mount(MarkdownEditorView)

      const markdownEditor = wrapper.findComponent(MarkdownEditor)

      // 设置包含特殊字符的内容
      const specialContent = '# 测试\n\n<script>alert("test")</script>\n\n$$\\int_{0}^{\\infty} x^2 dx$$'
      await markdownEditor.vm.$emit('update:modelValue', specialContent)

      await nextTick()

      expect(markdownEditor.props('modelValue')).toContain('<script>')
      expect(markdownEditor.props('modelValue')).toContain('$$')
    })

    it('应该处理长文本内容', async () => {
      const wrapper = mount(MarkdownEditorView)

      const markdownEditor = wrapper.findComponent(MarkdownEditor)

      // 设置长文本
      const longContent = '# 长文本\n\n' + 'a'.repeat(10000)
      await markdownEditor.vm.$emit('update:modelValue', longContent)

      await nextTick()

      // 验证内容长度（# 长文本\n\n = 7字符 + 10000字符）
      expect(markdownEditor.props('modelValue').length).toBeGreaterThanOrEqual(10000)
    })
  })

  describe('组件方法', () => {
    it('handleBack方法应该调用router.push', () => {
      const wrapper = mount(MarkdownEditorView, {
        global: {
          stubs: {
            MarkdownEditor: true,
          },
        },
      })

      const vm = wrapper.vm as any
      vm.handleBack()

      expect(mockPush).toHaveBeenCalledWith('/common-tools')
    })

    it('handleClear方法在用户确认时应该清空内容', async () => {
      mockConfirm.mockReturnValue(true)

      const wrapper = mount(MarkdownEditorView, {
        global: {
          stubs: {
            MarkdownEditor: true,
          },
        },
      })

      const vm = wrapper.vm as any
      await vm.handleClear()

      await nextTick()

      const markdownEditor = wrapper.findComponent(MarkdownEditor)
      expect(markdownEditor.props('modelValue')).toBe('')
    })

    it('handleClear方法在用户取消时不应清空内容', async () => {
      mockConfirm.mockReturnValue(false)

      const wrapper = mount(MarkdownEditorView, {
        global: {
          stubs: {
            MarkdownEditor: true,
          },
        },
      })

      const vm = wrapper.vm as any
      const markdownEditor = wrapper.findComponent(MarkdownEditor)
      const initialContent = markdownEditor.props('modelValue')

      await vm.handleClear()

      await nextTick()

      expect(markdownEditor.props('modelValue')).toBe(initialContent)
    })
  })
})
