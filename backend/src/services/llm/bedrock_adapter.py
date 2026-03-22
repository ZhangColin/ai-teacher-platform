"""AWS Bedrock 适配器 (Claude)

配置要求 (从数据库读取):

方式 1 - API Key 认证（推荐，2025 新功能）:
- api_key: Bedrock API Key
- base_url: AWS Region (如 us-west-2)

方式 2 - AWS IAM 凭证:
- api_key: AWS Access Key ID
- base_url: AWS Region (如 us-west-2)
- extra_config.aws_secret_access_key: AWS Secret Access Key

支持的模型 ID 格式（Bedrock 专用）:
- us.anthropic.claude-opus-4-6-v1:0
- us.anthropic.claude-sonnet-4-6
- anthropic.claude-haiku-4-5-20251001-v1:0 (全局端点，无 us. 前缀)

参考: https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys-use.html
"""
import asyncio
import json
import logging
import os
from typing import AsyncGenerator, Dict, List, Optional, Tuple
import aiohttp

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class BedrockAdapter(BaseLLMAdapter):
    """AWS Bedrock 适配器 (Claude)

    支持 2025 新的 API Key 认证方式，也支持传统 AWS IAM 凭证
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.region = self.base_url or "us-west-2"
        self.aws_secret_key = self.extra_config.get("aws_secret_access_key")

        # 判断使用哪种认证方式
        self.use_api_key = self.api_key and not self.aws_secret_key

        # 构建 API 端点
        self.endpoint = f"https://bedrock-runtime.{self.region}.amazonaws.com"

        # 如果使用 API Key，设置环境变量供 boto3 使用
        if self.use_api_key:
            os.environ['AWS_BEARER_TOKEN_BEDROCK'] = self.api_key
            # 使用 boto3，它会自动读取 AWS_BEARER_TOKEN_BEDROCK 环境变量
            import boto3
            self.boto3_client = boto3.client(
                "bedrock-runtime",
                region_name=self.region
            )
        else:
            # 使用 IAM 凭证
            import boto3
            self.boto3_client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
                aws_access_key_id=self.api_key,
                aws_secret_access_key=self.aws_secret_key
            )

    async def _make_request(self, endpoint: str, payload: dict) -> dict:
        """使用 HTTP 请求调用 Bedrock API"""
        url = f"{self.endpoint}{endpoint}"

        # 禁用 SSL 验证（用于 AWS Bedrock）
        import ssl
        connector = aiohttp.TCPConnector(ssl=False)

        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Bedrock API 错误: {response.status} - {error_text}")
                    raise Exception(f"Bedrock API 调用失败: {response.status} - {error_text}")
                return await response.json()

    async def _make_stream_request(self, endpoint: str, payload: dict):
        """使用流式 HTTP 请求调用 Bedrock API"""
        url = f"{self.endpoint}{endpoint}"

        # 禁用 SSL 验证（用于 AWS Bedrock）
        import ssl
        connector = aiohttp.TCPConnector(ssl=False)

        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Bedrock API 错误: {response.status} - {error_text}")
                    raise Exception(f"Bedrock API 调用失败: {response.status} - {error_text}")

                async for line in response.content:
                    if line:
                        yield line

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

        # 使用 boto3 调用
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.boto3_client.converse(**request_params)
            )
            content = response["output"]["message"]["content"][0]["text"]
            usage = self._extract_usage(response, model)
            return content, usage
        except Exception as e:
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
        # 打印调试信息（用 print 确保输出）
        print(f"[Bedrock] ===== 调用模型: {model} =====")
        print(f"[Bedrock] 区域: {self.region}")
        print(f"[Bedrock] 使用 API Key: {self.use_api_key}")
        logger.info(f"[Bedrock] 调用模型: {model}")
        logger.info(f"[Bedrock] 区域: {self.region}")
        logger.info(f"[Bedrock] 使用 API Key: {self.use_api_key}")

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

        # 使用 boto3 调用
        loop = asyncio.get_event_loop()
        try:
            logger.info(f"[Bedrock] 请求参数: modelId={request_params['modelId']}")
            print(f"[Bedrock] API 端点: {self.endpoint}")
            print(f"[Bedrock] 完整请求: region={self.region}, modelId={model}")
            response = await loop.run_in_executor(
                None,
                lambda: self.boto3_client.converse_stream(**request_params)
            )

            usage_info = None

            for chunk in response["stream"]:
                if "contentBlockDelta" in chunk:
                    yield chunk["contentBlockDelta"]["delta"]["text"]
                elif "metadata" in chunk:
                    usage_info = self._extract_usage(chunk["metadata"], model)

            if usage_info:
                yield usage_info

        except Exception as e:
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
