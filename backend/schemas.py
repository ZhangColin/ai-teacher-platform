# backend/schemas.py
from typing import Optional, List
from pydantic import BaseModel, Field

# --- 1. 基础消息模型 ---
class Message(BaseModel):
    role: str = Field(..., description="消息角色", examples=["user", "assistant", "system"])
    content: str = Field(..., description="消息内容")

# --- 2. 用户请求模型 (User Request DTO) ---
class UserRequest(BaseModel):
    user_input: str = Field(..., description="用户当前的输入指令", examples=["帮我做一个物理平抛运动演示"])
    # 新增：历史对话记录，默认为空列表
    history: List[Message] = Field(default=[], description="上下文对话历史，用于多轮对话")

# --- 3. 路由响应模型 (Router Response DTO) ---
class RouterResponse(BaseModel):
    intent: str = Field(..., description="AI 识别出的意图代理", examples=["agent_coder", "agent_planner"])
    subject: str = Field(..., description="识别出的学科", examples=["Physics", "Math"])
    topic: str = Field(..., description="提取的核心主题 (英文)", examples=["projectile motion"])
    user_language: str = Field(..., description="检测到的用户语言", examples=["zh-CN"])
    reasoning: Optional[str] = Field(None, description="AI 的推理过程分析 (可选)")