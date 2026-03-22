"""AWS Bedrock 适配器 (Claude)

配置要求 (从数据库读取):
- api_key: AWS Access Key ID
- base_url: AWS Region (如 us-east-1)
- extra_config.aws_secret_access_key: AWS Secret Access Key
"""
import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class BedrockAdapter(BaseLLMAdapter):
    """AWS Bedrock 适配器 (Claude)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.region = self.base_url or "us-east-1"
        self.aws_secret_key = self.extra_config.get("aws_secret_access_key")

        self.client = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            aws_access_key_id=self.api_key,
            aws_secret_access_key=self.aws_secret_key
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Tuple[str, Optional[Dict]]:
        # 转换消息格式
        bedrock_messages = self._to_bedrock_format(messages)

        # 构建请求参数
        request_params = {
            "modelId": model,
            "messages": bedrock_messages,
            "inferenceConfig": {
                "temperature": temperature,
                "maxTokens": kwargs.get("max_tokens", 4096),
            }
        }

        if system_prompt:
            request_params["system"] = [{"text": system_prompt}]

        # 在线程池中执行同步调用
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.converse(**request_params)
            )

            content = response["output"]["message"]["content"][0]["text"]
            usage = self._extract_usage(response, model)
            return content, usage

        except ClientError as e:
            logger.error(f"Bedrock API 调用失败: {e}")
            raise

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str | Dict, None]:
        bedrock_messages = self._to_bedrock_format(messages)

        request_params = {
            "modelId": model,
            "messages": bedrock_messages,
            "inferenceConfig": {
                "temperature": temperature,
                "maxTokens": kwargs.get("max_tokens", 4096),
            }
        }

        if system_prompt:
            request_params["system"] = [{"text": system_prompt}]

        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.converse_stream(**request_params)
            )

            usage_info = None

            for chunk in response["stream"]:
                if "contentBlockDelta" in chunk:
                    yield chunk["contentBlockDelta"]["delta"]["text"]
                elif "metadata" in chunk:
                    usage_info = self._extract_usage(chunk["metadata"], model)

            if usage_info:
                yield usage_info

        except ClientError as e:
            logger.error(f"Bedrock 流式 API 调用失败: {e}")
            raise

    def _to_bedrock_format(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """转换为 Bedrock 消息格式"""
        bedrock_messages = []
        for msg in messages:
            role = msg["role"]
            if role == "system":
                continue  # Bedrock 使用 system 字段，不在 messages 中
            bedrock_role = "user" if role == "user" else "assistant"
            bedrock_messages.append({
                "role": bedrock_role,
                "content": [{"text": msg["content"]}]
            })
        return bedrock_messages

    def _extract_usage(self, response, model: str) -> Dict:
        if isinstance(response, dict) and "usage" in response:
            usage = response["usage"]
            return {
                'prompt_tokens': usage.get("inputTokens", 0),
                'completion_tokens': usage.get("outputTokens", 0),
                'total_tokens': usage.get("totalTokens", 0),
                'model_provider': 'bedrock',
                'model_name': model
            }
        return super()._extract_usage(response, model, 'bedrock')
