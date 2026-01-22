/** Session Store - 管理当前会话状态 */
import { defineStore } from 'pinia'
import { ref, computed, nextTick } from 'vue'
import { ApiService } from '../services/apiClient'
import type { Message, Artifact } from '../types'

export const useSessionStore = defineStore('session', () => {
  // 状态
  const sessionId = ref<string | null>(null)
  const toolId = ref<string | null>(null)
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const titleGenerated = ref(false) // 标题是否已生成
  const currentPreviewArtifact = ref<Artifact | null>(null)

  // 计算属性
  const hasSession = computed(() => sessionId.value !== null)
  const messageCount = computed(() => messages.value.length)
  const showPreview = computed(() => currentPreviewArtifact.value !== null)

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
    titleGenerated.value = false // 重置标题生成标志

    // 添加用户消息（标记为 pending）
    messages.value.push({
      role: 'user',
      content,
      pending: true,
    })
    const userMsgIndex = messages.value.length - 1

    // 创建 AI 回复消息占位符（显示加载状态）
    messages.value.push({
      role: 'assistant',
      content: '',
      artifacts: [],
      pending: true, // 标记为加载中
    })
    const aiMsgIndex = messages.value.length - 1

    try {
      // 使用流式接口
      await ApiService.chatStream(
        toolId.value,
        {
          message: content,
          session_id: sessionId.value || null,
          history: messages.value.slice(0, -2).map(msg => ({
            role: msg.role,
            content: msg.content,
          })),
        },
        (data) => {
          // 处理流式数据块
          if (data.type === 'session_id') {
            // 更新会话ID
            if (data.session_id) {
              sessionId.value = data.session_id
            }
          } else if (data.type === 'content') {
            // 通过索引直接修改数组中的消息
            if (messages.value[aiMsgIndex]) {
              messages.value[aiMsgIndex].content += data.content || ''
              // 触发响应式更新 - 重新赋值该消息对象
              const msg = messages.value[aiMsgIndex]
              messages.value[aiMsgIndex] = { ...msg }
            }
            // 收到第一个内容块时，关闭 loading 状态
            if (loading.value) {
              loading.value = false
            }
          } else if (data.type === 'done') {
            // 流式完成
            if (messages.value[aiMsgIndex]) {
              messages.value[aiMsgIndex].artifacts = data.artifacts || []
              messages.value[aiMsgIndex].pending = false
            }
            if (messages.value[userMsgIndex]) {
              messages.value[userMsgIndex].pending = false
            }
          } else if (data.type === 'title_generated') {
            // 标题生成完成
            titleGenerated.value = true
          } else if (data.type === 'error') {
            // 错误处理
            throw new Error(data.error || '发送消息失败')
          }
        }
      )
    } catch (err) {
      console.error('发送消息失败:', err)
      // 移除 AI 占位符消息
      if (aiMsgIndex < messages.value.length) {
        messages.value.splice(aiMsgIndex, 1)
      }
      // 更新用户消息状态（标记为错误）
      if (userMsgIndex < messages.value.length && messages.value[userMsgIndex]) {
        messages.value[userMsgIndex].pending = false
        messages.value[userMsgIndex].error = err instanceof Error ? err.message : '发送消息失败'
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
        timestamp: msg.timestamp || (msg as any).created_at,
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
    titleGenerated,
    // 计算属性
    hasSession,
    messageCount,
    showPreview,
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

