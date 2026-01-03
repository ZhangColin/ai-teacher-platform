/** Session Store - 管理当前会话状态 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ApiService } from '../services/apiClient'
import type { Message, Artifact } from '../types'

export const useSessionStore = defineStore('session', () => {
  // 状态
  const sessionId = ref<string | null>(null)
  const toolId = ref<string | null>(null)
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const currentPreviewArtifact = ref<Artifact | null>(null)

  // 计算属性
  const hasSession = computed(() => sessionId.value !== null)
  const messageCount = computed(() => messages.value.length)

  /**
   * 初始化工具（不创建会话，仅设置工具ID）
   */
  function initTool(toolIdParam: string) {
    toolId.value = toolIdParam
    // 不创建会话，等待用户发送第一条消息
    sessionId.value = null
    messages.value = []
    error.value = null
  }

  /**
   * 发送消息（支持延迟创建会话）
   */
  async function sendMessage(content: string) {
    if (!toolId.value) {
      const errorMsg = '工具未初始化，无法发送消息'
      console.error(errorMsg, { toolId: toolId.value })
      error.value = errorMsg
      throw new Error(errorMsg)
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
      console.log('发送消息:', { toolId: toolId.value, sessionId: sessionId.value, content })
      
      // 使用新接口，session_id 可选
      const response = await ApiService.chat(toolId.value, {
        message: content,
        session_id: sessionId.value || null, // 如果有会话ID则继续会话，没有则创建新会话
        history: messages.value.slice(0, -1).map(msg => ({
          role: msg.role,
          content: msg.content,
        })), // 不包含刚添加的用户消息
      })

      console.log('收到回复:', response)

      // 更新会话ID（首次调用会返回新创建的session_id）
      if (response.session_id) {
        sessionId.value = response.session_id
        console.log('会话ID已更新:', response.session_id)
      }

      // 更新用户消息状态（移除 pending）
      const lastMessage = messages.value[messages.value.length - 1]
      if (lastMessage && lastMessage.role === 'user') {
        lastMessage.pending = false
      }

      // 添加 AI 回复
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.reply,
        artifacts: response.artifacts || [],
      }
      messages.value.push(assistantMessage)
    } catch (err) {
      console.error('发送消息失败:', err)
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
   * 恢复会话（从API加载会话详情）
   */
  async function restoreSession(sessionIdParam: string) {
    if (!sessionIdParam) {
      return
    }

    loading.value = true
    error.value = null

    try {
      const response = await ApiService.getSessionDetail(sessionIdParam)
      
      sessionId.value = response.session_id
      toolId.value = response.tool_id
      
      // 转换消息格式
      messages.value = response.messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || msg.created_at,
        artifacts: msg.artifacts || [],
      }))
    } catch (err) {
      error.value = err instanceof Error ? err.message : '恢复会话失败'
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
    toolId.value = null
    messages.value = []
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
    toolId,
    messages,
    loading,
    error,
    currentPreviewArtifact,
    // 计算属性
    hasSession,
    messageCount,
    // 方法
    initTool,
    sendMessage,
    restoreSession,
    setPreviewArtifact,
    retryMessage,
    clearSession,
    reset,
  }
})

