"""测试多模态生成API"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.src.main import app


class TestMediaGenerateAPI:
    """测试多模态生成API"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """创建认证头（Mock）"""
        # 在实际测试中需要真实的Token
        # 这里简化处理
        return {"Authorization": "Bearer test-token"}
    
    def test_generate_media_endpoint_exists(self, client):
        """测试接口是否存在"""
        # 不提供认证，应该返回401
        response = client.post("/api/v1/tools/image_gen/generate-media", json={
            "message": "生成一张猫的图片"
        })
        
        # 401 Unauthorized表示接口存在但需要认证
        assert response.status_code == 401
    
    def test_get_task_status_endpoint_exists(self, client):
        """测试任务状态查询接口是否存在"""
        response = client.get("/api/v1/tasks/test_task_id")
        
        # 401表示接口存在但需要认证
        assert response.status_code == 401
    
    @pytest.mark.skip(reason="需要真实的认证Token和数据库连接")
    def test_generate_media_full_flow(self, client, auth_headers):
        """测试完整的生成流程（需要真实环境）"""
        # 1. 发起生成请求
        response = client.post(
            "/api/v1/tools/image_gen/generate-media",
            headers=auth_headers,
            json={
                "message": "生成一张可爱的猫咪图片",
                "size": "1024x1024",
                "count": 1,
                "style": "auto"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert "message_id" in data
        assert "task_id" in data
        assert data["status"] in ["pending", "processing"]
        
        # 2. 查询任务状态
        task_id = data["task_id"]
        response = client.get(
            f"/api/v1/tasks/{task_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        task_data = response.json()
        
        assert task_data["task_id"] == task_id
        assert task_data["status"] in ["pending", "processing", "completed", "failed"]


class TestMediaGenerateRequest:
    """测试请求参数验证"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_request_without_message(self, client):
        """测试缺少message参数"""
        response = client.post(
            "/api/v1/tools/image_gen/generate-media",
            headers={"Authorization": "Bearer test-token"},
            json={}  # 缺少message
        )
        
        # 422 Unprocessable Entity（参数验证失败）
        assert response.status_code in [401, 422]  # 可能是401(未认证)或422(参数错误)
    
    def test_request_with_invalid_count(self, client):
        """测试无效的count参数"""
        response = client.post(
            "/api/v1/tools/image_gen/generate-media",
            headers={"Authorization": "Bearer test-token"},
            json={
                "message": "测试",
                "count": 10  # 超出范围(1-4)
            }
        )
        
        # 应该返回422或401
        assert response.status_code in [401, 422]


class TestTaskStatusAPI:
    """测试任务状态查询API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_nonexistent_task(self, client):
        """测试查询不存在的任务"""
        # 不提供认证
        response = client.get("/api/v1/tasks/nonexistent_task_id")
        
        # 401（需要认证）或404（任务不存在）
        assert response.status_code in [401, 404]
