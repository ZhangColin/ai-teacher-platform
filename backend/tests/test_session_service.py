"""SessionService 单元测试"""
import pytest
import sys
import tempfile
import os
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.session_service import SessionService
from src.models import Session, Message
from src.db_models import Base, UserModel, SessionModel, MessageModel, MessageRole
from src.services.user_service import UserService


class TestSessionService:
    """测试 SessionService 类"""
    
    @pytest.fixture
    def test_db(self):
        """创建测试数据库"""
        # 创建临时数据库文件
        test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        test_db_path = test_db_file.name
        test_db_file.close()
        
        # 创建测试数据库引擎
        test_engine = create_engine(f"sqlite:///{test_db_path}", echo=False, connect_args={"check_same_thread": False})
        Base.metadata.create_all(test_engine)
        
        # 创建测试会话
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        yield TestSessionLocal, test_db_path
        
        # 清理：删除测试数据库文件
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)
    
    @pytest.fixture
    def test_user(self, test_db):
        """创建测试用户"""
        TestSessionLocal, _ = test_db
        db = TestSessionLocal()
        
        try:
            # 创建测试用户
            user = UserModel(
                user_id="test-user-id",
                username="testuser",
                password_hash="hashed_password",
                created_at=datetime.now()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            yield user
        finally:
            db.close()
    
    def test_create_session(self, test_db, test_user):
        """测试创建会话"""
        TestSessionLocal, _ = test_db
        
        def get_db():
            db = TestSessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        service = SessionService()
        service._get_db = get_db
        
        session = service.create_session(
            user_id=test_user.user_id,
            tool_id="test_tool",
            title="测试会话"
        )
        
        assert session is not None
        assert session.user_id == test_user.user_id
        assert session.tool_id == "test_tool"
        assert session.title == "测试会话"
        assert session.session_id is not None
    
    def test_create_session_with_auto_title(self, test_db, test_user):
        """测试创建会话并自动生成标题"""
        TestSessionLocal, _ = test_db
        
        def get_db():
            db = TestSessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        service = SessionService()
        service._get_db = get_db
        
        first_message = "我想让 AI 帮我写小红书美妆文案"
        session = service.create_session(
            user_id=test_user.user_id,
            tool_id="test_tool",
            first_message=first_message
        )
        
        assert session is not None
        assert session.title == first_message[:50]  # 默认最大长度50
        assert len(session.title) <= 50
    
    def test_get_session_by_id(self, test_db, test_user):
        """测试根据ID获取会话"""
        TestSessionLocal, _ = test_db
        
        def get_db():
            db = TestSessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        service = SessionService()
        service._get_db = get_db
        
        # 先创建会话
        created_session = service.create_session(
            user_id=test_user.user_id,
            tool_id="test_tool",
            title="测试会话"
        )
        
        # 获取会话
        retrieved_session = service.get_session_by_id(created_session.session_id)
        
        assert retrieved_session is not None
        assert retrieved_session.session_id == created_session.session_id
        assert retrieved_session.title == "测试会话"
    
    def test_get_sessions_by_user_and_tool(self, test_db, test_user):
        """测试获取用户在某工具下的所有会话"""
        TestSessionLocal, _ = test_db
        
        def get_db():
            db = TestSessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        service = SessionService()
        service._get_db = get_db
        
        # 创建多个会话
        session1 = service.create_session(
            user_id=test_user.user_id,
            tool_id="test_tool",
            title="会话1"
        )
        
        session2 = service.create_session(
            user_id=test_user.user_id,
            tool_id="test_tool",
            title="会话2"
        )
        
        # 获取会话列表
        sessions = service.get_sessions_by_user_and_tool(
            user_id=test_user.user_id,
            tool_id="test_tool"
        )
        
        assert len(sessions) == 2
        session_ids = [s.session_id for s in sessions]
        assert session1.session_id in session_ids
        assert session2.session_id in session_ids
    
    def test_update_session_title(self, test_db, test_user):
        """测试更新会话标题"""
        TestSessionLocal, _ = test_db
        
        def get_db():
            db = TestSessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        service = SessionService()
        service._get_db = get_db
        
        # 创建会话
        session = service.create_session(
            user_id=test_user.user_id,
            tool_id="test_tool",
            title="原始标题"
        )
        
        # 更新标题
        updated_session = service.update_session_title(
            session_id=session.session_id,
            new_title="新标题"
        )
        
        assert updated_session is not None
        assert updated_session.title == "新标题"
        
        # 验证数据库中的标题已更新
        retrieved_session = service.get_session_by_id(session.session_id)
        assert retrieved_session.title == "新标题"
    
    def test_delete_session(self, test_db, test_user):
        """测试删除会话"""
        TestSessionLocal, _ = test_db
        
        def get_db():
            db = TestSessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        service = SessionService()
        service._get_db = get_db
        
        # 创建会话
        session = service.create_session(
            user_id=test_user.user_id,
            tool_id="test_tool",
            title="待删除的会话"
        )
        
        # 删除会话
        service.delete_session(session.session_id)
        
        # 验证会话已删除
        retrieved_session = service.get_session_by_id(session.session_id)
        assert retrieved_session is None
