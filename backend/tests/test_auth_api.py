"""登录API集成测试"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.main import app
from src.database import get_db, Base
from src.db_models import UserModel
from src.services.user_service import UserService


# 创建测试数据库（使用临时文件数据库，确保所有连接共享同一个数据库）
import tempfile
import os

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
    """每个测试前自动设置测试数据库和UserService"""
    # 为每个测试创建独立的数据库文件
    test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db_path = test_db_file.name
    test_db_file.close()
    _test_db_paths.append(test_db_path)
    
    # 创建测试数据库引擎
    test_engine = create_engine(f"sqlite:///{test_db_path}", echo=False, connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # 创建表
    Base.metadata.create_all(bind=test_engine)
    
    # Mock UserService，让它在测试中使用测试数据库
    from src import main
    original_main_user_service = main.user_service
    
    # 创建测试用的UserService实例
    test_user_service = UserService()
    # Mock _get_db方法，返回生成器
    def test_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
    test_user_service._get_db = test_get_db
    main.user_service = test_user_service
    
    yield
    
    # 清理：删除表，恢复原始user_service，删除临时数据库文件
    Base.metadata.drop_all(bind=test_engine)
    main.user_service = original_main_user_service
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)


@pytest.fixture(scope="function")
def client(setup_test_db):
    """创建测试客户端"""
    yield TestClient(app)


@pytest.fixture(scope="function")
def test_user(setup_test_db):
    """创建测试用户"""
    from src import main
    # 使用main中的user_service（已经被mock为使用测试数据库）
    user = main.user_service.create_user(
        username="测试用户",
        email="test@example.com",
        password="password123"
    )
    return user


class TestLoginAPI:
    """登录API测试"""
    
    def test_login_success(self, client, test_user):
        """测试登录成功"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123",
                "remember_me": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert "expires_in" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["username"] == "测试用户"
        assert data["expires_in"] == 86400  # 24小时
    
    def test_login_success_with_remember_me(self, client, test_user):
        """测试登录成功（记住我）"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123",
                "remember_me": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["expires_in"] == 604800  # 7天
    
    def test_login_failure_wrong_password(self, client, test_user):
        """测试登录失败（密码错误）"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrong_password",
                "remember_me": False
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "账号或密码错误" in data.get("detail", "")
    
    def test_login_failure_user_not_found(self, client):
        """测试登录失败（用户不存在）"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "notfound@example.com",
                "password": "password123",
                "remember_me": False
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "账号或密码错误" in data.get("detail", "")
    
    def test_login_failure_invalid_email_format(self, client):
        """测试登录失败（邮箱格式错误）"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "invalid-email",
                "password": "password123",
                "remember_me": False
            }
        )
        
        assert response.status_code == 422  # Pydantic验证错误
    
    def test_login_failure_password_too_short(self, client):
        """测试登录失败（密码长度不足）"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "12345",  # 少于6位
                "remember_me": False
            }
        )
        
        assert response.status_code == 422  # Pydantic验证错误


class TestGetCurrentUserAPI:
    """获取当前用户API测试"""
    
    def test_get_current_user_success(self, client, test_user):
        """测试获取当前用户成功"""
        # 先登录获取Token
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
        
        # 使用Token获取当前用户信息
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["user_id"] == test_user.user_id
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["username"] == "测试用户"
    
    def test_get_current_user_no_token(self, client):
        """测试获取当前用户失败（未提供Token）"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client):
        """测试获取当前用户失败（无效Token）"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401
    
    def test_get_current_user_user_not_found(self, client):
        """测试获取当前用户失败（用户不存在）"""
        from src.services.auth_service import AuthService
        from src.models import User
        from datetime import datetime
        
        # 创建一个Token，但用户不存在
        auth_service = AuthService()
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        fake_user = User(
            user_id=fake_user_id,
            username="fake",
            email="fake@example.com",
            password_hash="fake",
            created_at=datetime.now()
        )
        token = auth_service.generate_token(fake_user, remember_me=False)
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
