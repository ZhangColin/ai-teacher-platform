"""会话标题生成服务"""
import logging
from typing import Optional, Tuple
from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from src.services.model_provider_service import ModelProviderService

logger = logging.getLogger(__name__)


class TitleGenerator:
    """会话标题生成器"""

    def __init__(self, db: Session):
        """
        初始化标题生成器

        Args:
            db: 数据库会话
        """
        self.db = db
        self.model_provider_service = ModelProviderService(db)

    def _get_ai_client(self, provider_code: str, model_name: str) -> Optional[AsyncOpenAI]:
        """
        根据供应商代码和模型名称获取 AI 客户端

        Args:
            provider_code: 供应商代码（如 deepseek, openai）
            model_name: 模型名称

        Returns:
            AsyncOpenAI 客户端，如果获取失败返回 None
        """
        try:
            # 从数据库获取供应商配置
            provider = self.model_provider_service.get_provider_by_code(provider_code)
            if not provider:
                logger.warning(f"标题生成：供应商 '{provider_code}' 不存在")
                return None

            if not provider.is_enabled:
                logger.warning(f"标题生成：供应商 '{provider_code}' 已禁用")
                return None

            # 获取解密后的 API Key
            api_key = self.model_provider_service.get_provider_api_key(provider.id)
            base_url = provider.base_url

            # 创建异步客户端
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=30.0,
                max_retries=1
            )

            logger.info(f"标题生成客户端创建成功 - 服务商: {provider_code}, 模型: {model_name}")
            return client

        except Exception as e:
            logger.error(f"标题生成：获取 AI 客户端失败 - {e}")
            return None

    async def generate_title(
        self,
        user_message: str,
        ai_response: Optional[str] = None,
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> str:
        """
        智能生成会话标题

        Args:
            user_message: 用户消息
            ai_response: AI回复（可选）
            model_provider: 模型供应商代码（可选）
            model_name: 模型名称（可选）

        Returns:
            生成的标题（8-15个字）
        """
        user_msg = user_message.strip()

        # 如果用户消息为空，直接返回默认标题
        if not user_msg:
            return "新对话"

        # 如果没有指定模型，使用降级方案
        if not model_provider or not model_name:
            logger.warning("标题生成：未指定模型，使用降级方案")
            return self._fallback_title(user_message)

        # 获取 AI 客户端
        client = self._get_ai_client(model_provider, model_name)
        if not client:
            logger.warning("标题生成：无法获取 AI 客户端，使用降级方案")
            return self._fallback_title(user_message)

        # 策略选择：短消息需要AI回复辅助
        if len(user_msg) < 10:
            ai_preview = (ai_response[:300] if ai_response else "")
            prompt = f"""请为以下对话生成一个简洁的标题（8-15个字）。
用户消息：{user_msg}
AI回复：{ai_preview}

直接输出标题，无需标点："""
        else:
            # 长消息只用用户消息（限制500字符以控制成本）
            prompt = f"""请为以下用户提问生成一个简洁的标题（8-15个字）。
用户提问：{user_msg[:500]}

直接输出标题，无需标点："""

        try:
            logger.info(f"开始生成会话标题 - 使用模型: {model_provider}:{model_name}")

            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=30,
                temperature=0.7
            )

            title = response.choices[0].message.content.strip()
            title = self._clean_title(title)

            if len(title) > 30:
                title = title[:30]

            logger.info(f"标题生成成功: {title}")
            return title if title else "新对话"

        except Exception as e:
            logger.error(f"AI生成标题失败: {e}")
            return self._fallback_title(user_message)

    def _clean_title(self, title: str) -> str:
        """清理标题，移除标点符号"""
        punctuation = '"\'。，！？、：；""''《》【】（）[]{}、，。！？；：'
        for char in punctuation:
            title = title.replace(char, '')
        return title.strip()

    def _fallback_title(self, user_message: str) -> str:
        """降级方案：使用简单截取生成标题"""
        msg = user_message.strip()
        if not msg:
            return "新对话"
        msg = msg.replace('\n', ' ').replace('\r', ' ')
        if len(msg) > 30:
            return msg[:30]
        else:
            return msg

    async def generate_title_with_usage(
        self,
        user_message: str,
        ai_response: Optional[str] = None,
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> Tuple[str, Optional[dict]]:
        """
        生成标题并返回 token 使用信息

        Returns:
            (标题, token使用信息字典) 元组
            token使用信息格式: {'prompt_tokens': int, 'completion_tokens': int, 'total_tokens': int}
        """
        user_msg = user_message.strip()
        if not user_msg:
            return ("新对话", None)

        if not model_provider or not model_name:
            logger.warning("标题生成：未指定模型，使用降级方案")
            return (self._fallback_title(user_message), None)

        client = self._get_ai_client(model_provider, model_name)
        if not client:
            logger.warning("标题生成：无法获取 AI 客户端，使用降级方案")
            return (self._fallback_title(user_message), None)

        # 构造 prompt
        if len(user_msg) < 10:
            ai_preview = (ai_response[:300] if ai_response else "")
            prompt = f"""请为以下对话生成一个简洁的标题（8-15个字）。
用户消息：{user_msg}
AI回复：{ai_preview}

直接输出标题，无需标点："""
        else:
            prompt = f"""请为以下用户提问生成一个简洁的标题（8-15个字）。
用户提问：{user_msg[:500]}

直接输出标题，无需标点："""

        try:
            logger.info(f"开始生成会话标题 - 使用模型: {model_provider}:{model_name}")
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=30,
                temperature=0.7
            )

            title = response.choices[0].message.content.strip()
            title = self._clean_title(title)
            if len(title) > 30:
                title = title[:30]

            # 提取 token 使用信息
            usage = None
            if hasattr(response, 'usage') and response.usage:
                usage = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
                logger.info(f"标题生成成功: {title}, tokens: {usage['total_tokens']}")
            else:
                logger.info(f"标题生成成功: {title} (无 token 信息)")

            return (title if title else "新对话", usage)

        except Exception as e:
            logger.error(f"AI生成标题失败: {e}")
            return (self._fallback_title(user_message), None)
