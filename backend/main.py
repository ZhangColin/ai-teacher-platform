# backend/main.py
import os
import json
from typing import Optional, Tuple, List

from fastapi import FastAPI
from dotenv import load_dotenv
from openai import OpenAI

# 导入数据模型和提示词工厂
from schemas import UserRequest, RouterResponse, Message
from prompts import ROUTER_SYSTEM_PROMPT, assemble_prompt

# 加载环境变量
load_dotenv()

app = FastAPI(title="AI Teacher Platform Backend")

# --- AI 客户端初始化工厂 ---

def get_ai_client() -> Tuple[Optional[OpenAI], str]:
    """
    根据配置文件获取 OpenAI 兼容的客户端实例和模型名称。
    支持 DeepSeek, Kimi 等兼容 OpenAI 协议的模型。
    """
    provider = os.getenv("CURRENT_PROVIDER", "kimi").lower()
    
    api_key = ""
    base_url = ""
    model_name = ""

    # 根据服务商读取对应的环境变量
    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL")
        model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    elif provider == "kimi":
        api_key = os.getenv("KIMI_API_KEY")
        base_url = os.getenv("KIMI_BASE_URL")
        model_name = os.getenv("KIMI_MODEL", "moonshot-v1-8k")
        
    # 校验 API Key 是否有效
    if not api_key or not api_key.startswith("sk-"):
        print(f"警告: 未找到服务商 [{provider}] 的有效 Key，将使用 Mock 模式。")
        return None, "mock-model"
        
    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, model_name

# --- 核心业务逻辑 ---

def analyze_intent_with_ai(user_input: str) -> dict:
    """
    使用专门的路由提示词分析用户输入。
    返回结构化 JSON 数据，包含意图(intent)、学科(subject)、主题(topic)等元数据。
    """
    client, model_name = get_ai_client()

    # 无客户端时的模拟返回（用于本地无网调试）
    if not client:
        return {
            "intent": "agent_coder",
            "subject": "MockSubject",
            "topic": "Mocked Response",
            "user_language": "zh-CN",
            "reasoning": f"Local mock because {model_name} key is missing."
        }

    try:
        # 调用 AI 进行分类，强制要求返回 JSON 格式
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            response_format={"type": "json_object"}, 
            temperature=0.1 # 低温度以确保分类结果的稳定性
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        print(f"意图识别异常: {e}")
        # 异常时的兜底策略，默认转为普通问答
        return {
            "intent": "agent_planner",
            "subject": "Error",
            "topic": "Fallback",
            "user_language": "zh-CN",
            "reasoning": str(e)
        }

def generate_content_with_ai(intent: str, subject: str, topic: str, history: List[Message], current_input: str) -> str:
    """
    根据路由结果和对话历史生成具体的教学内容。
    包含：系统提示词组装 -> 历史记录回填 -> 调用 AI 生成。
    """
    client, model_name = get_ai_client()
    
    # 1. 根据意图和学科，从工厂获取对应的系统角色设定 (System Prompt)
    system_prompt_content = assemble_prompt(intent, subject, topic)
    
    # 2. 构建消息链：System Prompt + History + Current Input
    messages = [{"role": "system", "content": system_prompt_content}]
    
    # 选取最近的 N 轮对话历史，避免 Token 超出限制
    # 这里选取最近 6 条（3轮对话）作为上下文
    recent_history = history[-6:] 
    
    for msg in recent_history:
        messages.append({"role": msg.role, "content": msg.content})
        
    # 将当前用户的最新输入追加到消息链末尾
    messages.append({"role": "user", "content": current_input})

    print(f"正在生成内容... 意图:[{intent}] 学科:[{subject}] 上下文数量:[{len(recent_history)}]")
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.3 # 适度保留创造性
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"内容生成失败: {str(e)}"

# --- API 接口定义 ---

@app.post("/api/route", response_model=RouterResponse)
async def route_request(request: UserRequest):
    """
    仅用于测试意图识别逻辑的接口。
    """
    result = analyze_intent_with_ai(request.user_input)
    return result

@app.post("/api/generate_all")
async def generate_all(request: UserRequest):
    """
    全流程接口：接收用户输入和历史记录，先进行意图路由，再生成具体内容。
    """
    print(f"收到请求: {request.user_input}")
    
    # 1. 路由分析
    # 目前路由主要基于当前那一句指令来判断意图
    router_result = analyze_intent_with_ai(request.user_input)
    
    intent = router_result.get("intent")
    subject = router_result.get("subject")
    topic = router_result.get("topic")
    
    # 2. 内容生成
    # 将历史记录和当前输入一并传入，实现多轮对话记忆
    generated_content = generate_content_with_ai(
        intent, 
        subject, 
        topic, 
        request.history, 
        request.user_input
    )
    
    return {
        "router_info": router_result,
        "content": generated_content
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)