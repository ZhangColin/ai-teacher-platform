# schemas.py
from pydantic import BaseModel, Field
from typing import Literal, Optional

# --- Request DTO ---
class UserRequest(BaseModel):
    user_input: str = Field(..., description="老师的原始输入", example="帮我做一个平抛运动演示")

# --- Response DTO ---
# 这里对应我们之前定义的 Router JSON 结构
class RouterResponse(BaseModel):
    intent: Literal["agent_coder", "agent_visual", "agent_planner", "agent_roleplay"]
    subject: Literal[
        "Chinese", "Math", "English", 
        "Physics", "Chemistry", "Biology", 
        "History", "Politics", "Geography", 
        "Music", "PE", "General"
    ]
    topic: str = Field(..., description="提取的核心主题(英文)")
    user_language: str = Field(..., description="用户语言代码")
    
    # 额外加一个字段，方便调试看结果
    reasoning: Optional[str] = Field(None, description="AI的思考过程(如果有)")