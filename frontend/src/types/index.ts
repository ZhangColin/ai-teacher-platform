/** 前端类型定义 - 与后端 Model 对应 */

/**
 * Agent 列表项（用于 API 响应）- 已废弃，保留以保持向后兼容
 */
export interface AgentListItem {
  agent_id: string
  name: string
  description?: string
  icon?: string
}

/**
 * Agent 列表响应 - 已废弃，保留以保持向后兼容
 */
export interface AgentListResponse {
  agents: AgentListItem[]
}

/**
 * 工具列表项（用于 API 响应）
 */
export interface ToolListItem {
  tool_id: string // 工具唯一标识符
  name: string // 工具名称
  description?: string // 工具描述
  icon?: string // 图标标识（可选）
  category: string // 分类名称
  visible: boolean // 是否在工具选择器中显示
  type: 'normal' | 'placeholder' // 工具类型
  welcome_message?: string // 欢迎语（可选，用于占位工具）
}

/**
 * 分类组（用于 API 响应）
 */
export interface CategoryGroup {
  name: string // 分类名称
  icon?: string // 分类图标（可选）
  tools: ToolListItem[] // 该分类下的工具列表
}

/**
 * 工具列表响应
 */
export interface ToolListResponse {
  categories: CategoryGroup[] // 按分类组织的工具列表
}

/**
 * UI 配置值对象
 */
export interface UIConfig {
  show_preview: boolean
  preview_types: string[]
}

/**
 * 成果物值对象（不可变）
 */
export interface Artifact {
  type: string // 成果物类型，由代码块语言标识决定
  content: string // 代码块中的原始内容
  language: string // 代码块的语言标识（如 'markdown', 'html', 'svg'）
  timestamp: string // 成果物生成时间（ISO 8601 格式）
}

/**
 * 消息实体
 */
export interface Message {
  role: 'user' | 'assistant' // 消息角色
  content: string // 消息内容（Markdown 格式）
  timestamp?: string // 消息时间戳（ISO 8601 格式，可选）
  artifacts?: Artifact[] // 消息中包含的成果物列表（可选）
  error?: string // 错误信息（可选，用于显示发送失败）
  pending?: boolean // 是否正在发送（可选，用于显示加载状态）
}

/**
 * 会话初始化响应
 */
export interface SessionInitResponse {
  session_id: string // 会话 UUID
  welcome_message: string // AI 生成的欢迎语（第一条消息）
  ui_config: UIConfig // UI 配置，如是否开启预览、预览类型等
  artifacts: Artifact[] // 欢迎语中可能包含的成果物（如代码块）
}

/**
 * 对话请求
 */
export interface ChatRequest {
  message: string // 用户输入的消息
  session_id?: string | null // 会话 UUID（可选，如果有则继续会话，没有则创建新会话）
  history?: Message[] // 历史消息列表（可选）
}

/**
 * 对话响应
 */
export interface ChatResponse {
  session_id: string // 会话 UUID。首次调用返回新创建的session_id，后续调用返回原session_id
  reply: string // AI 的文本回复内容（完整 Markdown 文本）
  artifacts: Artifact[] // 从回复中解析出的成果物列表（代码块内容）
}

/**
 * 历史对话列表项
 */
export interface ConversationListItem {
  session_id: string // 会话 UUID
  title: string // 会话标题
  updated_at: string // 最后更新时间（ISO 8601 格式）
}

/**
 * 历史对话列表响应
 */
export interface ConversationListResponse {
  conversations: ConversationListItem[] // 对话列表
}

/**
 * 会话详情响应
 */
export interface SessionDetailResponse {
  session_id: string // 会话 UUID
  tool_id: string // 工具唯一标识符
  title: string // 会话标题
  created_at: string // 创建时间（ISO 8601 格式）
  updated_at: string // 最后更新时间（ISO 8601 格式）
  messages: Message[] // 消息列表
}

/**
 * 更新会话标题请求
 */
export interface UpdateSessionRequest {
  title: string // 新的会话标题
}

/**
 * 更新会话标题响应
 */
export interface UpdateSessionResponse {
  session_id: string // 会话 UUID
  title: string // 更新后的会话标题
}

/**
 * 用户信息（用于API响应，不包含密码）
 */
export interface UserInfo {
  user_id: string // 用户唯一标识（UUID）
  username: string // 用户名（用于登录）
  nickname?: string // 用户昵称（可选，用于显示，如未填写则使用用户名）
  email?: string // 用户邮箱（可选，用于登录）
  phone?: string // 用户手机号（可选，用于登录）
  avatar?: string // 用户头像URL（可选，默认头像）
}

/**
 * 登录请求
 */
export interface LoginRequest {
  account: string // 用户账号（用户名、邮箱或手机号）
  password: string // 用户密码
  remember_me: boolean // 是否记住我（影响Token有效期）
}

/**
 * 登录响应
 */
export interface LoginResponse {
  token: string // JWT Token，用于后续请求的身份验证
  user: UserInfo // 用户基本信息
  expires_in: number // Token有效期（秒），如：604800（7天）或86400（24小时）
}

/**
 * 用户列表项
 */
export interface UserListItem {
  user_id: string // 用户唯一标识（UUID）
  username: string // 用户名（用于登录）
  nickname?: string // 用户昵称（可选，用于显示，如未填写则使用用户名）
  email?: string // 用户邮箱（可选，用于登录）
  phone?: string // 用户手机号（可选，用于登录）
  avatar?: string // 用户头像URL
  created_at: string // 用户创建时间（ISO 8601 格式）
}

/**
 * 用户列表响应
 */
export interface UserListResponse {
  users: UserListItem[] // 用户列表
  total: number // 用户总数
  page: number // 当前页码
  page_size: number // 每页数量
}

/**
 * 创建用户请求
 */
export interface CreateUserRequest {
  username: string // 用户名（必填，用于登录，必须唯一）
  nickname?: string // 用户昵称（可选，用于显示，如未填写则使用用户名）
  email?: string // 用户邮箱（可选，用于登录）
  phone?: string // 用户手机号（可选，用于登录）
  password: string // 用户密码
  avatar?: string // 用户头像URL（可选）
}

/**
 * 创建用户响应
 */
export interface CreateUserResponse {
  user: UserInfo // 新创建的用户信息
}

// ==================== 常用工具模块 ====================

/**
 * 常用工具列表项（用于工具卡片页）
 */
export interface CommonToolListItem {
  id: string // 工具ID
  name: string // 工具名称
  description: string // 工具描述
  type: 'built-in' | 'html' // 工具类型
  icon?: string // 图标（可选）
  order: number // 排序字段
}

/**
 * 工具分类组（包含分类信息和工具列表）
 */
export interface ToolCategoryGroup {
  id: string // 分类ID
  name: string // 分类名称
  icon?: string // 分类图标（可选）
  order: number // 排序字段
  tools: CommonToolListItem[] // 该分类下的工具列表
}

/**
 * 常用工具分类响应
 */
export interface CommonToolCategoryResponse {
  categories: ToolCategoryGroup[] // 分类列表
}

/**
 * 常用工具详情
 */
export interface CommonToolDetail {
  id: string // 工具ID
  name: string // 工具名称
  description: string // 工具描述
  category_id: string // 分类ID
  category_name: string // 分类名称
  type: 'built-in' | 'html' // 工具类型
  icon?: string // 图标（可选）
  order: number // 排序字段
  html_url?: string // HTML工具访问URL（仅HTML工具）
  created_at: string // 创建时间（ISO 8601格式）
}

