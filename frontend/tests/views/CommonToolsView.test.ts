/**
 * @vitest-environment jsdom
 * CommonToolsView 组件测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import CommonToolsView from '../../src/views/CommonToolsView.vue'
import type { CommonToolCategoryResponse } from '../../src/types'

// Mock API 服务
const mockGetCommonToolCategories = vi.fn()

vi.mock('../../src/services/apiClient', () => ({
  ApiService: {
    getCommonToolCategories: mockGetCommonToolCategories,
  },
}))

describe('CommonToolsView', () => {
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
          component: CommonToolsView,
        },
        {
          path: '/common-tools/:toolId',
          name: 'common-tool-detail',
          component: { template: '<div>Tool Detail</div>' },
        },
        {
          path: '/common-tools/html/:toolId',
          name: 'common-tool-html',
          component: { template: '<div>HTML Tool</div>' },
        },
      ],
    })
  })

  it('应该显示加载状态', () => {
    // Mock pending promise
    mockGetCommonToolCategories.mockReturnValue(new Promise(() => {}))

    const wrapper = mount(CommonToolsView, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.text()).toContain('加载中')
  })

  it('应该成功加载并显示工具分类列表', async () => {
    const mockResponse: CommonToolCategoryResponse = {
      categories: [
        {
          id: 'doc-tools',
          name: '文档工具',
          icon: 'document-text',
          order: 1,
          tools: [
            {
              id: 'markdown-editor',
              name: 'Markdown编辑器',
              description: '在线编辑Markdown文档，实时预览，支持导出Word/PDF',
              type: 'built-in',
              icon: 'document-text',
              order: 1,
            },
          ],
        },
        {
          id: 'data-tools',
          name: '数据工具',
          icon: 'chart-bar',
          order: 2,
          tools: [
            {
              id: 'html-tool',
              name: 'HTML工具',
              description: 'HTML工具描述',
              type: 'html',
              icon: 'code',
              order: 1,
            },
          ],
        },
      ],
    }

    mockGetCommonToolCategories.mockResolvedValue(mockResponse)

    const wrapper = mount(CommonToolsView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    // 验证页面标题
    expect(wrapper.text()).toContain('常用工具')

    // 验证分类标题
    expect(wrapper.text()).toContain('文档工具')
    expect(wrapper.text()).toContain('数据工具')

    // 验证工具卡片
    expect(wrapper.text()).toContain('Markdown编辑器')
    expect(wrapper.text()).toContain('在线编辑Markdown文档')
    expect(wrapper.text()).toContain('HTML工具')

    // 验证工具类型标签
    expect(wrapper.text()).toContain('内置')
    expect(wrapper.text()).toContain('HTML')
  })

  it('应该显示空状态', async () => {
    const mockResponse: CommonToolCategoryResponse = {
      categories: [],
    }

    mockGetCommonToolCategories.mockResolvedValue(mockResponse)

    const wrapper = mount(CommonToolsView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('暂无工具')
    expect(wrapper.text()).toContain('目前还没有可用的工具')
  })

  it('应该显示错误状态并支持重试', async () => {
    mockGetCommonToolCategories.mockRejectedValue(new Error('网络错误'))

    const wrapper = mount(CommonToolsView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('加载失败')
    expect(wrapper.text()).toContain('网络错误')
    expect(wrapper.text()).toContain('重试')

    // 模拟重试成功
    const mockResponse: CommonToolCategoryResponse = {
      categories: [
        {
          id: 'doc-tools',
          name: '文档工具',
          icon: 'document-text',
          order: 1,
          tools: [
            {
              id: 'markdown-editor',
              name: 'Markdown编辑器',
              description: '描述',
              type: 'built-in',
              order: 1,
            },
          ],
        },
      ],
    }
    mockGetCommonToolCategories.mockResolvedValue(mockResponse)

    // 点击重试按钮
    const retryButton = wrapper.find('.retry-button')
    await retryButton.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('文档工具')
    expect(wrapper.text()).toContain('Markdown编辑器')
  })

  it('点击内置工具卡片应该导航到工具详情页', async () => {
    const mockResponse: CommonToolCategoryResponse = {
      categories: [
        {
          id: 'doc-tools',
          name: '文档工具',
          icon: 'document-text',
          order: 1,
          tools: [
            {
              id: 'markdown-editor',
              name: 'Markdown编辑器',
              description: '描述',
              type: 'built-in',
              order: 1,
            },
          ],
        },
      ],
    }

    mockGetCommonToolCategories.mockResolvedValue(mockResponse)

    const wrapper = mount(CommonToolsView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    // 查找并点击工具卡片
    const toolCard = wrapper.find('.tool-card')
    await toolCard.trigger('click')

    // 验证路由跳转
    expect(router.currentRoute.value.path).toBe('/common-tools/markdown-editor')
  })

  it('点击HTML工具卡片应该导航到HTML工具运行器', async () => {
    const mockResponse: CommonToolCategoryResponse = {
      categories: [
        {
          id: 'data-tools',
          name: '数据工具',
          icon: 'chart-bar',
          order: 1,
          tools: [
            {
              id: 'html-tool',
              name: 'HTML工具',
              description: '描述',
              type: 'html',
              order: 1,
            },
          ],
        },
      ],
    }

    mockGetCommonToolCategories.mockResolvedValue(mockResponse)

    const wrapper = mount(CommonToolsView, {
      global: {
        plugins: [router],
      },
    })

    await flushPromises()

    // 查找并点击HTML工具卡片
    const toolCard = wrapper.find('.tool-card')
    await toolCard.trigger('click')

    // 验证路由跳转到HTML工具运行器
    expect(router.currentRoute.value.path).toBe('/common-tools/html/html-tool')
  })
})
