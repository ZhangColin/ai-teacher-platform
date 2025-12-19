// src/types.ts

// 1. 定义消息角色 (相当于 Java Enum)
export type Role = 'user' | 'assistant' | 'system';

// 2. 定义聊天记录的数据结构
export interface ChatMessage {
  role: Role;
  content: string;
  // 后面我们会用到这个字段，区分是纯文本还是代码
  type?: 'text' | 'code' | 'plan'; 
}

// 3. 定义后端接口返回的数据结构 (对应 Python 的 RouterResponse + Content)
export interface RouterInfo {
  intent: string;
  subject: string;
  topic: string;
  user_language: string;
}

export interface ApiResponse {
  router_info: RouterInfo;
  content: string; // 这里可能是 HTML 代码，也可能是 Markdown 文本
}