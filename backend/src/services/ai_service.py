"""AI 服务：调用 LLM API"""
import os
import logging
import asyncio
from typing import Optional, Tuple, List, Dict, AsyncGenerator
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
            # 记录系统提示词（用于调试）
            logger.info(f"生成欢迎消息 - 系统提示词长度: {len(system_prompt)} 字符")
            logger.debug(f"系统提示词内容: {system_prompt[:200]}...")
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "请用一句话介绍你自己，并询问用户需要什么帮助。"}
                ],
                temperature=0.7
            )
            result = response.choices[0].message.content
            logger.info(f"AI 返回的欢迎消息: {result[:100]}...")
            return result
        except Exception as e:
            logger.error(f"AI 服务调用异常（生成欢迎消息）: {e}", exc_info=True)
            return "欢迎使用 AI 助手！抱歉，当前服务暂时不可用，请稍后重试。"
    
    async def chat(self, system_prompt: str, history: List[Dict[str, str]], user_message: str) -> str:
        """
        进行对话（非流式）
        
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
            
            # 记录系统提示词（用于调试）
            logger.info(f"对话请求 - 系统提示词长度: {len(system_prompt)} 字符, 历史消息数: {len(history)}, 用户消息: {user_message[:50]}...")
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7
            )
            result = response.choices[0].message.content
            logger.info(f"AI 返回的回复长度: {len(result)} 字符")
            return result
        except Exception as e:
            logger.error(f"AI 服务调用异常（对话）: {e}", exc_info=True)
            return "抱歉，当前服务暂时不可用，请稍后重试。"
    
    async def chat_stream(self, system_prompt: str, history: List[Dict[str, str]], user_message: str) -> AsyncGenerator[str, None]:
        """
        进行对话（流式输出）
        
        Args:
            system_prompt: Agent 的系统提示词
            history: 历史消息列表（格式：[{"role": "user/assistant", "content": "..."}, ...]）
            user_message: 用户当前消息
            
        Yields:
            str: AI 生成的回复片段（逐块返回）
        """
        # 无客户端时的模拟返回
        if not self.client:
            mock_reply = f"Mock 回复：收到你的消息「{user_message}」"
            # 模拟流式输出
            for char in mock_reply:
                yield char
                await asyncio.sleep(0.05)  # 模拟延迟
            return
        
        try:
            # 构建消息链：System Prompt + History + Current Input
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加历史消息
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": user_message})
            
            # 记录系统提示词（用于调试）
            logger.info(f"流式对话请求 - 系统提示词长度: {len(system_prompt)} 字符, 历史消息数: {len(history)}, 用户消息: {user_message[:50]}...")
            
            # 使用流式输出（同步调用，需要在异步函数中处理）
            # 注意：OpenAI 客户端的流式调用是同步的，需要在异步上下文中处理
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                stream=True  # 启用流式输出
            )
            
            # 逐块返回内容（在异步上下文中处理同步流）
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
                        # 让出控制权，允许其他协程运行，确保流式数据及时发送
                        await asyncio.sleep(0.001)  # 很小的延迟，确保流式效果
                    
        except Exception as e:
            logger.error(f"AI 服务调用异常（流式对话）: {e}", exc_info=True)
            yield "抱歉，当前服务暂时不可用，请稍后重试。"

