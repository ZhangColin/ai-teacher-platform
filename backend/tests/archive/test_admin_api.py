"""用户管理API集成测试"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os
from typing import Generator

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.main import app
from src.database import get_db, Base
from src.services.user_service import UserService


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """每个测试前自动设置测试数据库和UserService"""
    # 为每个测试创建独立的数据库文件
    test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db_path = test_db_file.name
    test_db_file.close()
    
    # 创建测试数据库引擎
    test_engine = create_engine(f"sqlite:///{test_db_path}", echo=False, connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # 创建表
    Base.metadata.create_all(bind=test_engine)
    
    # 覆盖get_db依赖，使用测试数据库
    def override_get_db() -> Generator[TestSessionLocal, None, None]:
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock UserService，让它在测试中使用测试数据库
    from src import main
    original_main_user_service = main.user_service
    
    # 创建测试用的UserService实例
    test_user_service = UserService()
    test_user_service._get_db = override_get_db
    main.user_service = test_user_service
    
    yield
    
    # 清理：删除表，恢复原始user_service，删除临时数据库文件
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.pop(get_db)
    main.user_service = original_main_user_service
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)


@pytest.fixture(scope="function")
def client(setup_test_db):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture(scope="function")
def test_user_and_token(client, setup_test_db):
    """创建测试用户并获取Token"""
    from src import main
    
    # 创建用户
    user = main.user_service.create_user(
        username="测试用户",
        email="test@example.com",
        password="password123"
    )
    
    # 登录获取Token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
            "remember_me": False
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    return user, token


class TestGetUserListAPI:
    """获取用户列表API测试"""
    
    def test_get_user_list_success(self, client, test_user_and_token):
        """测试获取用户列表成功"""
        _, token = test_user_and_token
        
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["users"]) == 1
        assert data["users"][0]["email"] == "test@example.com"
        assert data["total"] == 1
    
    def test_get_user_list_with_pagination(self, client, test_user_and_token):
        """测试获取用户列表（分页）"""
        _, token = test_user_and_token
        
        # 创建更多用户
        from src import main
        for i in range(5):
            main.user_service.create_user(
                username=f"用户{i}",
                email=f"user{i}@example.com",
                password="password123"
            )
        
        # 测试第一页
        response = client.get(
            "/api/v1/admin/users",
            params={"page": 1, "page_size": 2},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 6  # 1个测试用户 + 5个新用户
    
    def test_get_user_list_no_token(self, client):
        """测试获取用户列表失败（未提供Token）"""
        response = client.get("/api/v1/admin/users")
        
        assert response.status_code == 401
    
    def test_get_user_list_invalid_token(self, client):
        """测试获取用户列表失败（无效Token）"""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401


class TestCreateUserAPI:
    """创建用户API测试"""
    
    def test_create_user_success(self, client, test_user_and_token):
        """测试创建用户成功"""
        _, token = test_user_and_token
        
        response = client.post(
            "/api/v1/admin/users",
            json={
                "username": "新用户",
                "email": "newuser@example.com",
                "password": "password123",
                "avatar": None
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["username"] == "新用户"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["user_id"] is not None
    
    def test_create_user_with_avatar(self, client, test_user_and_token):
        """测试创建用户（带头像）"""
        _, token = test_user_and_token
        
        response = client.post(
            "/api/v1/admin/users",
            json={
                "username": "带头像用户",
                "email": "avatar@example.com",
                "password": "password123",
                "avatar": "http://example.com/avatar.png"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["avatar"] == "http://example.com/avatar.png"
    
    def test_create_user_duplicate_email(self, client, test_user_and_token):
        """测试创建用户失败（邮箱重复）"""
        _, token = test_user_and_token
        
        # 尝试创建相同邮箱的用户
        response = client.post(
            "/api/v1/admin/users",
            json={
                "username": "重复邮箱用户",
                "email": "test@example.com",  # 与测试用户相同
                "password": "password123",
                "avatar": None
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "邮箱已存在" in data.get("detail", "")
    
    def test_create_user_invalid_email_format(self, client, test_user_and_token):
        """测试创建用户失败（邮箱格式错误）"""
        _, token = test_user_and_token
        
        response = client.post(
            "/api/v1/admin/users",
            json={
                "username": "格式错误用户",
                "email": "invalid-email",
                "password": "password123",
                "avatar": None
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422  # Pydantic验证错误
    
    def test_create_user_password_too_short(self, client, test_user_and_token):
        """测试创建用户失败（密码长度不足）"""
        _, token = test_user_and_token
        
        response = client.post(
            "/api/v1/admin/users",
            json={
                "username": "短密码用户",
                "email": "shortpass@example.com",
                "password": "12345",  # 少于6位
                "avatar": None
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422  # Pydantic验证错误
    
    def test_create_user_no_token(self, client):
        """测试创建用户失败（未提供Token）"""
        response = client.post(
            "/api/v1/admin/users",
            json={
                "username": "新用户",
                "email": "newuser@example.com",
                "password": "password123",
                "avatar": None
            }
        )
        
        assert response.status_code == 401
    
    def test_create_user_invalid_token(self, client):
        """测试创建用户失败（无效Token）"""
        response = client.post(
            "/api/v1/admin/users",
            json={
                "username": "新用户",
                "email": "newuser@example.com",
                "password": "password123",
                "avatar": None
            },
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401

