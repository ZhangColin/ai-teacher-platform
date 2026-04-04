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
  const titleGeneratedSessionId = ref<string | null>(null) // 标题生成完成的会话ID
  const currentModel = ref<string | null>(null) // 当前选择的模型（格式：provider:model_name）

  // 计算属性
  const hasSession = computed(() => sessionId.value !== null)
  const messageCount = computed(() => messages.value.length)
  const showPreview = computed(() => currentPreviewArtifact.value !== null)

  /**
   * 初始化工具（不创建会话，仅设置工具ID）
   */
  function initTool(toolIdParam: string) {

    // 验证参数：拒绝空字符串、null、undefined
    if (!toolIdParam || toolIdParam.trim() === '') {
      console.warn('[sessionStore] Invalid toolId provided, rejecting:', toolIdParam)
      return
    }

    // 如果正在流式输出，拒绝清空 messages
    if (loading.value) {
      console.warn('正在流式输出，拒绝重新初始化工具')
      return
    }

    // 如果 toolId 相同且 messages 不为空，不需要重新初始化
    if (toolId.value === toolIdParam && messages.value.length > 0) {
      return
    }

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
    messages.value.push({
      role: 'user',
      content,
      pending: true,
      created_at: new Date().toISOString(),
    })
    const userMsgIndex = messages.value.length - 1

    // 创建 AI 回复消息占位符（显示加载状态）
    messages.value.push({
      role: 'assistant',
      content: '',
      artifacts: [],
      pending: true, // 标记为加载中
      created_at: new Date().toISOString(),
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
          model: currentModel.value || undefined, // 传递当前选择的模型
        },
        (data) => {
          // 调试日志：记录所有收到的数据
          console.log('[sessionStore] 收到 SSE 数据:', data)

          // 处理流式数据块
          if (data.type === 'session_id') {
            // 更新会话ID
            if (data.session_id) {
              sessionId.value = data.session_id
            }
          } else if (data.type === 'content') {
            // 处理流式数据块 - 直接追加，无去重逻辑
            if (messages.value[aiMsgIndex]) {
              const currentMsg = messages.value[aiMsgIndex]
              messages.value[aiMsgIndex] = {
                ...currentMsg,
                content: currentMsg.content + (data.content || '')
              }
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
            // 标题生成完成，记录会话ID以便刷新列表
            if (data.session_id) {
              titleGeneratedSessionId.value = data.session_id
            }
          } else if (data.type === 'error') {
            // 错误处理 - 不影响已生成的内容
            console.error('[sessionStore] 收到错误类型消息:', data)

            // 标记消息为错误状态，但保留已生成的内容
            if (messages.value[aiMsgIndex]) {
              messages.value[aiMsgIndex].error = data.error || '发送消息失败'
              messages.value[aiMsgIndex].pending = false
            }

            // 不再抛出异常，让流程正常结束
            // throw new Error(data.error || '发送消息失败')  // ❌ 注释掉
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

    // 如果正在流式输出，拒绝恢复会话
    if (loading.value) {
      console.warn('正在流式输出，拒绝恢复会话')
      return
    }

    // 如果 session ID 相同，不需要重新恢复
    if (sessionId.value === sessionIdParam && messages.value.length > 0) {
      return
    }

    loading.value = true
    error.value = null

    try {
      const response = await ApiService.getSessionDetail(sessionIdParam)

      sessionId.value = response.session_id

      // 验证tool_id：只有当tool_id有效时才更新
      // 这防止API返回null/undefined/空字符串导致toolId被清空
      if (response.tool_id && response.tool_id.trim() !== '') {
        toolId.value = response.tool_id
      } else {
        console.warn('[sessionStore] Invalid tool_id from API, preserving existing toolId:', {
          apiToolId: response.tool_id,
          preservedToolId: toolId.value
        })
      }

      // 转换消息格式
      messages.value = response.messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || (msg as any).created_at,
        artifacts: msg.artifacts || [],
      }))

      // 恢复模型选择
      if (response.model_provider && response.model_name) {
        currentModel.value = `${response.model_provider}:${response.model_name}`
        console.log('[sessionStore] 恢复会话模型:', currentModel.value)
      } else {
        currentModel.value = null
      }
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
   * 清空会话（不清空toolId，因为创建新会话不代表要切换工具）
   */
  function clearSession() {
    sessionId.value = null
    // 注意：不清空 toolId，因为用户只是想开始新对话，而不是切换工具
    // toolId.value = null  // <-- 这行被注释掉，保留toolId
    messages.value = []
    currentPreviewArtifact.value = null
    error.value = null

  }

  /**
   * 设置当前选择的模型
   */
  function setCurrentModel(model: string | null) {
    currentModel.value = model
    console.log('[sessionStore] 模型已切换为:', model)
  }

  /**
   * 计算两个字符串的相似度（简化版）
   */
  function calculateSimilarity(str1: string, str2: string): number {
    const len = Math.min(str1.length, str2.length)
    if (len === 0) return 0

    let sameChars = 0
    for (let i = 0; i < len; i++) {
      if (str1[i] === str2[i]) sameChars++
    }

    return sameChars / len
  }

  /**
   * 找到两个字符串的最佳分割点
   * 返回应该从 newContent 的第几个字符开始
   */
  function findSplitPosition(current: string, newContent: string): number {
    // 从后往前匹配，找到最长的公共后缀
    const maxCheck = Math.min(200, current.length, newContent.length)

    for (let i = maxCheck; i >= 10; i--) {
      const currentEnd = current.slice(-i).toLowerCase()
      const newStart = newContent.slice(0, i).toLowerCase()

      if (currentEnd === newStart) {
        return i
      }
    }

    return 0
  }

  /**
   * 完全重置状态（包括清空toolId，用于登出等场景）
   */
  function reset() {
    sessionId.value = null
    toolId.value = null  // reset会清空toolId
    messages.value = []
    currentPreviewArtifact.value = null
    error.value = null
    loading.value = false
    currentModel.value = null  // 清空模型选择

  }

  return {
    // 状态
    sessionId,
    toolId,
    messages,
    loading,
    error,
    currentPreviewArtifact,
    titleGeneratedSessionId,
    currentModel,
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
    setCurrentModel,
  }
})

