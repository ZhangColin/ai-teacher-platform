/**
 * @vitest-environment jsdom
 * 常用工具模块集成测试 - 端到端流程测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory, type Router } from 'vue-router'
import CommonToolsLayout from '../../src/layouts/CommonToolsLayout.vue'
import CommonToolsView from '../../src/views/CommonToolsView.vue'
import MarkdownEditorView from '../../src/views/MarkdownEditorView.vue'
import HtmlToolView from '../../src/views/HtmlToolView.vue'
import type { CommonToolCategoryResponse, CommonToolDetail } from '../../src/types'

// Mock API 服务
const mockGetCommonToolCategories = vi.fn()
const mockGetCommonToolDetail = vi.fn()

vi.mock('../../src/services/apiClient', () => ({
  ApiService: {
    getCommonToolCategories: mockGetCommonToolCategories,
    getCommonToolDetail: mockGetCommonToolDetail,
  },
}))

describe('常用工具模块 - 端到端集成测试', () => {
  let router: Router

  // 测试数据
  const mockCategoriesResponse: CommonToolCategoryResponse = {
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
            id: 'json-formatter',
            name: 'JSON格式化工具',
            description: '在线格式化和验证JSON数据',
            type: 'html',
            icon: 'code',
            order: 1,
          },
        ],
      },
    ],
  }

  const mockHtmlToolDetail: CommonToolDetail = {
    id: 'json-formatter',
    name: 'JSON格式化工具',
    description: '在线格式化和验证JSON数据',
    category_id: 'data-tools',
    category_name: '数据工具',
    type: 'html',
    icon: 'code',
    order: 1,
    html_url: '/static/common_tools/html/json-formatter/index.html',
    created_at: '2024-01-01T00:00:00Z',
  }

  beforeEach(() => {
    vi.clearAllMocks()

    // 创建完整的路由配置
    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/common-tools',
          component: CommonToolsLayout,
          children: [
            {
              path: '',
              name: 'common-tools-home',
              component: CommonToolsView,
            },
            {
              path: 'markdown-editor',
              name: 'markdown-editor',
              component: MarkdownEditorView,
            },
            {
              path: 'html/:toolId',
              name: 'html-tool',
              component: HtmlToolView,
              props: true,
            },
          ],
        },
      ],
    })

    // 设置初始路由
    router.push('/common-tools')
  })

  describe('用户故事1：浏览工具', () => {
    it('应该能够浏览所有工具分类和工具卡片', async () => {
      mockGetCommonToolCategories.mockResolvedValue(mockCategoriesResponse)

      const wrapper = mount(CommonToolsLayout, {
        global: {
          plugins: [router],
        },
      })

      await router.isReady()
      await flushPromises()

      // 验证页面标题
      expect(wrapper.text()).toContain('常用工具')

      // 验证分类显示
      expect(wrapper.text()).toContain('文档工具')
      expect(wrapper.text()).toContain('数据工具')

      // 验证工具卡片显示
      expect(wrapper.text()).toContain('Markdown编辑器')
      expect(wrapper.text()).toContain('在线编辑Markdown文档')
      expect(wrapper.text()).toContain('JSON格式化工具')

      // 验证工具类型标签
      expect(wrapper.text()).toContain('内置')
      expect(wrapper.text()).toContain('HTML')
    })

    it('应该只显示有工具的分类', async () => {
      const emptyResponse: CommonToolCategoryResponse = {
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
          // 没有data-tools分类（因为后端已过滤空分类）
        ],
      }

      mockGetCommonToolCategories.mockResolvedValue(emptyResponse)

      const wrapper = mount(CommonToolsLayout, {
        global: {
          plugins: [router],
        },
      })

      await router.isReady()
      await flushPromises()

      // 验证只显示有工具的分类
      expect(wrapper.text()).toContain('文档工具')
      expect(wrapper.text()).not.toContain('数据工具')
    })
  })

  describe('用户故事2：使用内置工具（Markdown编辑器）', () => {
    it('应该能够从卡片页导航到Markdown编辑器', async () => {
      mockGetCommonToolCategories.mockResolvedValue(mockCategoriesResponse)

      const wrapper = mount(CommonToolsLayout, {
        global: {
          plugins: [router],
        },
      })

      await router.isReady()
      await flushPromises()

      // 查找Markdown编辑器卡片
      const toolCards = wrapper.findAll('.tool-card')
      const markdownCard = toolCards.find(card => card.text().includes('Markdown编辑器'))
      expect(markdownCard).toBeTruthy()

      // 点击卡片
      await markdownCard!.trigger('click')
      await flushPromises()

      // 验证路由跳转
      expect(router.currentRoute.value.path).toBe('/common-tools/markdown-editor')
    })

    it('Markdown编辑器应该有编辑器和预览面板', async () => {
      await router.push('/common-tools/markdown-editor')
      await router.isReady()

      const wrapper = mount(CommonToolsLayout, {
        global: {
          plugins: [router],
        },
      })

      await flushPromises()

      // 验证编辑器标题
      expect(wrapper.text()).toContain('Markdown 编辑器')

      // 验证编辑器面板
      expect(wrapper.find('.editor-panel').exists()).toBe(true)

      // 验证预览面板
      expect(wrapper.find('.preview-container').exists()).toBe(true)

      // 验证清空按钮
      expect(wrapper.find('.editor-action-btn').exists()).toBe(true)
    })

    it('Markdown编辑器应该有默认内容', async () => {
      await router.push('/common-tools/markdown-editor')
      await router.isReady()

      const wrapper = mount(CommonToolsLayout, {
        global: {
          plugins: [router],
        },
      })

      await flushPromises()

      // 验证默认欢迎内容
      expect(wrapper.text()).toContain('欢迎使用 Markdown 编辑器')
    })
  })

  describe('用户故事3：使用HTML工具', () => {
    it('应该能够从卡片页导航到HTML工具运行器', async () => {
      mockGetCommonToolCategories.mockResolvedValue(mockCategoriesResponse)
      mockGetCommonToolDetail.mockResolvedValue(mockHtmlToolDetail)

      const wrapper = mount(CommonToolsLayout, {
        global: {
          plugins: [router],
        },
      })

      await router.isReady()
      await flushPromises()

      // 查找HTML工具卡片
      const toolCards = wrapper.findAll('.tool-card')
      const htmlCard = toolCards.find(card => card.text().includes('JSON格式化工具'))
      expect(htmlCard).toBeTruthy()

      // 点击卡片
      await htmlCard!.trigger('click')
      await flushPromises()

      // 验证路由跳转
      expect(router.currentRoute.value.path).toBe('/common-tools/html/json-formatter')
    })

    it('HTML工具应该在iframe沙箱中运行', async () => {
      mockGetCommonToolDetail.mockResolvedValue(mockHtmlToolDetail)

      await router.push('/common-tools/html/json-formatter')
      await router.isReady()

      const wrapper = mount(CommonToolsLayout, {
        global: {
          plugins: [router],
        },
      })

      await flushPromises()

      // 验证工具标题
      expect(wrapper.text()).toContain('JSON格式化工具')

      // 验证iframe存在
      const iframe = wrapper.find('iframe')
      expect(iframe.exists()).toBe(true)

      // 验证iframe沙箱属性
      const sandbox = iframe.attributes('sandbox')
      expect(sandbox).toContain('allow-scripts')
      expect(sandbox).toContain('allow-forms')
      expect(sandbox).toContain('allow-popups')
      expect(sandbox).toContain('allow-same-origin')

      // 验证HTML地址
      expect(iframe.attributes('src')).toBe('/static/common_tools/html/json-formatter/index.html')
    })

    it('HTML工具应该有返回和全屏按钮', async () => {
      mockGetCommonToolDetail.mockResolvedValue(mockHtmlToolDetail)

      await router.push('/common-tools/html/json-formatter')
      await router.isReady()

      const wrapper = mount(CommonToolsLayout, {
        global: {
          plugins: [router],
        },
      })

      await flushPromises()

      // 验证返回按钮
      expect(wrapper.find('.back-btn').exists()).toBe(true)

      // 验证全屏按钮
      expect(wrapper.find('.action-btn').exists()).toBe(true)
      expect(wrapper.text()).toContain('全屏')
    })

    it('点击返回按钮应该返回工具卡片页', async () => {
      mockGetCommonToolDetail.mockResolvedValue(mockHtmlToolDetail)

      await router.push('/common-tools/html/json-formatter')
      await router.isReady()

      const wrapper = mount(CommonToolsLayout, {
        global: {
          plugins: [router],
        },
      })

      await flushPromises()

      // 点击返回按钮
      const backButton = wrapper.find('.back-btn')
      await backButton.trigger('click')
      await flushPromises()

      // 验证返回到工具卡片页
      expect(router.currentRoute.value.path).toBe('/common-tools')
    })
  })

  describe('完整用户流程：浏览 → 使用 → 返回', () => {
    it('应该能完成完整的工具使用流程', async () => {
      mockGetCommonToolCategories.mockResolvedValue(mockCategoriesResponse)
      mockGetCommonToolDetail.mockResolvedValue(mockHtmlToolDetail)

      // 1. 进入工具卡片页
      const wrapper = mount(CommonToolsLayout, {
        global: {
          plugins: [router],
        },
      })

      await router.isReady()
      await flushPromises()

      expect(wrapper.text()).toContain('常用工具')
      expect(wrapper.text()).toContain('JSON格式化工具')

      // 2. 点击HTML工具卡片
      const toolCards = wrapper.findAll('.tool-card')
      const htmlCard = toolCards.find(card => card.text().includes('JSON格式化工具'))
      await htmlCard!.trigger('click')
      await flushPromises()

      expect(router.currentRoute.value.path).toBe('/common-tools/html/json-formatter')
      expect(wrapper.text()).toContain('JSON格式化工具')

      // 3. 验证工具运行中
      const iframe = wrapper.find('iframe')
      expect(iframe.exists()).toBe(true)

      // 4. 点击返回按钮
      const backButton = wrapper.find('.back-btn')
      await backButton.trigger('click')
      await flushPromises()

      // 5. 验证返回到工具卡片页
      expect(router.currentRoute.value.path).toBe('/common-tools')
      expect(wrapper.text()).toContain('常用工具')
    })
  })

  describe('错误处理', () => {
    it('应该正确处理API加载失败', async () => {
      mockGetCommonToolCategories.mockRejectedValue(new Error('网络错误'))

      const wrapper = mount(CommonToolsLayout, {
        global: {
          plugins: [router],
        },
      })

      await router.isReady()
      await flushPromises()

      // 验证错误提示
      expect(wrapper.text()).toContain('加载失败')
      expect(wrapper.text()).toContain('网络错误')

      // 验证重试按钮存在
      expect(wrapper.find('.retry-button').exists()).toBe(true)
    })

    it('应该正确处理工具不存在的情况', async () => {
      mockGetCommonToolDetail.mockRejectedValue(new Error('工具不存在或已下线'))

      await router.push('/common-tools/html/non-existent')
      await router.isReady()

      const wrapper = mount(CommonToolsLayout, {
        global: {
          plugins: [router],
        },
      })

      await flushPromises()

      // 验证错误提示
      expect(wrapper.text()).toContain('加载失败')
      expect(wrapper.text()).toContain('工具不存在或已下线')
    })
  })
})
