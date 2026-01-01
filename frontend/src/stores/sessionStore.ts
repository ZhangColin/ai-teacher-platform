/** Session Store - 管理当前会话状态 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ApiService } from '../services/apiClient'
import type { Message, UIConfig, Artifact } from '../types'

export const useSessionStore = defineStore('session', () => {
  // 状态
  const sessionId = ref<string | null>(null)
  const agentId = ref<string | null>(null)
  const messages = ref<Message[]>([])
  const uiConfig = ref<UIConfig | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const currentPreviewArtifact = ref<Artifact | null>(null)

  // 计算属性
  const hasSession = computed(() => sessionId.value !== null)
  const messageCount = computed(() => messages.value.length)
  const showPreview = computed(() => uiConfig.value?.show_preview ?? false)

  /**
   * 创建会话
   */
  async function createSession(agentIdParam: string) {
    loading.value = true
    error.value = null
    try {
      const response = await ApiService.createSession(agentIdParam)
      sessionId.value = response.session_id
      agentId.value = agentIdParam
      uiConfig.value = response.ui_config
      
      // 添加欢迎消息
      messages.value = [
        {
          role: 'assistant',
          content: response.welcome_message,
          artifacts: response.artifacts,
        },
      ]
    } catch (err) {
      error.value = err instanceof Error ? err.message : '创建会话失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 发送消息
   */
  async function sendMessage(content: string) {
    if (!sessionId.value) {
      throw new Error('会话未初始化')
    }

    loading.value = true
    error.value = null

    // 添加用户消息（标记为 pending）
    const userMessage: Message = {
      role: 'user',
      content,
      pending: true,
    }
    messages.value.push(userMessage)

    try {
      const response = await ApiService.chat(sessionId.value, {
        message: content,
        history: messages.value.slice(0, -1), // 不包含刚添加的用户消息
      })

      // 更新用户消息状态（移除 pending）
      const lastMessage = messages.value[messages.value.length - 1]
      if (lastMessage && lastMessage.role === 'user') {
        lastMessage.pending = false
      }

      // 添加 AI 回复
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.reply,
        artifacts: response.artifacts,
      }
      messages.value.push(assistantMessage)
    } catch (err) {
      // 更新用户消息状态（标记为错误）
      const lastMessage = messages.value[messages.value.length - 1]
      if (lastMessage && lastMessage.role === 'user') {
        lastMessage.pending = false
        lastMessage.error = err instanceof Error ? err.message : '发送消息失败'
      }
      error.value = err instanceof Error ? err.message : '发送消息失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 设置当前预览的成果物
   */
  function setPreviewArtifact(artifact: Artifact | null) {
    currentPreviewArtifact.value = artifact
  }

  /**
   * 重发消息
   */
  async function retryMessage(messageIndex: number) {
    const message = messages.value[messageIndex]
    if (!message || message.role !== 'user' || !message.error) {
      return
    }

    // 清除错误状态
    message.error = undefined
    message.pending = true

    // 重新发送
    try {
      await sendMessage(message.content)
      // 发送成功后，移除 pending 状态（sendMessage 会处理）
    } catch (err) {
      // 错误已在 sendMessage 中处理
    }
  }

  /**
   * 清空会话
   */
  function clearSession() {
    sessionId.value = null
    agentId.value = null
    messages.value = []
    uiConfig.value = null
    currentPreviewArtifact.value = null
    error.value = null
  }

  /**
   * 重置状态
   */
  function reset() {
    clearSession()
    loading.value = false
  }

  return {
    // 状态
    sessionId,
    agentId,
    messages,
    uiConfig,
    loading,
    error,
    currentPreviewArtifact,
    // 计算属性
    hasSession,
    messageCount,
    showPreview,
    // 方法
    createSession,
    sendMessage,
    setPreviewArtifact,
    retryMessage,
    clearSession,
    reset,
  }
})

