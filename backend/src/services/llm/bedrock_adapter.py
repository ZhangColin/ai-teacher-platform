"""AWS Bedrock 适配器 (Claude)

通过代理服务器调用 AWS Bedrock API

配置要求 (从数据库读取):
- api_key: AWS Bedrock API Key (Bearer Token)
- base_url: 代理服务器地址 (如 https://proxy.aieducenter.com)

请求格式:
- URL: {base_url}/aws/model/{model_id}/converse
- Header: Authorization: Bearer {api_key}
- Body: AWS Bedrock converse API 格式

支持的模型 ID 格式:
- global.anthropic.claude-sonnet-4-6
- global.anthropic.claude-opus-4-6
- anthropic.claude-haiku-4-5-20251001-v1:0

参考: https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys-use.html
"""
import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple
import aiohttp

from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class BedrockAdapter(BaseLLMAdapter):
    """AWS Bedrock 适配器 (Claude)

    通过代理服务器使用 HTTP 调用 AWS Bedrock Converse API
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # base_url 是代理服务器地址
        # 可能是 https://proxy.aieducenter.com 或 https://proxy.aieducenter.com/aws
        self.proxy_base_url = self.base_url.rstrip('/') if self.base_url else None

        if not self.proxy_base_url:
            raise ValueError("base_url 未配置，请设置代理服务器地址")

        # 检查 base_url 是否已经包含 /aws，避免重复
        self.has_aws_prefix = self.proxy_base_url.endswith('/aws')

        # 请求超时时间（秒）
        self.timeout = kwargs.get("timeout", 120)

    @property
    def provider_code(self) -> str:
        return 'bedrock'

    def _get_endpoint(self, model: str, stream: bool = False) -> str:
        """构建请求端点

        Args:
            model: 模型 ID，如 global.anthropic.claude-sonnet-4-6
            stream: 是否使用流式端点

        Returns:
            完整的请求 URL
        """
        # AWS Bedrock 流式端点是 converse-stream（连字符），不是 converse_stream
        endpoint = "converse-stream" if stream else "converse"

        # 如果 base_url 已经包含 /aws，不再添加
        if self.has_aws_prefix:
            return f"{self.proxy_base_url}/model/{model}/{endpoint}"
        else:
            return f"{self.proxy_base_url}/aws/model/{model}/{endpoint}"

    def _get_headers(self) -> Dict[str, str]:
        """构建请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept-Encoding": "identity"  # 禁用压缩，避免解码问题
        }

    def _to_bedrock_format(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """转换为 Bedrock 消息格式

        Bedrock converse API 格式:
        [
            {"role": "user", "content": [{"text": "..."}]},
            {"role": "assistant", "content": [{"text": "..."}]}
        ]
        """
        bedrock_messages = []
        for msg in messages:
            role = msg["role"]
            # system 角色单独处理，不在 messages 中
            if role == "system":
                continue
            bedrock_role = "user" if role == "user" else "assistant"
            bedrock_messages.append({
                "role": bedrock_role,
                "content": [{"text": msg["content"]}]
            })
        return bedrock_messages

    def _extract_usage(self, response: Dict, model: str) -> Dict:
        """从响应中提取 token 使用信息

        Bedrock usage 格式:
        {
            "inputTokens": 100,
            "outputTokens": 50,
            "totalTokens": 150
        }
        """
        if "usage" in response:
            usage = response["usage"]
            return {
                'prompt_tokens': usage.get("inputTokens", 0),
                'completion_tokens': usage.get("outputTokens", 0),
                'total_tokens': usage.get("totalTokens", 0),
                'model_provider': 'bedrock',
                'model_name': model
            }
        return super()._extract_usage(response, model, 'bedrock')

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Tuple[str, Optional[Dict]]:
        """非流式对话

        Args:
            messages: 消息列表
            model: 模型 ID
            system_prompt: 系统提示词
            temperature: 温度参数
            **kwargs: 额外参数 (max_tokens 等)

        Returns:
            (response_content, usage_info)
        """
        # 转换消息格式
        bedrock_messages = self._to_bedrock_format(messages)

        # 构建请求体
        payload = {
            "messages": bedrock_messages,
            "inferenceConfig": {
                "temperature": temperature,
                "maxTokens": kwargs.get("max_tokens", 4096),
            }
        }

        # 添加系统提示词
        if system_prompt:
            payload["system"] = [{"text": system_prompt}]

        # 构建请求
        url = self._get_endpoint(model, stream=False)
        headers = self._get_headers()

        logger.info(f"[Bedrock] 非流式调用: {url}")
        logger.debug(f"[Bedrock] 请求体: {json.dumps(payload, ensure_ascii=False)[:500]}")

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"[Bedrock] API 错误: {response.status} - {error_text}")
                        raise Exception(f"Bedrock API 调用失败: HTTP {response.status} - {error_text}")

                    result = await response.json()

                    # 提取响应内容
                    # Bedrock 响应格式: {"output": {"message": {"content": [{"text": "..."}]}}}
                    content = result["output"]["message"]["content"][0]["text"]
                    finish_reason = result.get("stopReason", "stop")
                    if finish_reason == "max_tokens":
                        finish_reason = "length"
                    usage = self._extract_usage(result, model)
                    usage['finish_reason'] = finish_reason
                    usage['type'] = 'usage'

                    logger.info(f"[Bedrock] 响应成功，内容长度: {len(content)}, tokens: {usage['total_tokens']}")
                    return content, usage

        except aiohttp.ClientError as e:
            logger.error(f"[Bedrock] 网络错误: {e}")
            raise Exception(f"Bedrock 网络请求失败: {e}")
        except Exception as e:
            logger.error(f"[Bedrock] 调用异常: {e}", exc_info=True)
            raise

    def _parse_eventstream_headers(self, data: bytes) -> Dict[str, str]:
        """解析 EventStream 头部 (简化版本)

        AWS EventStream headers 包含纯文本标记，如：
        :event-type\x00\x11contentBlockDelta
        :content-type\x00\x10application/json
        """
        headers = {}
        text = data.decode('utf-8', errors='ignore')

        # 查找所有 :key:value 格式的标记
        import re
        pattern = r':([a-zA-Z\-]+)\x00(.)'
        for match in re.finditer(pattern, text):
            key = match.group(1)
            value_type = match.group(2)
            # 实际值在标记后面，但这里我们只需要 key
            headers[key] = value_type
            logger.info(f"[Bedrock] Header: {key} (type={value_type})")

        # 尝试更精确的解析：找到 event-type 的值
        event_type_match = re.search(r':event-type\x00(.)\x00([^\x00:]+)', text)
        if event_type_match:
            event_type = event_type_match.group(2)
            headers['event-type'] = event_type
            logger.info(f"[Bedrock] 解析到 event-type: {event_type}")

        return headers

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str | Dict, None]:
        """流式对话

        Args:
            messages: 消息列表
            model: 模型 ID
            system_prompt: 系统提示词
            temperature: 温度参数
            **kwargs: 额外参数

        Yields:
            内容片段 (str)
            最后一次 yield usage_info (Dict)
        """
        # 转换消息格式
        bedrock_messages = self._to_bedrock_format(messages)

        # 构建请求体
        payload = {
            "messages": bedrock_messages,
            "inferenceConfig": {
                "temperature": temperature,
                "maxTokens": kwargs.get("max_tokens", 4096),
            }
        }

        # 添加系统提示词
        if system_prompt:
            payload["system"] = [{"text": system_prompt}]

        # 构建请求
        url = self._get_endpoint(model, stream=True)
        headers = self._get_headers()

        logger.info(f"[Bedrock] === 流式调用开始 ===")
        logger.debug(f"[Bedrock] URL: {url}")

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    logger.info(f"[Bedrock] 响应状态: {response.status}")

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"[Bedrock] 流式 API 错误: {response.status} - {error_text}")
                        yield f"⚠️ Bedrock API 调用失败: HTTP {response.status}"
                        return

                    # 解析 Amazon EventStream 二进制格式
                    # 使用简化方法：查找纯文本标记和 JSON body
                    usage_info = None
                    buffer = b""
                    event_count = 0

                    async for data in response.content.iter_any():
                        if not data:
                            continue
                        buffer += data

                        # 将 buffer 转换为文本查找事件类型标记
                        buffer_text = buffer.decode('utf-8', errors='ignore')

                        # 循环处理 buffer 中的所有事件
                        while True:
                            # 查找 event-type 标记
                            if 'contentBlockDelta' in buffer_text:
                                event_type = 'contentBlockDelta'
                            elif 'messageStart' in buffer_text:
                                event_type = 'messageStart'
                            elif 'messageStop' in buffer_text:
                                event_type = 'messageStop'
                            elif 'contentBlockStop' in buffer_text:
                                event_type = 'contentBlockStop'
                            elif 'metadata' in buffer_text:
                                event_type = 'metadata'
                            else:
                                # 没有更多事件，跳出内层循环等待新数据
                                break

                            logger.debug(f"[Bedrock] 检测到事件类型: {event_type}, buffer 长度: {len(buffer_text)}")

                            # 查找 JSON body (在 { 之后)
                            json_start = buffer_text.find('{"')
                            if json_start == -1:
                                json_start = buffer_text.find('{"')
                            if json_start == -1:
                                logger.info(f"[Bedrock] 未找到 JSON，buffer 前150字符: {buffer_text[:150]}")
                                break

                            # 尝试找到完整的 JSON 对象
                            json_end = json_start
                            brace_count = 0
                            in_string = False
                            escape_next = False

                            for i, char in enumerate(buffer_text[json_start:], json_start):
                                if escape_next:
                                    escape_next = False
                                    continue
                                if char == '\\':
                                    escape_next = True
                                    continue
                                if char == '"' and not escape_next:
                                    in_string = not in_string
                                if not in_string:
                                    if char == '{':
                                        brace_count += 1
                                    elif char == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            json_end = i + 1
                                            break

                            if json_end <= json_start or json_end >= len(buffer_text):
                                # JSON 不完整，跳出内层循环等待更多数据
                                break

                            # 解析 JSON
                            json_str = buffer_text[json_start:json_end]
                            try:
                                body_json = json.loads(json_str)
                                logger.debug(f"[Bedrock] 解析到 JSON: {list(body_json.keys())}, 事件类型: {event_type}")

                                # 处理 contentBlockDelta 事件
                                if event_type == 'contentBlockDelta':
                                    delta = body_json.get('delta', {})
                                    if 'text' in delta:
                                        text = delta['text']
                                        logger.debug(f"[Bedrock] 文本: {text[:30]}...")
                                        yield text

                                # 处理 metadata 事件
                                elif event_type == 'metadata':
                                    if 'usage' in body_json:
                                        usage_info = self._extract_usage(body_json['usage'], model)
                                        logger.debug(f"[Bedrock] usage: {usage_info}")

                                # 清理已处理的数据
                                prefix_bytes = buffer_text[:json_end].encode('utf-8')
                                buffer = buffer[len(prefix_bytes):]
                                event_count += 1

                                # 重新计算 buffer_text，继续处理下一个事件
                                buffer_text = buffer.decode('utf-8', errors='ignore')

                            except json.JSONDecodeError as e:
                                logger.debug(f"[Bedrock] JSON 解析失败: {e}")
                                break
                            json_str = buffer_text[json_start:json_end]
                            try:
                                body_json = json.loads(json_str)
                                logger.debug(f"[Bedrock] 解析到 JSON: {list(body_json.keys())}, 事件类型: {event_type}")

                                # 处理 contentBlockDelta 事件
                                if event_type == 'contentBlockDelta':
                                    delta = body_json.get('delta', {})
                                    if 'text' in delta:
                                        text = delta['text']
                                        logger.debug(f"[Bedrock] 文本: {text[:30]}...")
                                        yield text

                                # 处理 metadata 事件
                                elif event_type == 'metadata':
                                    if 'usage' in body_json:
                                        usage_info = self._extract_usage(body_json['usage'], model)
                                        logger.debug(f"[Bedrock] usage: {usage_info}")

                                # 清理已处理的数据
                                # 重要：json_end 是字符串索引，需要找到对应的字节位置
                                # 方法：将 buffer[:json_end] 解码，然后取其字节长度
                                prefix_bytes = buffer_text[:json_end].encode('utf-8')
                                buffer = buffer[len(prefix_bytes):]
                                event_count += 1

                            except json.JSONDecodeError as e:
                                logger.debug(f"[Bedrock] JSON 解析失败: {e}")
                                # 等待更多数据
                                pass

                    logger.info(f"[Bedrock] 流式结束，共 {event_count} 个事件")

                    # 最后 yield usage 信息
                    if usage_info:
                        usage_info['type'] = 'usage'
                        usage_info['finish_reason'] = usage_info.get('finish_reason', 'stop')
                        logger.info(f"[Bedrock] 流式完成，tokens: {usage_info['total_tokens']}")
                        yield usage_info
                    else:
                        yield self._build_usage(model, finish_reason='stop')

        except aiohttp.ClientError as e:
            logger.error(f"[Bedrock] 流式网络错误: {e}")
            yield f"⚠️ Bedrock 网络请求失败: {e}"
        except Exception as e:
            logger.error(f"[Bedrock] 流式调用异常: {e}", exc_info=True)
            yield f"⚠️ Bedrock 调用异常: {e}"
            raise  # 重新抛出异常，让 ai_service.py 的异常处理捕获
