"""Session 模型单元测试"""
import pytest
from datetime import datetime
from src.models import Session


class TestSession:
    """测试 Session 模型"""
    
    def test_session_creation(self):
        """测试创建 Session"""
        session = Session(
            session_id="test-session-id",
            user_id="test-user-id",
            tool_id="test-tool-id",
            title="测试会话"
        )
        
        assert session.session_id == "test-session-id"
        assert session.user_id == "test-user-id"
        assert session.tool_id == "test-tool-id"
        assert session.title == "测试会话"
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)
    
    def test_generate_title_short_message(self):
        """测试生成标题（短消息）"""
        session = Session(
            session_id="test",
            user_id="user",
            tool_id="tool",
            title=""
        )
        
        title = session.generate_title("这是一个短消息")
        assert title == "这是一个短消息"
    
    def test_generate_title_long_message(self):
        """测试生成标题（长消息，需要截断）"""
        session = Session(
            session_id="test",
            user_id="user",
            tool_id="tool",
            title=""
        )
        
        long_message = "这是一个非常长的消息内容，超过了默认的最大长度限制，应该被截断并添加省略号"
        title = session.generate_title(long_message, max_length=20)
        
        assert len(title) <= 23  # 20 + "..."
        assert title.endswith("...")
        assert title.startswith("这是一个非常长的消息")
    
    def test_generate_title_custom_max_length(self):
        """测试生成标题（自定义最大长度）"""
        session = Session(
            session_id="test",
            user_id="user",
            tool_id="tool",
            title=""
        )
        
        message = "这是一个非常长的测试消息内容，需要被截断"
        title = session.generate_title(message, max_length=10)
        
        assert len(title) <= 13  # 10 + "..."
        assert title.endswith("...")
    
    def test_generate_title_empty_message(self):
        """测试生成标题（空消息，使用默认标题）"""
        session = Session(
            session_id="test",
            user_id="user",
            tool_id="tool",
            title=""
        )
        
        title = session.generate_title("")
        assert title == "新对话"
    
    def test_generate_title_whitespace_only(self):
        """测试生成标题（只有空白字符）"""
        session = Session(
            session_id="test",
            user_id="user",
            tool_id="tool",
            title=""
        )
        
        title = session.generate_title("   \n\t  ")
        assert title == "新对话"
    
    def test_update_timestamp(self):
        """测试更新会话时间戳"""
        session = Session(
            session_id="test",
            user_id="user",
            tool_id="tool",
            title="测试"
        )
        
        original_updated_at = session.updated_at
        
        # 等待一小段时间确保时间戳不同
        import time
        time.sleep(0.01)
        
        session.update_timestamp()
        
        assert session.updated_at > original_updated_at

