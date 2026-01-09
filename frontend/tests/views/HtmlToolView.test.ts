/**
 * @vitest-environment jsdom
 * HtmlToolView 组件测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import HtmlToolView from '../../src/views/HtmlToolView.vue'
import type { CommonToolDetail } from '../../src/types'

// Mock API 服务
const mockGetCommonToolDetail = vi.fn()

vi.mock('../../src/services/apiClient', () => ({
  ApiService: {
    getCommonToolDetail: mockGetCommonToolDetail,
  },
}))

describe('HtmlToolView', () => {
  let router: ReturnType<typeof createRouter>

  beforeEach(() => {
    vi.clearAllMocks()

    // 创建测试用的 router
    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/common-tools',
          name: 'common-tools-home',
          component: { template: '<div>Common Tools</div>' },
        },
        {
          path: '/common-tools/html/:toolId',
          name: 'html-tool',
          component: HtmlToolView,
          props: true,
        },
      ],
    })
  })

  it('应该显示加载状态', () => {
    // Mock pending promise
    mockGetCommonToolDetail.mockReturnValue(new Promise(() => {}))

    const wrapper = mount(HtmlToolView, {
      props: {
        toolId: 'test-html-tool',
      },
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.text()).toContain('加载工具中')
  })

  it('应该成功加载HTML工具并显示iframe', async () => {
    const mockToolDetail: CommonToolDetail = {
      id: 'test-html-tool',
      name: '测试HTML工具',
      description: 'HTML工具描述',
      category_id: 'data-tools',
      category_name: '数据工具',
      type: 'html',
      icon: 'code',
      order: 1,
      html_url: '/static/common_tools/html/test-html-tool/index.html',
      created_at: '2024-01-01T00:00:00Z',
    }

    mockGetCommonToolDetail.mockResolvedValue(mockToolDetail)

    const wrapper = mount(HtmlToolView, {
      props: {
        toolId: 'test-html-tool',
      },
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    // 验证工具名称
    expect(wrapper.text()).toContain('测试HTML工具')

    // 验证返回按钮
    expect(wrapper.find('.back-btn').exists()).toBe(true)
    expect(wrapper.find('.back-btn').text()).toContain('返回')

    // 验证全屏按钮
    expect(wrapper.find('.action-btn').exists()).toBe(true)
    expect(wrapper.find('.action-btn').text()).toContain('全屏')

    // 验证iframe存在
    const iframe = wrapper.find('iframe')
    expect(iframe.exists()).toBe(true)
    expect(iframe.attributes('src')).toBe('/static/common_tools/html/test-html-tool/index.html')
    expect(iframe.attributes('sandbox')).toBe('allow-scripts allow-forms allow-popups allow-same-origin')
  })

  it('应该显示错误状态（工具不存在）', async () => {
    mockGetCommonToolDetail.mockRejectedValue(new Error('工具不存在或已下线'))

    const wrapper = mount(HtmlToolView, {
      props: {
        toolId: 'non-existent',
      },
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('加载失败')
    expect(wrapper.text()).toContain('工具不存在或已下线')
    expect(wrapper.find('.retry-button').exists()).toBe(true)
    expect(wrapper.find('.back-button').exists()).toBe(true)
  })

  it('应该显示错误（工具类型不是HTML）', async () => {
    const mockToolDetail: CommonToolDetail = {
      id: 'markdown-editor',
      name: 'Markdown编辑器',
      description: '描述',
      category_id: 'doc-tools',
      category_name: '文档工具',
      type: 'built-in',
      icon: 'document-text',
      order: 1,
      created_at: '2024-01-01T00:00:00Z',
    }

    mockGetCommonToolDetail.mockResolvedValue(mockToolDetail)

    const wrapper = mount(HtmlToolView, {
      props: {
        toolId: 'markdown-editor',
      },
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('加载失败')
    expect(wrapper.text()).toContain('此工具不是HTML工具')
  })

  it('应该显示错误（HTML地址无效）', async () => {
    const mockToolDetail: CommonToolDetail = {
      id: 'test-html-tool',
      name: '测试HTML工具',
      description: '描述',
      category_id: 'data-tools',
      category_name: '数据工具',
      type: 'html',
      icon: 'code',
      order: 1,
      html_url: undefined, // 没有HTML地址
      created_at: '2024-01-01T00:00:00Z',
    }

    mockGetCommonToolDetail.mockResolvedValue(mockToolDetail)

    const wrapper = mount(HtmlToolView, {
      props: {
        toolId: 'test-html-tool',
      },
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('加载失败')
    expect(wrapper.text()).toContain('工具HTML地址无效')
  })

  it('点击返回按钮应该导航到工具卡片页', async () => {
    const mockToolDetail: CommonToolDetail = {
      id: 'test-html-tool',
      name: '测试HTML工具',
      description: '描述',
      category_id: 'data-tools',
      category_name: '数据工具',
      type: 'html',
      icon: 'code',
      order: 1,
      html_url: '/static/test.html',
      created_at: '2024-01-01T00:00:00Z',
    }

    mockGetCommonToolDetail.mockResolvedValue(mockToolDetail)

    const wrapper = mount(HtmlToolView, {
      props: {
        toolId: 'test-html-tool',
      },
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    const backButton = wrapper.find('.back-btn')
    await backButton.trigger('click')

    // 验证路由跳转
    expect(router.currentRoute.value.path).toBe('/common-tools')
  })

  it('点击重试按钮应该重新加载工具', async () => {
    mockGetCommonToolDetail.mockRejectedValue(new Error('网络错误'))

    const wrapper = mount(HtmlToolView, {
      props: {
        toolId: 'test-html-tool',
      },
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    // 第一次加载失败
    expect(wrapper.text()).toContain('加载失败')

    // 模拟重试成功
    const mockToolDetail: CommonToolDetail = {
      id: 'test-html-tool',
      name: '测试HTML工具',
      description: '描述',
      category_id: 'data-tools',
      category_name: '数据工具',
      type: 'html',
      icon: 'code',
      order: 1,
      html_url: '/static/test.html',
      created_at: '2024-01-01T00:00:00Z',
    }
    mockGetCommonToolDetail.mockResolvedValue(mockToolDetail)

    const retryButton = wrapper.find('.retry-button')
    await retryButton.trigger('click')
    await flushPromises()

    // 验证重新加载成功
    expect(wrapper.text()).toContain('测试HTML工具')
    expect(wrapper.find('iframe').exists()).toBe(true)
  })

  it('iframe应该有安全的sandbox属性', async () => {
    const mockToolDetail: CommonToolDetail = {
      id: 'test-html-tool',
      name: '测试HTML工具',
      description: '描述',
      category_id: 'data-tools',
      category_name: '数据工具',
      type: 'html',
      icon: 'code',
      order: 1,
      html_url: '/static/test.html',
      created_at: '2024-01-01T00:00:00Z',
    }

    mockGetCommonToolDetail.mockResolvedValue(mockToolDetail)

    const wrapper = mount(HtmlToolView, {
      props: {
        toolId: 'test-html-tool',
      },
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    const iframe = wrapper.find('iframe')
    const sandbox = iframe.attributes('sandbox')

    // 验证沙箱属性
    expect(sandbox).toContain('allow-scripts')
    expect(sandbox).toContain('allow-forms')
    expect(sandbox).toContain('allow-popups')
    expect(sandbox).toContain('allow-same-origin')
  })
})
