"""Session API 接口测试"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestCreateSession:
    """测试 POST /api/v1/agents/{agent_id}/sessions 接口"""
    
    @patch('src.services.ai_service.AIService.generate_welcome_message')
    def test_create_session_success(self, mock_generate):
        """测试成功创建会话"""
        # Mock AI 服务
        mock_generate.return_value = "你好！我是你的提示词向导。请告诉我你想让 AI 帮你完成什么任务。"
        
        response = client.post("/api/v1/agents/prompt_wizard/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "welcome_message" in data
        assert "ui_config" in data
        assert "artifacts" in data
        assert isinstance(data["session_id"], str)
        assert len(data["session_id"]) > 0
        assert data["welcome_message"] == "你好！我是你的提示词向导。请告诉我你想让 AI 帮你完成什么任务。"
        assert data["ui_config"]["show_preview"] is True
        assert "markdown" in data["ui_config"]["preview_types"]
        assert isinstance(data["artifacts"], list)
    
    def test_create_session_agent_not_found(self):
        """测试使用不存在的 Agent 创建会话"""
        response = client.post("/api/v1/agents/non_existent_agent/sessions")
        
        assert response.status_code == 404
        data = response.json()
        assert "error_code" in data or "detail" in data
    
    @patch('src.services.ai_service.AIService.generate_welcome_message')
    def test_create_session_with_artifacts(self, mock_generate):
        """测试欢迎消息包含代码块时的会话创建"""
        # Mock AI 服务返回包含代码块的消息
        mock_generate.return_value = """你好！我是你的提示词向导。

```markdown
## 示例提示词
这是一个示例。
```"""
        
        response = client.post("/api/v1/agents/prompt_wizard/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["artifacts"]) > 0
        artifact = data["artifacts"][0]
        assert artifact["type"] == "markdown"
        assert artifact["language"] == "markdown"
        assert "示例提示词" in artifact["content"]
        assert "timestamp" in artifact

