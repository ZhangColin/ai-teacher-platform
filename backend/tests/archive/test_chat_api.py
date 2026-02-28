"""Chat API 接口测试"""
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


class TestChat:
    """测试 POST /api/v1/sessions/{session_id}/chat 接口"""
    
    def setup_method(self):
        """设置测试夹具"""
        # 先创建一个会话
        response = client.post("/api/v1/agents/prompt_wizard/sessions")
        assert response.status_code == 200
        self.session_id = response.json()["session_id"]
    
    @patch('src.services.ai_service.AIService.chat')
    def test_chat_success(self, mock_chat):
        """测试成功的对话交互"""
        # Mock AI 服务
        mock_chat.return_value = "好的，我来帮你打造一个专业的小红书美妆文案提示词。"
        
        response = client.post(
            f"/api/v1/sessions/{self.session_id}/chat",
            json={
                "message": "我想让 AI 帮我写小红书美妆文案",
                "history": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "artifacts" in data
        assert data["reply"] == "好的，我来帮你打造一个专业的小红书美妆文案提示词。"
        assert isinstance(data["artifacts"], list)
    
    @patch('src.services.ai_service.AIService.chat')
    def test_chat_with_history(self, mock_chat):
        """测试带历史消息的对话"""
        mock_chat.return_value = "继续我们的对话..."
        
        response = client.post(
            f"/api/v1/sessions/{self.session_id}/chat",
            json={
                "message": "继续",
                "history": [
                    {"role": "assistant", "content": "你好！"},
                    {"role": "user", "content": "我想写文案"}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
    
    @patch('src.services.ai_service.AIService.chat')
    def test_chat_with_artifacts(self, mock_chat):
        """测试包含代码块（成果物）的对话回复"""
        mock_chat.return_value = """好的，这是你的提示词：

```markdown
## [角色设定]
你是一位拥有5年经验的小红书美妆文案专家...
```"""
        
        response = client.post(
            f"/api/v1/sessions/{self.session_id}/chat",
            json={
                "message": "生成提示词",
                "history": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["artifacts"]) > 0
        artifact = data["artifacts"][0]
        assert artifact["type"] == "markdown"
        assert artifact["language"] == "markdown"
        assert "角色设定" in artifact["content"]
    
    def test_chat_session_not_found(self):
        """测试使用不存在的会话进行对话"""
        response = client.post(
            "/api/v1/sessions/non-existent-session/chat",
            json={
                "message": "测试",
                "history": []
            }
        )
        
        assert response.status_code == 404
    
    def test_chat_empty_message(self):
        """测试空消息的对话（应该验证失败）"""
        response = client.post(
            f"/api/v1/sessions/{self.session_id}/chat",
            json={
                "message": "",
                "history": []
            }
        )
        
        # Should fail validation (422 or 400)
        assert response.status_code in [400, 422]

