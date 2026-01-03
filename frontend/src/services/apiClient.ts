/** API 客户端服务 - 封装后端接口调用 */
import axios, { type AxiosInstance, type AxiosError } from 'axios'
import type {
  AgentListResponse,
  SessionInitResponse,
  ChatRequest,
  ChatResponse,
  LoginRequest,
  LoginResponse,
  UserListResponse,
  CreateUserRequest,
  CreateUserResponse,
  UserInfo,
} from '../types'

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
    // 添加认证 token
    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
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
      // 服务器返回了错误响应
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
   * 获取 Agent 列表
   */
  static async getAgents(): Promise<AgentListResponse> {
    const response = await apiClient.get<AgentListResponse>('/agents')
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
   * 发送消息
   * @param sessionId 会话 UUID
   * @param request 对话请求
   */
  static async chat(
    sessionId: string,
    request: ChatRequest
  ): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>(
      `/sessions/${sessionId}/chat`,
      request
    )
    return response.data
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
}

export default apiClient

