# backend/main.py
import os
import json
from typing import Optional, Tuple

from fastapi import FastAPI
from dotenv import load_dotenv
from openai import OpenAI

# 导入数据模型(DTO) 和 Prompt工厂
from schemas import UserRequest, RouterResponse
from prompts import ROUTER_SYSTEM_PROMPT, assemble_prompt

# 加载 .env 环境变量
load_dotenv()

app = FastAPI(title="AI Teacher Platform Backend")

# --- AI 模型工厂 (AI Provider Factory) ---

def get_ai_client() -> Tuple[Optional[OpenAI], str]:
    """
    根据配置初始化并返回兼容 OpenAI 协议的客户端。
    返回: (Client对象, 模型名称)
    """
    # 获取当前配置的服务商，默认为 kimi
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
        
    # 检查 Key 是否存在且格式正确
    if not api_key or not api_key.startswith("sk-"):
        print(f"⚠️ 警告: 未找到服务商 [{provider}] 的有效 Key，将使用 Mock 模式。")
        return None, "mock-model"
        
    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, model_name

# --- 业务逻辑层 (Service Layer) ---

def analyze_intent_with_ai(user_input: str) -> dict:
    """
    调用 AI Router 进行意图识别，返回 JSON 格式的元数据。
    """
    client, model_name = get_ai_client()

    # 如果没有 Client，返回本地模拟数据 (Mock)
    if not client:
        return {
            "intent": "agent_coder",
            "subject": "MockSubject",
            "topic": "Mocked Response",
            "user_language": "zh-CN",
            "reasoning": f"Local mock because {model_name} key is missing."
        }

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            response_format={"type": "json_object"}, # 强制 JSON 输出
            temperature=0.1 # 温度设低，保证路由判断的准确性
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        print(f"❌ 意图识别出错: {e}")
        # 出错时的降级处理
        return {
            "intent": "agent_planner",
            "subject": "Error",
            "topic": "Fallback",
            "user_language": "zh-CN",
            "reasoning": str(e)
        }

def generate_content_with_ai(intent: str, subject: str, topic: str) -> str:
    """
    根据意图，生成最终的教学内容 (HTML代码, SVG代码 或 文本教案)。
    """
    client, model_name = get_ai_client()
    
    # 1. 调用工厂组装 System Prompt
    system_prompt = assemble_prompt(intent, subject, topic)
    
    # 2. 组装 User Prompt (由于 System Prompt 已经很详细，这里只需简单触发)
    user_prompt = f"Please execute the task for topic: {topic}"

    print(f"🏭 正为 [{subject}] 学科生成 [{intent}] 内容，主题: {topic}")
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3 # 稍微增加一点创造性
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ 内容生成出错: {str(e)}"

# --- 接口层 (Controller Layer) ---

@app.post("/api/route", response_model=RouterResponse)
async def route_request(request: UserRequest):
    """
    测试接口：仅进行意图识别 (Router)，不生成内容。
    """
    result = analyze_intent_with_ai(request.user_input)
    return result

@app.post("/api/generate_all")
async def generate_all(request: UserRequest):
    """
    主干接口：执行 [路由识别] -> [内容生成] 的全流程。
    """
    print(f"🚀 收到全流程请求: {request.user_input}")

    # 第一步: 路由分析 (Brain)
    router_result = analyze_intent_with_ai(request.user_input)
    
    intent = router_result.get("intent")
    subject = router_result.get("subject")
    topic = router_result.get("topic")
    
    # 第二步: 内容生成 (Hands)
    # 注意：Kimi 生成长代码可能需要 15-30 秒
    generated_content = generate_content_with_ai(intent, subject, topic)
    
    return {
        "router_info": router_result,
        "content": generated_content
    }

if __name__ == "__main__":
    import uvicorn
    # 启动服务，端口 8000，开启热重载
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)