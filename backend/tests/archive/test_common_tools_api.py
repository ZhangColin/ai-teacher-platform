"""常用工具API集成测试"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.main import app
from src.database import SessionLocal, engine, Base
from src.db_models import UserModel, ToolCategoryModel, CommonToolModel, CommonToolType
from src.services.auth_service import AuthService


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 创建会话
    db = SessionLocal()
    
    yield db
    
    # 清理数据
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture(scope="function")
def test_user_token(db_session: Session):
    """创建测试用户并返回Token"""
    # 创建测试用户
    import bcrypt
    password_hash = bcrypt.hashpw("testpass123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user = UserModel(
        user_id="test-user-id",
        username="testuser",
        nickname="测试用户",
        email="test@example.com",
        password_hash=password_hash,
        created_at=datetime.now()
    )
    db_session.add(user)
    db_session.commit()
    
    # 生成Token
    auth_service = AuthService()
    token = auth_service.create_token(user_id=user.user_id, remember_me=False)
    
    return token


@pytest.fixture(scope="function")
def setup_test_data(db_session: Session):
    """设置测试数据"""
    # 创建分类
    category1 = ToolCategoryModel(
        id="test-category-1",
        name="测试分类1",
        icon="test-icon-1",
        order=1,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    category2 = ToolCategoryModel(
        id="test-category-2",
        name="测试分类2",
        icon="test-icon-2",
        order=2,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db_session.add_all([category1, category2])
    
    # 创建工具
    tool1 = CommonToolModel(
        id="test-tool-1",
        name="测试工具1",
        description="这是测试工具1的描述",
        category_id="test-category-1",
        type=CommonToolType.built_in,
        icon="tool-icon-1",
        html_path=None,
        order=1,
        visible=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    tool2 = CommonToolModel(
        id="test-tool-2",
        name="测试HTML工具",
        description="这是测试HTML工具的描述",
        category_id="test-category-2",
        type=CommonToolType.html,
        icon="tool-icon-2",
        html_path="common_tools/html/test-tool-2/index.html",
        order=1,
        visible=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db_session.add_all([tool1, tool2])
    db_session.commit()


class TestCommonToolsAPI:
    """常用工具API集成测试类"""
    
    def test_get_categories_success(self, test_client, test_user_token, setup_test_data):
        """测试获取分类列表 - 成功"""
        # 执行
        response = test_client.get(
            "/api/v1/common-tools/categories",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        assert len(data["categories"]) == 2
        
        # 验证第一个分类
        cat1 = data["categories"][0]
        assert cat1["id"] == "test-category-1"
        assert cat1["name"] == "测试分类1"
        assert cat1["order"] == 1
        assert len(cat1["tools"]) == 1
        assert cat1["tools"][0]["id"] == "test-tool-1"
    
    def test_get_categories_unauthorized(self, test_client, setup_test_data):
        """测试获取分类列表 - 未认证"""
        # 执行
        response = test_client.get("/api/v1/common-tools/categories")
        
        # 验证
        assert response.status_code == 403  # FastAPI HTTPBearer 返回403
    
    def test_get_tool_detail_built_in_success(self, test_client, test_user_token, setup_test_data):
        """测试获取工具详情 - 内置工具成功"""
        # 执行
        response = test_client.get(
            "/api/v1/common-tools/tools/test-tool-1",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "test-tool-1"
        assert data["name"] == "测试工具1"
        assert data["type"] == "built-in"
        assert data["category_id"] == "test-category-1"
        assert data["category_name"] == "测试分类1"
        assert data["html_url"] is None
    
    def test_get_tool_detail_html_success(self, test_client, test_user_token, setup_test_data):
        """测试获取工具详情 - HTML工具成功"""
        # 执行
        response = test_client.get(
            "/api/v1/common-tools/tools/test-tool-2",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "test-tool-2"
        assert data["type"] == "html"
        assert data["html_url"] == "/static/common_tools/html/test-tool-2/index.html"
    
    def test_get_tool_detail_not_found(self, test_client, test_user_token, setup_test_data):
        """测试获取工具详情 - 工具不存在"""
        # 执行
        response = test_client.get(
            "/api/v1/common-tools/tools/non-existent",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # 验证
        assert response.status_code == 404
        assert "工具不存在或已下线" in response.json()["detail"]
    
    def test_get_tool_detail_unauthorized(self, test_client, setup_test_data):
        """测试获取工具详情 - 未认证"""
        # 执行
        response = test_client.get("/api/v1/common-tools/tools/test-tool-1")
        
        # 验证
        assert response.status_code == 403  # FastAPI HTTPBearer 返回403
