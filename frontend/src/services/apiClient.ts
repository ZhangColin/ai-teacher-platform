/** API 客户端服务 - 封装后端接口调用 */
import axios, { type AxiosInstance, type AxiosError } from 'axios'
import type {
  AgentListResponse,
  ToolListResponse,
  SessionInitResponse,
  ChatRequest,
  ChatResponse,
  ConversationListResponse,
  SessionDetailResponse,
  UpdateSessionRequest,
  UpdateSessionResponse,
  LoginRequest,
  LoginResponse,
  UserListResponse,
  CreateUserRequest,
  CreateUserResponse,
  UserInfo,
  CommonToolCategoryResponse,
  CommonToolDetail,
  WorkCategoryResponse,
  WorkDetail,
} from '../types'
import type { NavigationResponse } from '../types/navigation'

/**
 * API 错误响应格式
 */
export interface ApiErrorResponse {
  error_code: string
  error_message: string
  details?: Record<string, unknown>
}

/**
 * 创建 axios 实例
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000, // 30 秒超时
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * 请求拦截器
 */
apiClient.interceptors.request.use(
  (config) => {
    // 公开接口（不需要token）
    const publicEndpoints = ['/auth/login', '/auth/register']
    const isPublicEndpoint = publicEndpoints.some(endpoint => config.url?.includes(endpoint))
    
    // 非公开接口才添加认证token
    if (!isPublicEndpoint) {
      const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器 - 统一错误处理
 */
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError<ApiErrorResponse | { detail?: string }>) => {
    // 统一错误处理
    if (error.response) {
      const status = error.response.status
      
      // 401 未授权：Token过期或无效，清除本地认证信息并跳转到登录页
      if (status === 401) {
        // 清除本地token
        localStorage.removeItem('auth_token')
        localStorage.removeItem('auth_user')
        sessionStorage.removeItem('auth_token')
        sessionStorage.removeItem('auth_user')
        
        // 如果不在登录页，跳转到登录页
        if (window.location.pathname !== '/login') {
          window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`
        }
        
        return Promise.reject(new Error('登录已过期，请重新登录'))
      }
      
      // 其他错误
      const errorData = error.response.data
      // FastAPI默认错误格式是 { detail: string }，也支持自定义格式 { error_message: string }
      const errorMessage = 
        (errorData as { detail?: string })?.detail ||
        (errorData as ApiErrorResponse)?.error_message ||
        error.message ||
        '请求失败'
      return Promise.reject(new Error(errorMessage))
    } else if (error.request) {
      // 请求已发出但没有收到响应
      return Promise.reject(new Error('网络错误，请检查网络连接'))
    } else {
      // 请求配置出错
      return Promise.reject(new Error('请求配置错误'))
    }
  }
)

/**
 * API 服务类
 */
export class ApiService {
  /**
   * 获取 Agent 列表（已废弃，请使用 getTools）
   */
  static async getAgents(): Promise<AgentListResponse> {
    const response = await apiClient.get<AgentListResponse>('/agents')
    return response.data
  }

  /**
   * 获取导航模块列表
   */
  static async getNavigationModules(): Promise<NavigationResponse> {
    const response = await apiClient.get<NavigationResponse>('/navigation')
    return response.data
  }

  /**
   * 获取工具列表（按分类组织）
   */
  static async getTools(): Promise<ToolListResponse> {
    const response = await apiClient.get<ToolListResponse>('/tools')
    return response.data
  }

  /**
   * 获取指定工具集的工具列表（按分类组织）
   * @param toolsetId 工具集ID
   */
  static async getToolsetTools(toolsetId: string): Promise<ToolListResponse> {
    const response = await apiClient.get<ToolListResponse>(`/toolsets/${toolsetId}/tools`)
    return response.data
  }

  /**
   * 创建会话
   * @param agentId Agent 唯一标识符
   */
  static async createSession(agentId: string): Promise<SessionInitResponse> {
    const response = await apiClient.post<SessionInitResponse>(
      `/agents/${agentId}/sessions`
    )
    return response.data
  }

  /**
   * 发送消息（新接口，支持延迟创建会话）
   * @param toolId 工具唯一标识符
   * @param request 对话请求（包含 session_id 可选）
   */
  static async chat(
    toolId: string,
    request: ChatRequest
  ): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>(
      `/tools/${toolId}/chat`,
      request
    )
    return response.data
  }

  /**
   * 发送消息（流式接口，支持延迟创建会话）
   * @param toolId 工具唯一标识符
   * @param request 对话请求（包含 session_id 可选）
   * @param onChunk 接收数据块的回调函数
   */
  static async chatStream(
    toolId: string,
    request: ChatRequest,
    onChunk: (data: { type: string; session_id?: string; content?: string; artifacts?: any[]; error?: string }) => void
  ): Promise<void> {
    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
    if (!token) {
      throw new Error('未登录')
    }

    const response = await fetch(`/api/v1/tools/${toolId}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(request)
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '请求失败' }))
      throw new Error(error.detail || '请求失败')
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('无法读取响应流')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 保留最后一个不完整的行

        for (const line of lines) {
          const trimmedLine = line.trim()
          if (trimmedLine.startsWith('data: ')) {
            try {
              const jsonStr = trimmedLine.slice(6).trim()
              if (jsonStr) {
                const data = JSON.parse(jsonStr)
                console.log('收到流式数据块:', data.type, data.content?.substring(0, 20) || '')
                onChunk(data)
              }
            } catch (e) {
              console.error('解析 SSE 数据失败:', e, trimmedLine)
            }
          } else if (trimmedLine === '') {
            // 空行，跳过
            continue
          }
        }
      }

      // 处理最后一行
      const trimmedBuffer = buffer.trim()
      if (trimmedBuffer.startsWith('data: ')) {
        try {
          const jsonStr = trimmedBuffer.slice(6).trim()
          if (jsonStr) {
            const data = JSON.parse(jsonStr)
            console.log('收到流式数据块（最后）:', data.type)
            onChunk(data)
          }
        } catch (e) {
          console.error('解析 SSE 数据失败:', e, trimmedBuffer)
        }
      }
    } finally {
      reader.releaseLock()
    }
  }

  /**
   * 获取历史对话列表
   * @param toolId 工具唯一标识符
   */
  static async getConversations(toolId: string): Promise<ConversationListResponse> {
    const response = await apiClient.get<ConversationListResponse>(
      `/tools/${toolId}/conversations`
    )
    return response.data
  }

  /**
   * 获取会话详情
   * @param sessionId 会话 UUID
   */
  static async getSessionDetail(sessionId: string): Promise<SessionDetailResponse> {
    const response = await apiClient.get<SessionDetailResponse>(
      `/sessions/${sessionId}`
    )
    return response.data
  }

  /**
   * 更新会话标题
   * @param sessionId 会话 UUID
   * @param request 更新请求
   */
  static async updateSessionTitle(
    sessionId: string,
    request: UpdateSessionRequest
  ): Promise<UpdateSessionResponse> {
    const response = await apiClient.patch<UpdateSessionResponse>(
      `/sessions/${sessionId}`,
      request
    )
    return response.data
  }

  /**
   * 删除会话
   * @param sessionId 会话 UUID
   */
  static async deleteSession(sessionId: string): Promise<void> {
    await apiClient.delete(`/sessions/${sessionId}`)
  }

  /**
   * 用户登录
   * @param request 登录请求
   */
  static async login(request: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/auth/login', request)
    return response.data
  }

  /**
   * 获取当前用户信息
   */
  static async getCurrentUser(): Promise<{ user: UserInfo }> {
    const response = await apiClient.get<{ user: UserInfo }>('/auth/me')
    return response.data
  }

  /**
   * 获取用户列表
   * @param page 页码（可选，默认1）
   * @param pageSize 每页数量（可选，默认20）
   */
  static async getUserList(page: number = 1, pageSize: number = 20): Promise<UserListResponse> {
    const response = await apiClient.get<UserListResponse>('/admin/users', {
      params: { page, page_size: pageSize },
    })
    return response.data
  }

  /**
   * 创建用户
   * @param request 创建用户请求
   */
  static async createUser(request: CreateUserRequest): Promise<CreateUserResponse> {
    const response = await apiClient.post<CreateUserResponse>('/admin/users', request)
    return response.data
  }

  // ==================== 常用工具模块 ====================

  /**
   * 获取常用工具分类列表（包含每个分类下的工具列表）
   */
  static async getCommonToolCategories(): Promise<CommonToolCategoryResponse> {
    const response = await apiClient.get<CommonToolCategoryResponse>('/common-tools/categories')
    return response.data
  }

  /**
   * 获取常用工具详情
   * @param toolId 工具ID
   */
  static async getCommonToolDetail(toolId: string): Promise<CommonToolDetail> {
    const response = await apiClient.get<CommonToolDetail>(`/common-tools/tools/${toolId}`)
    return response.data
  }

  // ==================== 作品展示模块 ====================

  /**
   * 获取作品分类列表（包含每个分类下的作品列表）
   */
  static async getWorkCategories(): Promise<WorkCategoryResponse> {
    const response = await apiClient.get<WorkCategoryResponse>('/works/categories')
    return response.data
  }

  /**
   * 获取作品详情
   * @param workId 作品ID
   */
  static async getWorkDetail(workId: string): Promise<WorkDetail> {
    const response = await apiClient.get<WorkDetail>(`/works/${workId}`)
    return response.data
  }
}

export default apiClient

