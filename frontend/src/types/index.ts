/** 前端类型定义 - 与后端 Model 对应 */

/**
 * Agent 列表项（用于 API 响应）
 */
export interface AgentListItem {
  agent_id: string
  name: string
  description?: string
  icon?: string
}

/**
 * Agent 列表响应
 */
export interface AgentListResponse {
  agents: AgentListItem[]
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
  history?: Message[] // 历史消息列表（可选）
}

/**
 * 对话响应
 */
export interface ChatResponse {
  reply: string // AI 的文本回复内容（完整 Markdown 文本）
  artifacts: Artifact[] // 从回复中解析出的成果物列表（代码块内容）
}

