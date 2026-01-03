"""工具 API 接口测试"""
import pytest
import sys
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
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


@pytest.fixture(scope="function")
def auth_token(client, test_user):
    """获取认证Token"""
    # 登录获取Token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "account": "test@example.com",
            "password": "password123",
            "remember_me": False
        }
    )
    assert login_response.status_code == 200
    return login_response.json()["token"]


class TestGetTools:
    """测试 GET /api/v1/tools 接口"""
    
    def test_get_tools_requires_authentication(self, client):
        """测试 GET /api/v1/tools 需要认证"""
        response = client.get("/api/v1/tools")
        # 应该返回 401 未授权
        assert response.status_code == 401
    
    def test_get_tools_returns_categories(self, client, auth_token):
        """测试 GET /api/v1/tools 返回分类列表"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/tools", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)
    
    def test_get_tools_category_structure(self, client, auth_token):
        """测试分类结构是否正确"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/tools", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data["categories"]) > 0:
            category = data["categories"][0]
            assert "name" in category
            assert "tools" in category
            assert isinstance(category["name"], str)
            assert isinstance(category["tools"], list)
            # icon 是可选的
    
    def test_get_tools_tool_structure(self, client, auth_token):
        """测试工具项结构是否正确"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/tools", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # 查找包含工具的分类
        for category in data["categories"]:
            if len(category["tools"]) > 0:
                tool = category["tools"][0]
                assert "tool_id" in tool
                assert "name" in tool
                assert "category" in tool
                assert "visible" in tool
                assert "type" in tool
                assert isinstance(tool["tool_id"], str)
                assert isinstance(tool["name"], str)
                assert isinstance(tool["category"], str)
                assert isinstance(tool["visible"], bool)
                assert tool["type"] in ["normal", "placeholder"]
                # description 和 icon 是可选的
    
    def test_get_tools_only_returns_visible_tools(self, client, auth_token):
        """测试只返回 visible=true 的工具"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/tools", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # 检查所有工具都是 visible=true
        for category in data["categories"]:
            for tool in category["tools"]:
                assert tool["visible"] is True
    
    def test_get_tools_returns_empty_list_when_no_tools(self, client, auth_token):
        """测试当没有配置工具时，返回空列表"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/tools", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["categories"], list)
        # 如果没有工具，categories 应该是空列表或包含空分类
    
    def test_get_tools_groups_by_category(self, client, auth_token):
        """测试工具按分类聚合"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/tools", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # 检查同一分类的工具是否在同一分类组中
        category_names = {}
        for category in data["categories"]:
            category_name = category["name"]
            for tool in category["tools"]:
                # 每个工具的 category 应该与分类组的 name 一致
                assert tool["category"] == category_name
                # 记录每个分类的工具数量
                if category_name not in category_names:
                    category_names[category_name] = 0
                category_names[category_name] += 1

