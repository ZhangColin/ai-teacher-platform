# main.py
import os
import json
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from openai import OpenAI
from typing import Optional, Tuple

# 导入 DTO
from schemas import UserRequest, RouterResponse

# 1. 加载环境变量
load_dotenv()

app = FastAPI(title="AI Teacher Platform Backend")

# --- 核心资产：Router System Prompt ---
ROUTER_SYSTEM_PROMPT = """
You are the intelligent routing core for an AI Education Platform. 
Your job is to analyze the User Input and strictly categorize it into the correct 'Agent Intent' and extract metadata.

Constraint: Output MUST be valid JSON only. No markdown.

Agents Definition:
- agent_coder: Interactive tools, simulators, games, HTML/JS code.
- agent_visual: Visualizations, diagrams, charts, timelines, SVG code.
- agent_planner: Lesson plans, teaching guides, quiz questions, text-based content.
- agent_roleplay: Conversing with a specific persona.

Schema:
{
  "intent": "agent_coder" | "agent_visual" | "agent_planner" | "agent_roleplay",
  "subject": "Chinese" | "Math" | "English" | "Physics" | ... | "General",
  "topic": "Extracted core topic in English",
  "user_language": "Detected language code"
}
"""

# --- 架构升级：AI Provider Factory (模型工厂) ---
def get_ai_client() -> Tuple[Optional[OpenAI], str]:
    """
    根据配置返回：(Client对象, 模型名称)
    """
    provider = os.getenv("CURRENT_PROVIDER", "kimi").lower()
    
    api_key = ""
    base_url = ""
    model_name = ""

    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL")
        model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        
    elif provider == "kimi":
        api_key = os.getenv("KIMI_API_KEY")
        base_url = os.getenv("KIMI_BASE_URL")
        model_name = os.getenv("KIMI_MODEL", "moonshot-v1-8k")
        
    # 未来可以在这里加 Gemini, Claude ...
    
    # 检查 Key 是否存在
    if not api_key or not api_key.startswith("sk-"):
        print(f"⚠️ Warning: No valid API Key found for provider [{provider}]. Using Mock Mode.")
        return None, "mock-model"
        
    # 初始化 OpenAI 兼容客户端 (Kimi 和 DeepSeek 都支持这个协议)
    client = OpenAI(api_key=api_key, base_url=base_url)
    print(f"✅ AI Client Initialized: [{provider}] using model [{model_name}]")
    return client, model_name

# --- Service Logic ---
def analyze_intent_with_ai(user_input: str) -> dict:
    client, model_name = get_ai_client()

    # 1. Mock 模式 (无 Key 时)
    if not client:
        return {
            "intent": "agent_coder",
            "subject": "MockSubject",
            "topic": "Mocked Response (No Key)",
            "user_language": "zh-CN",
            "reasoning": f"Local mock because {model_name} key is missing."
        }

    # 2. 真实调用
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            response_format={"type": "json_object"}, 
            temperature=0.1 
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        print(f"❌ Error calling AI: {e}")
        # 错误降级
        return {
            "intent": "agent_planner",
            "subject": "Error",
            "topic": "Fallback",
            "user_language": "zh-CN",
            "reasoning": str(e)
        }

# --- Controller ---
@app.post("/api/route", response_model=RouterResponse)
async def route_request(request: UserRequest):
    print(f"收到请求: {request.user_input}")
    result = analyze_intent_with_ai(request.user_input)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)