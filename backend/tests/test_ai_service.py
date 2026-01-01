"""AIService 单元测试"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.ai_service import AIService


class TestAIService:
    """测试 AIService 类"""
    
    def test_init_without_api_key(self):
        """测试在没有 API Key 的情况下初始化（应该使用 Mock 模式）"""
        with patch.dict(os.environ, {}, clear=True):
            service = AIService()
            assert service.client is None
            assert service.model_name == "mock-model"
    
    def test_init_with_invalid_api_key(self):
        """测试使用无效的 API Key 初始化（应该使用 Mock 模式）"""
        with patch.dict(os.environ, {
            "CURRENT_PROVIDER": "kimi",
            "KIMI_API_KEY": "invalid-key"  # 不以 sk- 开头
        }, clear=True):
            service = AIService()
            assert service.client is None
            assert service.model_name == "mock-model"
    
    @patch('src.services.ai_service.OpenAI')
    def test_init_with_valid_api_key(self, mock_openai):
        """测试使用有效的 API Key 初始化"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        with patch.dict(os.environ, {
            "CURRENT_PROVIDER": "kimi",
            "KIMI_API_KEY": "sk-valid-key",
            "KIMI_BASE_URL": "https://api.example.com",
            "KIMI_MODEL": "moonshot-v1-8k"
        }, clear=True):
            service = AIService()
            assert service.client is not None
            assert service.model_name == "moonshot-v1-8k"
            mock_openai.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_welcome_message_mock_mode(self):
        """测试 Mock 模式下生成欢迎消息"""
        with patch.dict(os.environ, {}, clear=True):
            service = AIService()
            result = await service.generate_welcome_message("你是一个助手")
            
            assert result == "你好！我是你的 AI 助手。请告诉我你需要什么帮助。"
    
    @pytest.mark.asyncio
    @patch('src.services.ai_service.OpenAI')
    async def test_generate_welcome_message_with_client(self, mock_openai):
        """测试有客户端时生成欢迎消息"""
        # Mock OpenAI 客户端
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "你好！我是你的 AI 助手。"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.dict(os.environ, {
            "CURRENT_PROVIDER": "kimi",
            "KIMI_API_KEY": "sk-valid-key",
            "KIMI_BASE_URL": "https://api.example.com",
            "KIMI_MODEL": "moonshot-v1-8k"
        }, clear=True):
            service = AIService()
            result = await service.generate_welcome_message("你是一个助手")
            
            assert result == "你好！我是你的 AI 助手。"
            mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.ai_service.OpenAI')
    async def test_generate_welcome_message_error_handling(self, mock_openai):
        """测试生成欢迎消息时的错误处理"""
        # Mock OpenAI 客户端抛出异常
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("网络错误")
        mock_openai.return_value = mock_client
        
        with patch.dict(os.environ, {
            "CURRENT_PROVIDER": "kimi",
            "KIMI_API_KEY": "sk-valid-key",
            "KIMI_BASE_URL": "https://api.example.com",
            "KIMI_MODEL": "moonshot-v1-8k"
        }, clear=True):
            service = AIService()
            result = await service.generate_welcome_message("你是一个助手")
            
            # 应该返回错误提示消息
            assert "暂时不可用" in result or "抱歉" in result
    
    @pytest.mark.asyncio
    async def test_chat_mock_mode(self):
        """测试 Mock 模式下的对话"""
        with patch.dict(os.environ, {}, clear=True):
            service = AIService()
            result = await service.chat(
                system_prompt="你是一个助手",
                history=[],
                user_message="你好"
            )
            
            assert "Mock 回复" in result
            assert "你好" in result
    
    @pytest.mark.asyncio
    @patch('src.services.ai_service.OpenAI')
    async def test_chat_with_client(self, mock_openai):
        """测试有客户端时的对话"""
        # Mock OpenAI 客户端
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "好的，我来帮你。"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.dict(os.environ, {
            "CURRENT_PROVIDER": "kimi",
            "KIMI_API_KEY": "sk-valid-key",
            "KIMI_BASE_URL": "https://api.example.com",
            "KIMI_MODEL": "moonshot-v1-8k"
        }, clear=True):
            service = AIService()
            result = await service.chat(
                system_prompt="你是一个助手",
                history=[],
                user_message="你好"
            )
            
            assert result == "好的，我来帮你。"
            mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.ai_service.OpenAI')
    async def test_chat_with_history(self, mock_openai):
        """测试带历史消息的对话"""
        # Mock OpenAI 客户端
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "继续对话"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.dict(os.environ, {
            "CURRENT_PROVIDER": "kimi",
            "KIMI_API_KEY": "sk-valid-key",
            "KIMI_BASE_URL": "https://api.example.com",
            "KIMI_MODEL": "moonshot-v1-8k"
        }, clear=True):
            service = AIService()
            result = await service.chat(
                system_prompt="你是一个助手",
                history=[
                    {"role": "user", "content": "第一句话"},
                    {"role": "assistant", "content": "第一句回复"}
                ],
                user_message="第二句话"
            )
            
            assert result == "继续对话"
            # 验证消息链包含历史消息
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]["messages"]
            assert len(messages) == 4  # system + 2 history + current
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"
            assert messages[2]["role"] == "assistant"
            assert messages[3]["role"] == "user"
    
    @pytest.mark.asyncio
    @patch('src.services.ai_service.OpenAI')
    async def test_chat_error_handling(self, mock_openai):
        """测试对话时的错误处理"""
        # Mock OpenAI 客户端抛出异常
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("服务不可用")
        mock_openai.return_value = mock_client
        
        with patch.dict(os.environ, {
            "CURRENT_PROVIDER": "kimi",
            "KIMI_API_KEY": "sk-valid-key",
            "KIMI_BASE_URL": "https://api.example.com",
            "KIMI_MODEL": "moonshot-v1-8k"
        }, clear=True):
            service = AIService()
            result = await service.chat(
                system_prompt="你是一个助手",
                history=[],
                user_message="你好"
            )
            
            # 应该返回错误提示消息
            assert "暂时不可用" in result or "抱歉" in result

