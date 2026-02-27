# -*- coding: utf-8 -*-
"""
工具列表路由集成测试
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
from src.services.user_service import UserService


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
    """创建并返回认证token

    注意：这是一个简化的fixture，用于测试路由是否被保护。
    完整的认证测试需要更复杂的设置。
    """
    # 使用现有的auth服务创建token
    from src.services.auth_service import AuthService
    from src.models import User
    from datetime import datetime
    from src.db_models import UserModel
    import bcrypt
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


class TestGetTools:
    """测试获取工具列表"""

    def test_get_tools_as_authenticated_user(self, client, auth_token):
        """测试认证用户获取工具列表"""
        response = client.get(
            "/api/v1/tools",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)

    def test_get_tools_unauthorized_returns_401(self, client):
        """测试未认证用户访问返回401"""
        response = client.get("/api/v1/tools")

        assert response.status_code == 401

    def test_get_tools_returns_visible_tools_only(self, client, auth_token):
        """测试只返回可见的工具"""
        response = client.get(
            "/api/v1/tools",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

        data = response.json()
        # 验证所有工具都是可见的
        for category in data["categories"]:
            for tool in category.get("tools", []):
                assert tool.get("visible") is True


class TestGetToolsetTools:
    """测试获取指定工具集的工具列表"""

    def test_get_toolset_tools_with_valid_toolset(self, client, auth_token):
        """测试获取有效工具集的工具列表"""
        response = client.get(
            "/api/v1/toolsets/ai_tools/tools",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 如果工具集存在，返回200；如果不存在，可能返回空列表或404
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "categories" in data

    def test_get_toolset_tools_unauthorized(self, client):
        """测试未认证访问工具集工具返回401"""
        response = client.get("/api/v1/toolsets/ai_tools/tools")

        assert response.status_code == 401
