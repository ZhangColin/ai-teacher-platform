# -*- coding: utf-8 -*-
"""
会话路由集成测试
"""
import pytest
import sys
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.main import app
from src.database import get_db, Base
from src.db_models import UserModel
import bcrypt

# 全局变量，用于存储测试数据库路径
_test_db_paths = []


def override_get_db():
    """覆盖get_db依赖，使用测试数据库"""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# 覆盖app的get_db依赖
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """每个测试前自动设置测试数据库"""
    test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db_path = test_db_file.name
    test_db_file.close()
    _test_db_paths.append(test_db_path)

    # 创建测试数据库引擎
    test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    global TestSessionLocal
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # 创建表
    Base.metadata.create_all(bind=test_engine)

    yield

    # 清理
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)


@pytest.fixture(scope="function")
def client(setup_test_db):
    """创建测试客户端"""
    yield TestClient(app)


@pytest.fixture(scope="function")
def auth_token(client, setup_test_db):
    """创建并返回认证token"""
    from src.services.auth_service import AuthService
    from src.models import User
    from datetime import datetime
    from src.db_models import UserModel
    import uuid

    # 创建用户
    db = TestSessionLocal()
    try:
        password_hash = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user_model = UserModel(
            user_id=str(uuid.uuid4()),
            username="测试用户",
            email="test2@example.com",
            password_hash=password_hash,
            created_at=datetime.now()
        )
        db.add(user_model)
        db.commit()
        db.refresh(user_model)

        # 使用auth_service生成token
        auth_service = AuthService()
        user = User(
            user_id=user_model.user_id,
            username=user_model.username,
            email=user_model.email,
            password_hash=password_hash
        )
        token = auth_service.generate_token(user, remember_me=False)
        return token
    finally:
        db.close()


class TestGetConversations:
    """测试获取会话列表"""

    def test_get_conversations(self, client, auth_token):
        """测试获取会话列表"""
        tool_id = "ai_tools"

        response = client.get(
            f"/api/v1/tools/{tool_id}/conversations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 应该返回200（可能是空列表）
        assert response.status_code == 200

        data = response.json()
        assert "conversations" in data
        assert isinstance(data["conversations"], list)

    def test_get_conversations_unauthorized(self, client):
        """测试未认证访问返回401"""
        tool_id = "ai_tools"

        response = client.get(f"/api/v1/tools/{tool_id}/conversations")

        assert response.status_code == 401


class TestDeleteConversation:
    """测试删除会话"""

    def test_delete_conversation_not_found(self, client, auth_token):
        """测试删除不存在的会话"""
        tool_id = "ai_tools"
        conv_id = "nonexistent-conv-id"

        response = client.delete(
            f"/api/v1/tools/{tool_id}/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 404

    def test_delete_conversation_unauthorized(self, client):
        """测试未认证删除返回401"""
        tool_id = "ai_tools"
        conv_id = "test-conv-id"

        response = client.delete(f"/api/v1/tools/{tool_id}/conversations/{conv_id}")

        assert response.status_code == 401


class TestGetConversationDetail:
    """测试获取会话详情"""

    def test_get_conversation_detail_not_found(self, client, auth_token):
        """测试获取不存在的会话详情"""
        tool_id = "ai_tools"
        conv_id = "nonexistent-conv-id"

        response = client.get(
            f"/api/v1/tools/{tool_id}/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 404

    def test_get_conversation_detail_unauthorized(self, client):
        """测试未认证访问返回401"""
        tool_id = "ai_tools"
        conv_id = "test-conv-id"

        response = client.get(f"/api/v1/tools/{tool_id}/conversations/{conv_id}")

        assert response.status_code == 401

    def test_get_conversation_detail_after_chat(self, client, auth_token):
        """测试获取聊天后的会话详情"""
        tool_id = "lesson-generator"

        # 首先创建一个会话（通过聊天）
        chat_response = client.post(
            f"/api/v1/tools/{tool_id}/chat",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "Test message",
                "session_id": None,
                "history": None
            }
        )

        # 如果工具存在，会话应该被创建
        if chat_response.status_code == 200:
            session_id = chat_response.json().get("session_id")

            # 获取会话详情
            response = client.get(
                f"/api/v1/tools/{tool_id}/conversations/{session_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "conversation" in data
            assert "messages" in data
            assert data["conversation"]["session_id"] == session_id
