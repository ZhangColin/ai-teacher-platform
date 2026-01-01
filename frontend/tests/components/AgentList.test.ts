/**
 * @vitest-environment jsdom
 * AgentList 组件测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import AgentList from '../../src/components/AgentList.vue'
import { useAgentStore } from '../../src/stores/agentStore'
import type { AgentListItem } from '../../src/types'

// Mock API 服务，避免实际网络请求
vi.mock('../../src/services/apiClient', () => ({
  ApiService: {
    getAgents: vi.fn(),
  },
}))

describe('AgentList', () => {
  let router: ReturnType<typeof createRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    
    // 创建测试用的 router
    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/agent/:agentId',
          name: 'agent-detail',
          component: { template: '<div>Agent Detail</div>' },
        },
      ],
    })
  })

  it('应该显示加载状态', () => {
    const store = useAgentStore()
    store.loading = true

    const wrapper = mount(AgentList, {
      global: {
        plugins: [pinia, router],
      },
    })

    expect(wrapper.text()).toContain('加载中')
  })

  it('应该显示 Agent 列表', async () => {
    const store = useAgentStore()
    store.agents = [
      {
        agent_id: 'prompt_wizard',
        name: 'AI 提示词向导',
        description: '通过六步引导法，帮助您打造专家级提示词',
      },
      {
        agent_id: 'code_assistant',
        name: '代码助手',
        description: '帮助您编写和优化代码',
      },
    ]

    const wrapper = mount(AgentList, {
      global: {
        plugins: [pinia, router],
      },
    })

    expect(wrapper.text()).toContain('AI 提示词向导')
    expect(wrapper.text()).toContain('代码助手')
    expect(wrapper.text()).toContain('通过六步引导法')
  })

  it('应该显示空列表提示', () => {
    const store = useAgentStore()
    store.agents = []
    store.loading = false

    const wrapper = mount(AgentList, {
      global: {
        plugins: [pinia, router],
      },
    })

    expect(wrapper.text()).toContain('暂无 Agent')
  })

  it('应该显示错误信息', () => {
    const store = useAgentStore()
    store.error = '获取 Agent 列表失败'
    store.loading = false

    const wrapper = mount(AgentList, {
      global: {
        plugins: [pinia, router],
      },
    })

    expect(wrapper.text()).toContain('获取 Agent 列表失败')
  })

  it('应该点击 Agent 项时触发导航', async () => {
    const pushSpy = vi.spyOn(router, 'push')

    const store = useAgentStore()
    store.agents = [
      {
        agent_id: 'prompt_wizard',
        name: 'AI 提示词向导',
        description: '通过六步引导法，帮助您打造专家级提示词',
      },
    ]

    const wrapper = mount(AgentList, {
      global: {
        plugins: [pinia, router],
      },
    })

    const agentItem = wrapper.find('[data-testid="agent-item-prompt_wizard"]')
    await agentItem.trigger('click')

    expect(pushSpy).toHaveBeenCalledWith({
      name: 'agent-detail',
      params: { agentId: 'prompt_wizard' },
    })
  })

  it('应该在挂载时调用 fetchAgents', () => {
    const store = useAgentStore()
    const fetchAgentsSpy = vi.spyOn(store, 'fetchAgents')

    mount(AgentList, {
      global: {
        plugins: [pinia, router],
      },
    })

    expect(fetchAgentsSpy).toHaveBeenCalled()
  })
})
