"""AI 服务：调用 LLM API"""
import os
import logging
import asyncio
import httpx
import json
import base64
import uuid
from pathlib import Path
from typing import Optional, Tuple, List, Dict, AsyncGenerator
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import Session
from src.services.code_validator import CodeValidator

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

# 需要使用适配器的供应商（非 OpenAI 兼容）
ADAPTER_PROVIDERS = {'bedrock', 'claude', 'anthropic'}





class AIService:
    """AI 服务客户端"""

    def __init__(self, db: Optional[Session] = None):
        """
        初始化 AI 服务（使用默认配置）

        Args:
            db: 可选的数据库会话，如果提供则从数据库读取模型配置
        """
        self.db = db
        self._default_client = None  # 惰性缓存
        self._default_model_name = None  # 惰性缓存
        self.code_validator = CodeValidator()  # 代码完整性验证器
    
    def _get_ai_client(self, model_config: Optional[str] = None) -> Tuple[Optional[OpenAI], str]:
        """
        从数据库获取模型配置，创建 OpenAI 兼容客户端。

        不再支持环境变量回退，所有配置必须从数据库读取。

        Args:
            model_config: 模型配置字符串，格式：provider:model_name（如 "openai:gpt-4o"）
                         如果为 None，使用数据库中的默认配置

        Returns:
            (client, model_name) 元组

        Raises:
            ValueError: 配置不存在或无效
        """
        # 测试环境支持：如果没有数据库会话，允许使用环境变量
        testing = os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING")
        if not self.db and not testing:
            raise ValueError("数据库会话未提供，无法读取模型配置")

        # 测试环境回退：使用环境变量
        if not self.db and testing:
            return self._get_ai_client_from_env(model_config)

        from src.services.model_provider_service import ModelProviderService
        from src.services.encryption_service import EncryptionService
        from src.db_models import ModelProviderModel

        provider_service = ModelProviderService(self.db)
        encryption = EncryptionService()

        provider_code = None
        model_code = None

        # 解析 model_config
        if model_config and ":" in model_config:
            provider_code, model_code = model_config.split(":", 1)
            provider_code = provider_code.lower()
            logger.info(f"使用工具指定的模型配置: {provider_code}:{model_code}")
        else:
            # 使用默认供应商
            provider_info = provider_service.get_default_provider()
            if not provider_info:
                raise ValueError("未配置默认模型供应商，请先在管理后台配置")
            if not provider_info.is_enabled:
                raise ValueError(f"默认供应商 [{provider_info.provider_name}] 未启用")

            provider_code = provider_info.provider_code

            # 获取第一个启用的模型
            models = provider_service.get_all_models(
                provider_id=provider_info.id,
                include_disabled=False
            )
            if not models:
                raise ValueError(f"默认供应商 [{provider_info.provider_name}] 没有启用的模型")
            model_code = models[0].model_code
            logger.info(f"使用数据库默认配置: {provider_code}:{model_code}")

        # 从数据库获取供应商配置
        provider_info = provider_service.get_provider_by_code(provider_code)
        if not provider_info:
            raise ValueError(f"供应商 [{provider_code}] 未在数据库中配置")

        if not provider_info.is_enabled:
            raise ValueError(f"供应商 [{provider_info.provider_name}] 未启用")

        provider_model = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.id == provider_info.id
        ).first()

        if not provider_model:
            raise ValueError(f"供应商 [{provider_code}] 的配置数据不完整")

        # 解密 API Key
        try:
            api_key = encryption.decrypt(provider_model.api_key_encrypted)
        except Exception as e:
            # 检查是否是占位符
            if provider_model.api_key_encrypted == "placeholder":
                raise ValueError(f"供应商 [{provider_info.provider_name}] 的 API 密钥未配置，请在管理后台「模型供应商配置」页面配置 API 密钥")
            raise ValueError(f"解密供应商 [{provider_code}] 的 API 密钥失败: {e}")

        if not api_key or api_key == "placeholder":
            raise ValueError(f"供应商 [{provider_code}] 的 API 密钥未配置，请在管理后台「模型供应商配置」页面配置")

        base_url = provider_info.base_url
        if not base_url:
            raise ValueError(f"供应商 [{provider_code}] 的 API 地址未配置")

        # 从环境变量读取超时配置（秒），默认120秒
        timeout_seconds = float(os.getenv("AI_REQUEST_TIMEOUT", "120"))

        # 创建客户端
        logger.info(f"创建 OpenAI 客户端 - provider: {provider_code}, base_url: {base_url}, model: {model_code}")

        # 创建自定义 httpx 客户端，解决 macOS OpenSSL 3.0 兼容性问题
        import httpx

        # 针对 Kimi 和其他可能有 SSL 问题的供应商，禁用 HTTP/2
        if provider_code in ["kimi", "newapi"]:
            http_client = httpx.Client(
                verify=True,
                timeout=timeout_seconds,
                http2=False  # 禁用 HTTP/2，使用 HTTP/1.1
            )
        else:
            http_client = None  # 使用默认配置

        # newapi 供应商需要特殊处理（httpx 与 NewAPI 不兼容）
        if provider_code == "newapi":
            # 标记为使用自定义客户端，在后续调用中特殊处理
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout_seconds,
                max_retries=0,
                http_client=http_client
            )
            client._use_custom_http = True  # 标记
        else:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout_seconds,
                max_retries=2,
                http_client=http_client
            )

        logger.info(f"AI 客户端初始化成功 - provider: {provider_code}, base_url: {base_url}, model: {model_code}")
        return client, model_code

    def _init_default_client(self) -> None:
        """惰性初始化默认客户端（仅在实际需要时调用）"""
        if self._default_client is None:
            self._default_client, self._default_model_name = self._get_ai_client()

    @property
    def default_client(self) -> OpenAI:
        """获取默认 AI 客户端（惰性初始化）"""
        self._init_default_client()
        return self._default_client

    @property
    def default_model_name(self) -> str:
        """获取默认模型名称（惰性初始化）"""
        self._init_default_client()
        return self._default_model_name

    def _create_adapter(self, provider_code: str, api_key: str, base_url: str):
        """创建 LLM 适配器（用于非 OpenAI 兼容的供应商）"""
        from src.services.llm import create_adapter

        return create_adapter(
            provider_code=provider_code,
            api_key=api_key,
            base_url=base_url,
        )

    def _get_adapter(self, model_config: Optional[str] = None):
        """统一获取 LLM 适配器（新接口，所有供应商走适配器层）

        Args:
            model_config: 格式 "provider:model_name"，如 "deepseek:deepseek-chat"

        Returns:
            (adapter, model_name) 元组
        """
        from src.services.llm import create_adapter

        testing = os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING")

        if not self.db and not testing:
            raise ValueError("数据库会话未提供，无法读取模型配置")

        if not self.db and testing:
            return self._get_adapter_from_env(model_config)

        from src.services.model_provider_service import ModelProviderService
        from src.services.encryption_service import EncryptionService
        from src.db_models import ModelProviderModel

        provider_service = ModelProviderService(self.db)
        encryption = EncryptionService()

        provider_code = None
        model_code = None

        if model_config and ":" in model_config:
            provider_code, model_code = model_config.split(":", 1)
            provider_code = provider_code.lower()
        else:
            provider_info = provider_service.get_default_provider()
            if not provider_info:
                raise ValueError("未配置默认模型供应商，请先在管理后台配置")
            if not provider_info.is_enabled:
                raise ValueError(f"默认供应商 [{provider_info.provider_name}] 未启用")
            provider_code = provider_info.provider_code

            models = provider_service.get_all_models(
                provider_id=provider_info.id, include_disabled=False
            )
            if not models:
                raise ValueError(f"默认供应商 [{provider_info.provider_name}] 没有启用的模型")
            model_code = models[0].model_code

        provider_info = provider_service.get_provider_by_code(provider_code)
        if not provider_info:
            raise ValueError(f"供应商 [{provider_code}] 未在数据库中配置")
        if not provider_info.is_enabled:
            raise ValueError(f"供应商 [{provider_info.provider_name}] 未启用")

        provider_model = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.id == provider_info.id
        ).first()
        if not provider_model:
            raise ValueError(f"供应商 [{provider_code}] 的配置数据不完整")

        try:
            api_key = encryption.decrypt(provider_model.api_key_encrypted)
        except Exception as e:
            if provider_model.api_key_encrypted == "placeholder":
                raise ValueError(f"供应商 [{provider_info.provider_name}] 的 API 密钥未配置")
            raise ValueError(f"解密供应商 [{provider_code}] 的 API 密钥失败: {e}")

        if not api_key or api_key == "placeholder":
            raise ValueError(f"供应商 [{provider_code}] 的 API 密钥未配置")

        base_url = provider_info.base_url
        if not base_url:
            raise ValueError(f"供应商 [{provider_code}] 的 API 地址未配置")

        logger.info(f"创建适配器 - provider: {provider_code}, model: {model_code}")

        adapter = create_adapter(
            provider_code=provider_code,
            api_key=api_key,
            base_url=base_url,
            provider=provider_code,
        )
        return adapter, model_code

    def _get_adapter_from_env(self, model_config: Optional[str] = None):
        """从环境变量获取适配器（仅测试环境）"""
        from src.services.llm import create_adapter

        provider_code = None
        model_code = None

        if model_config and ":" in model_config:
            provider_code, model_code = model_config.split(":", 1)
            provider_code = provider_code.lower()
        else:
            provider_code = os.getenv("CURRENT_PROVIDER", "deepseek")

        env_configs = {
            "deepseek": ("DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "https://api.deepseek.com", "deepseek-chat"),
            "openai": ("OPENAI_API_KEY", "OPENAI_BASE_URL", "https://api.openai.com/v1", "gpt-4o"),
            "kimi": ("KIMI_API_KEY", "KIMI_BASE_URL", "https://api.moonshot.cn/v1", "moonshot-v1-8k"),
            "glm": ("GLM_API_KEY", "GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4", "glm-4"),
        }

        config = env_configs.get(provider_code)
        if not config:
            raise ValueError(f"测试环境不支持的供应商: {provider_code}")

        key_env, url_env, default_url, default_model = config
        api_key = os.getenv(key_env)
        if not api_key:
            raise ValueError(f"测试环境缺少 API Key: {key_env}")

        base_url = os.getenv(url_env, default_url)
        model_code = model_code or os.getenv(f"{provider_code.upper()}_MODEL", default_model)

        adapter = create_adapter(
            provider_code=provider_code,
            api_key=api_key,
            base_url=base_url,
            provider=provider_code,
        )
        return adapter, model_code

    def _get_ai_client_from_env(self, model_config: Optional[str] = None) -> Tuple[Optional[OpenAI], str]:
        """
        从环境变量获取 AI 客户端（仅用于测试）

        Args:
            model_config: 模型配置字符串，格式：provider:model_name

        Returns:
            (client, model_name) 元组

        Raises:
            ValueError: 配置不存在或无效
        """
        provider_code = None
        model_code = None

        # 解析 model_config
        if model_config and ":" in model_config:
            provider_code, model_code = model_config.split(":", 1)
            provider_code = provider_code.lower()
        else:
            # 使用默认供应商
            provider_code = os.getenv("CURRENT_PROVIDER", "deepseek")

        # 获取 API key
        api_key = None
        base_url = None

        if provider_code == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            model_code = model_code or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        elif provider_code == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            model_code = model_code or os.getenv("OPENAI_MODEL", "gpt-4o")
        elif provider_code == "kimi":
            api_key = os.getenv("KIMI_API_KEY")
            base_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
            model_code = model_code or os.getenv("KIMI_MODEL", "moonshot-v1-8k")
        elif provider_code == "glm":
            api_key = os.getenv("GLM_API_KEY")
            base_url = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
            model_code = model_code or os.getenv("GLM_MODEL", "glm-4")
        else:
            raise ValueError(f"测试环境不支持的供应商: {provider_code}")

        if not api_key:
            raise ValueError(f"测试环境缺少 API Key: {provider_code.upper()}_API_KEY")

        # 创建客户端
        if provider_code in ADAPTER_PROVIDERS:
            adapter = self._create_adapter(provider_code, api_key, base_url)
            return adapter, model_code
        else:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=120.0,
                max_retries=2,
            )
            return client, model_code

    
    async def generate_welcome_message(self, system_prompt: str, model_config: Optional[str] = None) -> str:
        """
        生成欢迎消息
        
        Args:
            system_prompt: Agent 的系统提示词
            model_config: 模型配置（格式：provider:model_name），如果为 None 使用默认配置
            
        Returns:
            AI 生成的欢迎消息
        """
        # 获取客户端和模型
        client, model_name = self._get_ai_client(model_config) if model_config else (self.default_client, self.default_model_name)
        
        # 无客户端时的模拟返回（用于本地无网调试）
        if not client:
            return "你好！我是你的 AI 助手。请告诉我你需要什么帮助。"
        
        try:
            # 记录系统提示词（用于调试）
            logger.info(f"生成欢迎消息 - 系统提示词长度: {len(system_prompt)} 字符, 使用模型: {model_name}")
            logger.debug(f"系统提示词内容: {system_prompt[:200]}...")
            
            response = client.chat.completions.create(
                model=model_name,
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
            error_type = type(e).__name__
            logger.error(f"AI 服务调用异常（生成欢迎消息）- 错误类型: {error_type}: {e}", exc_info=True)
            
            # 根据错误类型返回友好提示
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                return "⚠️ AI服务响应超时，请检查网络连接后重试。"
            else:
                return "欢迎使用 AI 助手！抱歉，当前服务暂时不可用，请稍后重试。"
    
    async def chat(self, system_prompt: str, history: List[Dict[str, str]], user_message: str, max_continue: int = 3, model_config: Optional[str] = None) -> tuple[str, Optional[dict]]:
        """进行对话（非流式），委托给适配器 + ContinuationManager"""
        from src.services.continuation_manager import ContinuationManager

        try:
            adapter, model_name = self._get_adapter(model_config)
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
            messages.append({"role": "user", "content": user_message})

            logger.info(f"对话请求 - 历史消息数: {len(history)}, 用户消息: {user_message[:50]}..., 使用模型: {model_name}")

            manager = ContinuationManager(max_continue=max_continue)
            content, usage = await manager.chat_with_continuation(
                adapter=adapter,
                messages=messages,
                model=model_name,
                system_prompt=system_prompt,
                temperature=0.7,
            )
            return content, usage
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"AI 服务调用异常（对话）- {error_type}: {e}", exc_info=True)
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                return "⚠️ AI服务响应超时，可能是网络问题，请稍后重试。", None
            elif "connection" in str(e).lower():
                return "⚠️ 无法连接到AI服务，请检查网络或API配置。", None
            else:
                return f"⚠️ AI服务调用失败: {str(e)[:100]}", None

    async def chat_stream(self, system_prompt: str, history: List[Dict[str, str]], user_message: str, max_continue: int = 3, model_config: Optional[str] = None) -> AsyncGenerator[str | dict, None]:
        """进行对话（流式输出），委托给适配器 + ContinuationManager"""
        from src.services.continuation_manager import ContinuationManager

        provider_code = 'unknown'
        model_name = 'unknown'

        try:
            adapter, model_name = self._get_adapter(model_config)
            provider_code = adapter.provider_code

            messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
            messages.append({"role": "user", "content": user_message})

            logger.info(f"流式对话请求 - 历史消息数: {len(history)}, 用户消息: {user_message[:50]}..., 使用模型: {model_name}")

            manager = ContinuationManager(max_continue=max_continue)
            usage_info = None

            async for chunk in manager.chat_stream_with_continuation(
                adapter=adapter,
                messages=messages,
                model=model_name,
                system_prompt=system_prompt,
                temperature=0.7,
            ):
                if isinstance(chunk, dict):
                    usage_info = chunk
                else:
                    yield chunk
                    await asyncio.sleep(0.001)

            if usage_info:
                try:
                    from .point_service import PointService
                    point_service = PointService(self.db)
                    points = point_service.calculate_points_from_tokens(
                        provider_code=usage_info.get('model_provider', provider_code),
                        model_code=usage_info.get('model_name', model_name),
                        prompt_tokens=usage_info.get('prompt_tokens', 0),
                        completion_tokens=usage_info.get('completion_tokens', 0)
                    )
                    usage_info['points_deducted'] = points
                except Exception as e:
                    logger.error(f"积分计算失败: {e}")
                    usage_info['points_deducted'] = 0

                yield {
                    'type': 'usage',
                    'prompt_tokens': usage_info.get('prompt_tokens', 0),
                    'completion_tokens': usage_info.get('completion_tokens', 0),
                    'total_tokens': usage_info.get('total_tokens', 0),
                    'model_provider': usage_info.get('model_provider', provider_code),
                    'model_name': usage_info.get('model_name', model_name),
                    'points_deducted': usage_info.get('points_deducted', 0),
                }
            else:
                logger.warning("流式响应中未找到 usage 信息")
                yield {
                    'type': 'usage',
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'total_tokens': 0,
                    'model_provider': provider_code,
                    'model_name': model_name,
                }

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"AI 服务调用异常（流式对话）- {error_type}: {e}", exc_info=True)

            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                error_msg = "⚠️ AI服务响应超时，可能是网络问题，请稍后重试。"
            elif "connection" in str(e).lower():
                error_msg = "⚠️ 无法连接到AI服务，请检查网络或API配置。"
            else:
                error_msg = f"⚠️ AI服务调用失败: {str(e)[:100]}"

            # 以 error 类型 dict 返回，避免错误消息混入内容流被前端拼接进正文
            yield {'type': 'error', 'error': error_msg}

            yield {
                'type': 'usage',
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0,
                'model_provider': provider_code,
                'model_name': model_name,
            }

    # ==================== 多模态生成功能 ====================

    async def generate_image(
        self,
        prompt: str,
        model_config: str,  # "glm:cogview-4"
        size: str = "1024x1024",
        count: int = 1,
        style: Optional[str] = None
    ) -> Dict[str, any]:
        """
        调用GLM图像生成API（异步）
        
        Args:
            prompt: 图片描述提示词
            model_config: 模型配置（格式：glm:model_name）
            size: 图片尺寸（如 "1024x1024", "512x512"）
            count: 生成数量（1-4）
            style: 生成风格（可选）
        
        Returns:
            {"task_id": "xxx", "request_id": "xxx"}
        
        Raises:
            ValueError: 不支持的服务商或参数错误
            Exception: API调用失败
        """
        # 解析模型配置
        if not model_config or ":" not in model_config:
            raise ValueError(f"模型配置格式错误: {model_config}")
        
        provider, model_name = model_config.split(":", 1)
        provider = provider.lower()
        
        if provider != "glm":
            raise ValueError(f"图像生成仅支持GLM服务商，当前配置: {provider}")
        
        # 获取GLM配置
        api_key = os.getenv("GLM_API_KEY")
        base_url = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        
        if not api_key:
            raise ValueError("未配置GLM_API_KEY")
        
        # 构建请求
        url = f"{base_url}/images/generations"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求体
        payload = {
            "model": model_name,
            "prompt": prompt
        }
        
        # 添加可选参数
        # 注意：GLM API可能不支持所有这些参数，我们需要通过日志观察实际支持的参数
        if size:
            payload["size"] = size
        
        # count 参数：移除 count > 1 的限制，始终传递
        if count:
            payload["n"] = count  # DALL-E风格的参数名
        
        if style:
            payload["style"] = style
        
        try:
            print("\n" + "-"*50)
            print("【调用GLM API】")
            print(f"模型: {model_name}")
            print(f"提示词: {prompt[:100]}...")
            print(f"参数 - size: {size}, count: {count}, style: {style}")
            print(f"完整payload: {payload}")
            print("-"*50 + "\n")
            
            logger.info(f"调用GLM图像生成API - 模型: {model_name}, payload: {payload}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:  # 延长超时到60秒，因为图片生成需要时间
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                print("\n" + "~"*50)
                print("【GLM API 返回结果】")
                print(f"状态码: {response.status_code}")
                print(f"返回数据: {result}")
                print(f"data字段存在: {'data' in result}")
                if "data" in result:
                    print(f"data内容: {result['data']}")
                    print(f"图片数量: {len(result.get('data', []))}")
                print("~"*50 + "\n")
                
                logger.info(f"GLM图像生成API调用成功，完整返回: {result}")
                
                # 检查GLM是否直接返回了图片（同步模式）
                if "data" in result:
                    # 同步模式：{"data": [{"url": "..."}, ...]}
                    print(f"✓ GLM同步模式，返回了 {len(result['data'])} 张图片")
                    logger.info("GLM返回了同步结果（直接包含图片）")
                    return {
                        "mode": "sync",
                        "data": result["data"]
                    }
                else:
                    # 异步模式：{"id": "task_xxx", ...}
                    print(f"✓ GLM异步模式，任务ID: {result.get('id')}")
                    logger.info(f"GLM返回了异步任务ID: {result}")
                    return {
                        "mode": "async",
                        "result": result
                    }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"GLM API返回错误: {e.response.status_code} - {e.response.text}")
            raise Exception(f"图像生成失败: {e.response.text}")
        except httpx.TimeoutException:
            logger.error("GLM API请求超时")
            raise Exception("图像生成请求超时，请稍后重试")
        except Exception as e:
            logger.error(f"GLM图像生成异常: {e}", exc_info=True)
            raise
    
    async def get_image_result(self, task_id: str) -> Dict[str, any]:
        """
        查询GLM图像生成结果
        
        Args:
            task_id: 任务ID
        
        Returns:
            {
                "status": "completed" | "processing" | "failed",
                "data": [{"url": "https://..."}, ...],
                "metadata": {...}
            }
        
        Raises:
            Exception: API调用失败
        """
        api_key = os.getenv("GLM_API_KEY")
        base_url = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        
        if not api_key:
            raise ValueError("未配置GLM_API_KEY")
        
        # 构建请求
        url = f"{base_url}/async-result/{task_id}"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"查询任务状态: {task_id} - {result.get('task_status')} - 完整结果: {result}")
                
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"GLM查询结果失败: {e.response.status_code} - {e.response.text}")
            raise Exception(f"查询生成结果失败: {e.response.text}")
        except Exception as e:
            logger.error(f"查询GLM任务状态异常: {e}", exc_info=True)
            raise
    
    async def generate_audio(
        self,
        prompt: str,
        model_config: str,
        voice: str = None,
        **kwargs
    ) -> Dict[str, any]:
        """
        生成音频（文本转语音）
        
        Args:
            prompt: 要转换为语音的文本
            model_config: 模型配置（格式：provider:model_name）
            voice: 音色ID（可选）
            **kwargs: 其他参数
        
        Returns:
            {
                "mode": "sync",
                "data": [{"url": "https://..."}, ...],
                "metadata": {...}
            }
        
        Raises:
            Exception: API调用失败
        """
        # 解析模型配置
        if not model_config or ":" not in model_config:
            raise ValueError(f"模型配置格式错误: {model_config}")
        
        provider, model_name = model_config.split(":", 1)
        provider = provider.lower()
        
        if provider != "glm":
            raise ValueError(f"音频生成仅支持GLM服务商，当前配置: {provider}")
        
        # 获取GLM配置
        api_key = os.getenv("GLM_API_KEY")
        base_url = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        
        if not api_key:
            raise ValueError("未配置GLM_API_KEY")
        
        # GLM-TTS需要使用glm-4-voice模型通过chat/completions调用
        # 将glm-tts映射到glm-4-voice
        if model_name == "glm-tts":
            model_name = "glm-4-voice"
        
        # 构建请求 - 使用chat/completions端点
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求体 - GLM-4-Voice的content必须是列表格式
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "stream": False  # 同步调用
        }
        
        try:
            print("\n" + "-"*50)
            print("【调用GLM TTS API】")
            print(f"模型: {model_name}")
            print(f"文本: {prompt[:100]}...")
            print(f"音色: {voice}")
            print(f"完整payload: {payload}")
            print("-"*50 + "\n")
            
            logger.info(f"调用GLM音频生成API - 模型: {model_name}, payload: {payload}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                print("\n" + "~"*50)
                print("【GLM TTS API 返回结果】")
                print(f"状态码: {response.status_code}")
                print(f"返回数据: {result}")
                print("~"*50 + "\n")
                
                logger.info(f"GLM音频生成API调用成功，完整返回: {result}")
                
                # GLM-4-Voice 通过chat/completions返回
                # 返回格式示例: {"choices": [{"message": {"content": "...", "audio": {...}}}]}
                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0].get("message", {})
                    
                    # 检查是否有音频数据
                    audio_data = message.get("audio")
                    if audio_data and isinstance(audio_data, dict):
                        # 检查是否是URL
                        audio_url = audio_data.get("url")
                        if audio_url:
                            return {
                                "mode": "sync",
                                "data": [{"url": audio_url}]
                            }
                        
                        # 检查是否是base64编码的音频
                        audio_base64 = audio_data.get("data") or audio_data.get("audio")
                        if audio_base64:
                            print(f"检测到base64音频数据，长度: {len(audio_base64)}")
                            
                            # 保存base64音频到文件
                            audio_url = await self._save_base64_audio(audio_base64, audio_data.get("format", "mp3"))
                            
                            return {
                                "mode": "sync",
                                "data": [{"url": audio_url}]
                            }
                    
                    # 如果没有audio字段，可能音频在content中
                    content = message.get("content", "")
                    if content:
                        # TODO: 处理content中可能包含的音频信息
                        logger.warning(f"GLM返回了文本内容而非音频: {content}")
                
                # 尝试其他可能的格式
                if "data" in result:
                    data_obj = result["data"]
                    if isinstance(data_obj, dict):
                        audio_url = data_obj.get("url")
                        if audio_url:
                            return {
                                "mode": "sync",
                                "data": [{"url": audio_url}]
                            }
                
                # 如果都不匹配，抛出异常
                raise Exception(f"无法从GLM响应中提取音频数据，返回格式: {result}")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"GLM API返回错误: {e.response.status_code} - {e.response.text}")
            raise Exception(f"音频生成失败: {e.response.text}")
        except httpx.TimeoutException:
            logger.error("GLM API请求超时")
            raise Exception("音频生成请求超时，请稍后重试")
        except Exception as e:
            logger.error(f"GLM音频生成异常: {e}", exc_info=True)
            raise
    
    async def _save_base64_audio(self, base64_data: str, audio_format: str = "mp3") -> str:
        """
        保存base64编码的音频到本地文件
        
        Args:
            base64_data: base64编码的音频数据
            audio_format: 音频格式（mp3, wav等）
        
        Returns:
            可访问的音频URL路径
        """
        try:
            # 创建static/media/audio目录（与HTML上传统一到static目录）
            static_dir = Path(__file__).parent.parent.parent / "static"
            media_dir = static_dir / "media" / "audio"
            media_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成唯一文件名
            file_name = f"{uuid.uuid4()}.{audio_format}"
            file_path = media_dir / file_name
            
            # 解码base64并保存
            audio_bytes = base64.b64decode(base64_data)
            with open(file_path, "wb") as f:
                f.write(audio_bytes)
            
            # 返回可访问的URL（通过/static路径访问）
            audio_url = f"/static/media/audio/{file_name}"
            
            logger.info(f"Base64音频已保存: {file_path}, URL: {audio_url}")
            print(f"✓ Base64音频已保存到: {file_path}")
            print(f"✓ 访问URL: {audio_url}")
            
            return audio_url
            
        except Exception as e:
            logger.error(f"保存base64音频失败: {e}", exc_info=True)
            raise Exception(f"保存音频文件失败: {str(e)}")
    
    async def generate_video(
        self,
        prompt: str,
        model_config: str,
        size: str = None,
        fps: int = None,
        quality: str = None,
        with_audio: bool = False,
        **kwargs
    ) -> Dict[str, any]:
        """
        生成视频（文本转视频）
        
        Args:
            prompt: 视频描述文本
            model_config: 模型配置（格式：provider:model_name）
            size: 视频分辨率（如：1920x1080）
            fps: 帧率（30或60）
            quality: 质量模式（quality或speed）
            with_audio: 是否生成AI音效
            **kwargs: 其他参数
        
        Returns:
            {
                "mode": "async",
                "result": {"id": "task_xxx", ...}
            }
        
        Raises:
            Exception: API调用失败
        """
        # 解析模型配置
        if not model_config or ":" not in model_config:
            raise ValueError(f"模型配置格式错误: {model_config}")
        
        provider, model_name = model_config.split(":", 1)
        provider = provider.lower()
        
        if provider != "glm":
            raise ValueError(f"视频生成仅支持GLM服务商，当前配置: {provider}")
        
        # 获取GLM配置
        api_key = os.getenv("GLM_API_KEY")
        base_url = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        
        if not api_key:
            raise ValueError("未配置GLM_API_KEY")
        
        # 构建请求
        url = f"{base_url}/videos/generations"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求体
        payload = {
            "model": model_name,
            "prompt": prompt
        }
        
        # 添加可选参数
        if size:
            payload["size"] = size
        if fps:
            payload["fps"] = fps
        if quality:
            payload["quality"] = quality
        if with_audio:
            payload["with_audio"] = with_audio
        
        try:
            print("\n" + "-"*50)
            print("【调用GLM Video API】")
            print(f"模型: {model_name}")
            print(f"提示词: {prompt[:100]}...")
            print(f"参数 - size: {size}, fps: {fps}, quality: {quality}, with_audio: {with_audio}")
            print(f"完整payload: {payload}")
            print("-"*50 + "\n")
            
            logger.info(f"调用GLM视频生成API - 模型: {model_name}, payload: {payload}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                print("\n" + "~"*50)
                print("【GLM Video API 返回结果】")
                print(f"状态码: {response.status_code}")
                print(f"返回数据: {result}")
                print("~"*50 + "\n")
                
                logger.info(f"GLM视频生成API调用成功，完整返回: {result}")
                
                # CogVideoX 返回异步任务ID
                return {
                    "mode": "async",
                    "result": result
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"GLM API返回错误: {e.response.status_code} - {e.response.text}")
            raise Exception(f"视频生成失败: {e.response.text}")
        except httpx.TimeoutException:
            logger.error("GLM API请求超时")
            raise Exception("视频生成请求超时，请稍后重试")
        except Exception as e:
            logger.error(f"GLM视频生成异常: {e}", exc_info=True)
            raise
    
    async def get_video_result(self, task_id: str) -> Dict[str, any]:
        """
        查询GLM视频生成结果（与图片查询相同的接口）
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务状态和结果
        
        Raises:
            Exception: API调用失败
        """
        # 视频查询使用与图片相同的异步结果查询接口
        return await self.get_image_result(task_id)

