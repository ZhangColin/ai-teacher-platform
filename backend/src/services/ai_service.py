"""AI 服务：调用 LLM API"""
import os
import logging
from typing import Optional, Tuple, List, Dict
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


class AIService:
    """AI 服务客户端"""
    
    def __init__(self):
        """初始化 AI 服务"""
        self.client, self.model_name = self._get_ai_client()
    
    def _get_ai_client(self) -> Tuple[Optional[OpenAI], str]:
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
            logger.warning(f"未找到服务商 [{provider}] 的有效 Key，将使用 Mock 模式。")
            return None, "mock-model"
        
        client = OpenAI(api_key=api_key, base_url=base_url)
        return client, model_name
    
    async def generate_welcome_message(self, system_prompt: str) -> str:
        """
        生成欢迎消息
        
        Args:
            system_prompt: Agent 的系统提示词
            
        Returns:
            AI 生成的欢迎消息
        """
        # 无客户端时的模拟返回（用于本地无网调试）
        if not self.client:
            return "你好！我是你的 AI 助手。请告诉我你需要什么帮助。"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "请用一句话介绍你自己，并询问用户需要什么帮助。"}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI 服务调用异常（生成欢迎消息）: {e}", exc_info=True)
            return "欢迎使用 AI 助手！抱歉，当前服务暂时不可用，请稍后重试。"
    
    async def chat(self, system_prompt: str, history: List[Dict[str, str]], user_message: str) -> str:
        """
        进行对话
        
        Args:
            system_prompt: Agent 的系统提示词
            history: 历史消息列表（格式：[{"role": "user/assistant", "content": "..."}, ...]）
            user_message: 用户当前消息
            
        Returns:
            AI 生成的回复
        """
        # 无客户端时的模拟返回
        if not self.client:
            return f"Mock 回复：收到你的消息「{user_message}」"
        
        try:
            # 构建消息链：System Prompt + History + Current Input
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加历史消息
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": user_message})
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI 服务调用异常（对话）: {e}", exc_info=True)
            return "抱歉，当前服务暂时不可用，请稍后重试。"

