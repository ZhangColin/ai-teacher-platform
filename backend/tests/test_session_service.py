"""SessionService 单元测试"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.session_service import SessionService
from src.models import Agent, UIConfig


class TestSessionService:
    """测试 SessionService 类"""
    
    def test_init(self):
        """测试初始化"""
        service = SessionService()
        assert service.sessions == {}
    
    def test_create_session(self):
        """测试创建会话"""
        service = SessionService()
        
        # 创建测试用的 Agent
        agent = Agent(
            agent_id="test_agent",
            name="测试 Agent",
            system_prompt="你是一个测试助手",
            ui_config=UIConfig(show_preview=False, preview_types=[])
        )
        
        # 创建会话
        session_id = service.create_session(agent)
        
        # 验证会话 ID 格式（UUID）
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # UUID 格式长度
        assert session_id.count('-') == 4  # UUID 包含 4 个连字符
        
        # 验证会话已存储
        assert session_id in service.sessions
        assert service.sessions[session_id]["agent_id"] == "test_agent"
    
    def test_create_multiple_sessions(self):
        """测试创建多个会话（每个会话 ID 应该不同）"""
        service = SessionService()
        
        agent = Agent(
            agent_id="test_agent",
            name="测试 Agent",
            system_prompt="你是一个测试助手",
            ui_config=UIConfig(show_preview=False, preview_types=[])
        )
        
        session_id1 = service.create_session(agent)
        session_id2 = service.create_session(agent)
        
        # 两个会话 ID 应该不同
        assert session_id1 != session_id2
        
        # 两个会话都应该存在
        assert session_id1 in service.sessions
        assert session_id2 in service.sessions
    
    def test_get_session_existing(self):
        """测试获取存在的会话"""
        service = SessionService()
        
        agent = Agent(
            agent_id="test_agent",
            name="测试 Agent",
            system_prompt="你是一个测试助手",
            ui_config=UIConfig(show_preview=False, preview_types=[])
        )
        
        session_id = service.create_session(agent)
        session = service.get_session(session_id)
        
        assert session is not None
        assert session["agent_id"] == "test_agent"
    
    def test_get_session_nonexistent(self):
        """测试获取不存在的会话（应该返回 None）"""
        service = SessionService()
        session = service.get_session("non-existent-session-id")
        assert session is None
    
    def test_session_exists_true(self):
        """测试检查存在的会话"""
        service = SessionService()
        
        agent = Agent(
            agent_id="test_agent",
            name="测试 Agent",
            system_prompt="你是一个测试助手",
            ui_config=UIConfig(show_preview=False, preview_types=[])
        )
        
        session_id = service.create_session(agent)
        assert service.session_exists(session_id) is True
    
    def test_session_exists_false(self):
        """测试检查不存在的会话"""
        service = SessionService()
        assert service.session_exists("non-existent-session-id") is False

