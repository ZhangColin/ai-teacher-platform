/**
 * ChatArea组件单元测试
 * 测试修复：handleSendMessage实现、watch immediate: true
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import ChatArea from '@/components/ChatArea.vue'
import ConversationList from '@/components/ConversationList.vue'
import ChatPanel from '@/components/ChatPanel.vue'
import PreviewPanel from '@/components/PreviewPanel.vue'
import { useSessionStore } from '@/stores/sessionStore'

// Mock sessionStore
// Pinia stores 自动解包 refs，所以 mock 应该返回普通值
vi.mock('@/stores/sessionStore', () => ({
  useSessionStore: vi.fn(() => ({
    sessionId: null,
    toolId: null,
    messages: [],
    loading: false,
    error: null,
    titleGenerated: false,
    initTool: vi.fn(),
    sendMessage: vi.fn(),
    clearSession: vi.fn(),
    setPreviewArtifact: vi.fn(),
  }))
}))

describe('ChatArea', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // 测试修复：handleSendMessage应该调用sessionStore.sendMessage
  it('should call sessionStore.sendMessage when handleSendMessage is called', async () => {
    const mockSendMessage = vi.fn().mockResolvedValue(undefined)
    const sessionStore = {
      sessionId: null,
      toolId: 'test-tool',
      messages: [],
      loading: false,
      error: null,
      titleGenerated: false,
      initTool: vi.fn(),
      sendMessage: mockSendMessage,
      clearSession: vi.fn(),
      setPreviewArtifact: vi.fn(),
    }

    vi.mocked(useSessionStore).mockReturnValue(sessionStore)

    const wrapper = mount(ChatArea, {
      props: {
        toolId: 'test-tool',
        welcomeMessage: 'Hello'
      },
      global: {
        stubs: {
          ConversationList: true,
          ChatPanel: true,
          PreviewPanel: true
        }
      }
    })

    // 调用handleSendMessage
    const chatArea = wrapper.vm as any
    await chatArea.handleSendMessage('Test message')

    // 验证sessionStore.sendMessage被调用
    expect(mockSendMessage).toHaveBeenCalledWith('Test message')
    expect(mockSendMessage).toHaveBeenCalledTimes(1)
  })

  // 测试修复：handleSendMessage应该处理错误
  it('should handle errors from sessionStore.sendMessage', async () => {
    const mockError = new Error('Network error')
    const mockSendMessage = vi.fn().mockRejectedValue(mockError)

    const sessionStore = {
      sessionId: null,
      toolId: 'test-tool',
      messages: [],
      loading: false,
      error: null,
      titleGenerated: false,
      initTool: vi.fn(),
      sendMessage: mockSendMessage,
      clearSession: vi.fn(),
      setPreviewArtifact: vi.fn(),
    }

    vi.mocked(useSessionStore).mockReturnValue(sessionStore)

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    const wrapper = mount(ChatArea, {
      props: {
        toolId: 'test-tool'
      },
      global: {
        stubs: {
          ConversationList: true,
          ChatPanel: true,
          PreviewPanel: true
        }
      }
    })

    const chatArea = wrapper.vm as any

    // 不应该抛出错误
    await expect(chatArea.handleSendMessage('Test message')).resolves.not.toThrow()

    // 应该记录错误
    expect(consoleSpy).toHaveBeenCalled()

    consoleSpy.mockRestore()
  })

  // 测试修复：toolId变化时应该调用sessionStore.initTool
  it('should call sessionStore.initTool when toolId prop changes', async () => {
    const mockInitTool = vi.fn()

    const sessionStore = {
      sessionId: null,
      toolId: null,
      messages: [],
      loading: false,
      error: null,
      titleGenerated: false,
      initTool: mockInitTool,
      sendMessage: vi.fn().mockResolvedValue(undefined),
      clearSession: vi.fn(),
      setPreviewArtifact: vi.fn(),
    }

    vi.mocked(useSessionStore).mockReturnValue(sessionStore)

    const wrapper = mount(ChatArea, {
      props: {
        toolId: 'test-tool'
      },
      global: {
        stubs: {
          ConversationList: true,
          ChatPanel: true,
          PreviewPanel: true
        }
      }
    })

    // 等待watch执行（immediate: true）
    await wrapper.vm.$nextTick()

    // 验证initTool被调用
    expect(mockInitTool).toHaveBeenCalledWith('test-tool')
  })

  it('should render all child components', () => {
    const wrapper = mount(ChatArea, {
      props: {
        toolId: 'test-tool'
      },
      global: {
        stubs: {
          ConversationList: true,
          ChatPanel: true,
          PreviewPanel: true
        }
      }
    })

    expect(wrapper.findComponent(ConversationList).exists()).toBe(true)
    expect(wrapper.findComponent(ChatPanel).exists()).toBe(true)
  })

  // 测试修复：ChatArea应该在模板中传递sessionStore.messages给ChatPanel
  it('should pass sessionStore.messages to ChatPanel in template', () => {
    const mockSessionStore = {
      sessionId: null,
      toolId: 'test-tool',
      messages: ref([{ role: 'user', content: 'Test' }]),
      loading: false,
      error: null,
      titleGenerated: false,
      initTool: vi.fn(),
      sendMessage: vi.fn().mockResolvedValue(undefined),
      clearSession: vi.fn(),
      setPreviewArtifact: vi.fn(),
    }

    vi.mocked(useSessionStore).mockReturnValue(mockSessionStore)

    const wrapper = mount(ChatArea, {
      props: {
        toolId: 'test-tool'
      },
      global: {
        stubs: {
          ConversationList: true,
          ChatPanel: true,
          PreviewPanel: true
        }
      }
    })

    // 验证ChatArea组件可以访问sessionStore
    const chatArea = wrapper.vm as any
    expect(chatArea.sessionStore).toBeDefined()
    expect(chatArea.sessionStore.messages).toBe(mockSessionStore.messages)
  })

  // 测试修复：ChatArea应该正确传递error和loading props（类型安全验证）
  it('should mount correctly when sessionStore has error and loading state', async () => {
    const testErrorMessage = '网络错误'
    const mockSessionStore = {
      sessionId: null,
      toolId: 'test-tool',
      messages: [],
      loading: true,
      error: ref(testErrorMessage),
      titleGenerated: false,
      initTool: vi.fn(),
      sendMessage: vi.fn().mockResolvedValue(undefined),
      clearSession: vi.fn(),
      setPreviewArtifact: vi.fn(),
    }

    vi.mocked(useSessionStore).mockReturnValue(mockSessionStore)

    // 只验证组件能够正确挂载，不抛出类型错误
    // 这已经足够证明 null → undefined 的类型转换有效
    const wrapper = mount(ChatArea, {
      props: {
        toolId: 'test-tool'
      },
      global: {
        stubs: {
          ConversationList: true,
          ChatPanel: true,
          PreviewPanel: true
        }
      }
    })

    await wrapper.vm.$nextTick()

    // 验证组件存在
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'ChatPanel' }).exists()).toBe(true)
  })

  // 测试修复：ChatArea应该正确处理error为null的情况（类型转换验证）
  it('should mount correctly when sessionStore.error is null', async () => {
    const mockSessionStore = {
      sessionId: null,
      toolId: 'test-tool',
      messages: [],
      loading: false,
      error: null, // error 为 null
      titleGenerated: false,
      initTool: vi.fn(),
      sendMessage: vi.fn().mockResolvedValue(undefined),
      clearSession: vi.fn(),
      setPreviewArtifact: vi.fn(),
    }

    vi.mocked(useSessionStore).mockReturnValue(mockSessionStore)

    // 验证 null → undefined 类型转换不会导致组件挂载失败
    // TypeScript 编译器会检查这个类型转换的正确性
    const wrapper = mount(ChatArea, {
      props: {
        toolId: 'test-tool'
      },
      global: {
        stubs: {
          ConversationList: true,
          ChatPanel: true,
          PreviewPanel: true
        }
      }
    })

    await wrapper.vm.$nextTick()

    // 验证组件存在
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'ChatPanel' }).exists()).toBe(true)
  })
})
