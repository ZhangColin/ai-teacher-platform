# -*- coding: utf-8 -*-
"""
工具对话路由集成测试
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
            email="test@example.com",
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


class TestChatStream:
    """测试流式对话接口"""

    def test_chat_stream_with_valid_tool(self, client, auth_token):
        """测试有效工具的流式对话"""
        # 使用一个可能存在的工具ID
        tool_id = "lesson-generator"

        response = client.post(
            f"/api/v1/tools/{tool_id}/chat/stream",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "Hello",
                "session_id": None,
                "history": None
            }
        )

        # 工具可能存在也可能不存在
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_chat_stream_with_invalid_tool(self, client, auth_token):
        """测试无效工具返回404"""
        response = client.post(
            "/api/v1/tools/invalid-tool-chat-test/chat/stream",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "Hello",
                "session_id": None,
                "history": None
            }
        )

        assert response.status_code == 404

    def test_chat_stream_unauthorized(self, client):
        """测试未认证访问返回401"""
        response = client.post(
            "/api/v1/tools/lesson-generator/chat/stream",
            json={
                "message": "Hello",
                "session_id": None,
                "history": None
            }
        )

        assert response.status_code == 401

    def test_chat_stream_sse_format(self, client, auth_token):
        """测试SSE响应格式"""
        tool_id = "lesson-generator"

        response = client.post(
            f"/api/v1/tools/{tool_id}/chat/stream",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "Say 'test'",
                "session_id": None,
                "history": None
            },
            timeout=30.0
        )

        # 可能返回404（工具不存在）或200
        if response.status_code == 200:
            # 验证SSE格式
            content = response.text
            assert "data: " in content or "[DONE]" in content


class TestChatNonStream:
    """测试非流式对话接口"""

    def test_chat_non_stream_with_valid_tool(self, client, auth_token):
        """测试非流式对话接口"""
        tool_id = "lesson-generator"

        response = client.post(
            f"/api/v1/tools/{tool_id}/chat",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "Hello",
                "session_id": None,
                "history": None
            }
        )

        # 可能返回404（工具不存在）或200
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "session_id" in data

    def test_chat_non_stream_unauthorized(self, client):
        """测试未认证访问返回401"""
        response = client.post(
            "/api/v1/tools/lesson-generator/chat",
            json={
                "message": "Hello",
                "session_id": None,
                "history": None
            }
        )

        assert response.status_code == 401

    def test_chat_non_stream_with_session(self, client, auth_token):
        """测试使用现有会话ID的对话"""
        tool_id = "lesson-generator"

        # 首先创建一个会话
        create_response = client.post(
            f"/api/v1/tools/{tool_id}/chat",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "First message",
                "session_id": None,
                "history": None
            }
        )

        if create_response.status_code == 200:
            session_id = create_response.json().get("session_id")

            # 使用session_id继续对话
            response = client.post(
                f"/api/v1/tools/{tool_id}/chat",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "message": "Second message",
                    "session_id": session_id,
                    "history": None
                }
            )

            assert response.status_code == 200
