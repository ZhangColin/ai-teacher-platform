"""测试GLM图像生成服务"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.services.ai_service import AIService
import httpx


class TestGLMImageGeneration:
    """测试GLM图像生成功能"""
    
    @pytest.mark.asyncio
    async def test_generate_image_success(self):
        """测试成功生成图片"""
        service = AIService()
        
        # Mock httpx响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "task_123456",
            "request_id": "req_789",
            "model": "cogview-4",
            "task_status": "PROCESSING"
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            # 设置环境变量
            with patch.dict("os.environ", {
                "GLM_API_KEY": "sk-test-key",
                "GLM_BASE_URL": "https://open.bigmodel.cn/api/paas/v4"
            }):
                result = await service.generate_image(
                    prompt="一只可爱的猫咪",
                    model_config="glm:cogview-4",
                    size="1024x1024",
                    count=1
                )
                
                assert result is not None
                assert "id" in result or "task_id" in result.get("id", "task_123456")
    
    @pytest.mark.asyncio
    async def test_generate_image_invalid_provider(self):
        """测试不支持的服务商"""
        service = AIService()
        
        with pytest.raises(ValueError, match="图像生成仅支持GLM服务商"):
            await service.generate_image(
                prompt="测试",
                model_config="deepseek:deepseek-chat",
                size="1024x1024",
                count=1
            )
    
    @pytest.mark.asyncio
    async def test_generate_image_missing_api_key(self):
        """测试缺少API Key"""
        service = AIService()
        
        with patch.dict("os.environ", {"GLM_API_KEY": ""}, clear=False):
            with pytest.raises(ValueError, match="未配置GLM_API_KEY"):
                await service.generate_image(
                    prompt="测试",
                    model_config="glm:cogview-4",
                    size="1024x1024",
                    count=1
                )
    
    @pytest.mark.asyncio
    async def test_get_image_result_success(self):
        """测试成功查询生成结果"""
        service = AIService()
        
        # Mock httpx响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "task_id": "task_123456",
            "task_status": "SUCCESS",
            "image_result": [
                {"url": "https://example.com/image1.png"},
                {"url": "https://example.com/image2.png"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with patch.dict("os.environ", {
                "GLM_API_KEY": "sk-test-key",
                "GLM_BASE_URL": "https://open.bigmodel.cn/api/paas/v4"
            }):
                result = await service.get_image_result("task_123456")
                
                assert result is not None
                assert result["task_status"] == "SUCCESS"
    
    @pytest.mark.asyncio
    async def test_get_image_result_processing(self):
        """测试查询进行中的任务"""
        service = AIService()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "task_id": "task_123456",
            "task_status": "PROCESSING"
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with patch.dict("os.environ", {
                "GLM_API_KEY": "sk-test-key"
            }):
                result = await service.get_image_result("task_123456")
                
                assert result["task_status"] == "PROCESSING"
    
    @pytest.mark.asyncio
    async def test_get_image_result_failed(self):
        """测试查询失败的任务"""
        service = AIService()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "task_id": "task_123456",
            "task_status": "FAIL",
            "error": {
                "code": "CONTENT_VIOLATION",
                "message": "内容违规"
            }
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with patch.dict("os.environ", {
                "GLM_API_KEY": "sk-test-key"
            }):
                result = await service.get_image_result("task_123456")
                
                assert result["task_status"] == "FAIL"
                assert "error" in result


class TestGLMClientConfiguration:
    """测试GLM客户端配置"""
    
    def test_get_glm_client(self):
        """测试获取GLM客户端配置"""
        service = AIService()
        
        with patch.dict("os.environ", {
            "GLM_API_KEY": "sk-test-glm-key",
            "GLM_BASE_URL": "https://open.bigmodel.cn/api/paas/v4",
            "GLM_MODEL": "glm-4"
        }):
            client, model_name = service._get_ai_client("glm:cogview-3")
            
            # 验证模型名称
            assert model_name == "cogview-4"
    
    def test_get_glm_client_with_default_model(self):
        """测试使用默认GLM模型"""
        service = AIService()
        
        with patch.dict("os.environ", {
            "GLM_API_KEY": "sk-test-glm-key",
            "GLM_MODEL": "glm-4",
            "CURRENT_PROVIDER": "glm"  # 设置默认服务商为glm
        }):
            # 不传model_config，应该使用环境变量的默认配置
            client, model_name = service._get_ai_client(None)
            
            # 应该使用环境变量的默认模型
            assert model_name == "glm-4"
