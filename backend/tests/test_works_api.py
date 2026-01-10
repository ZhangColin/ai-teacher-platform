"""作品展示API集成测试"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.main import app
from src.database import SessionLocal, engine, Base
from src.db_models import UserModel, WorkCategoryModel, WorkModel
from src.services.auth_service import AuthService
from src.models import User


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
    
    user_model = UserModel(
        user_id="test-user-id",
        username="testuser",
        nickname="测试用户",
        email="test@example.com",
        password_hash=password_hash,
        created_at=datetime.now()
    )
    db_session.add(user_model)
    db_session.commit()
    
    # 创建User领域对象用于生成Token
    user = User(
        user_id=user_model.user_id,
        username=user_model.username,
        nickname=user_model.nickname,
        email=user_model.email,
        phone=user_model.phone,
        password_hash=user_model.password_hash,
        created_at=user_model.created_at
    )
    
    # 生成Token
    auth_service = AuthService()
    token = auth_service.generate_token(user=user, remember_me=False)
    
    return token


@pytest.fixture(scope="function")
def setup_test_data(db_session: Session):
    """设置测试数据"""
    # 创建分类
    category1 = WorkCategoryModel(
        id="test-work-category-1",
        name="创意设计",
        icon="sparkles",
        order=1,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    category2 = WorkCategoryModel(
        id="test-work-category-2",
        name="数据可视化",
        icon="chart-bar",
        order=2,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db_session.add_all([category1, category2])
    
    # 创建作品
    work1 = WorkModel(
        id="test-work-1",
        name="交互式卡片",
        description="一个精美的交互式卡片效果展示",
        category_id="test-work-category-1",
        icon="star",
        html_path="works/html/interactive-card/index.html",
        order=1,
        visible=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    work2 = WorkModel(
        id="test-work-2",
        name="图表演示",
        description="各种图表的可视化展示",
        category_id="test-work-category-2",
        icon="presentation-chart-line",
        html_path="works/html/chart-demo/index.html",
        order=1,
        visible=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db_session.add_all([work1, work2])
    db_session.commit()
    
    yield
    
    # 清理数据（会话关闭时自动清理）


class TestWorksAPI:
    """测试作品展示API"""
    
    def test_get_work_categories_success(
        self,
        test_client: TestClient,
        db_session: Session,
        test_user_token: str,
        setup_test_data
    ):
        """测试成功获取作品分类列表"""
        # 发送请求
        response = test_client.get(
            "/api/v1/works/categories",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        
        # 验证数据结构
        assert "categories" in data
        assert len(data["categories"]) == 2
        
        # 验证第一个分类
        category1 = data["categories"][0]
        assert category1["id"] == "test-work-category-1"
        assert category1["name"] == "创意设计"
        assert category1["icon"] == "sparkles"
        assert category1["order"] == 1
        assert len(category1["works"]) == 1
        
        # 验证作品数据
        work1 = category1["works"][0]
        assert work1["id"] == "test-work-1"
        assert work1["name"] == "交互式卡片"
        assert work1["description"] == "一个精美的交互式卡片效果展示"
        assert work1["icon"] == "star"
    
    def test_get_work_categories_unauthorized(
        self,
        test_client: TestClient,
        db_session: Session,
        setup_test_data
    ):
        """测试未授权访问"""
        # 不带Token发送请求
        response = test_client.get("/api/v1/works/categories")
        
        # 验证返回401
        assert response.status_code == 401
    
    def test_get_work_categories_empty(
        self,
        test_client: TestClient,
        db_session: Session,
        test_user_token: str
    ):
        """测试获取空分类列表"""
        # 发送请求（没有创建测试数据）
        response = test_client.get(
            "/api/v1/works/categories",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) == 0
    
    def test_get_work_detail_success(
        self,
        test_client: TestClient,
        db_session: Session,
        test_user_token: str,
        setup_test_data
    ):
        """测试成功获取作品详情"""
        # 发送请求
        response = test_client.get(
            "/api/v1/works/test-work-1",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        
        # 验证数据
        assert data["id"] == "test-work-1"
        assert data["name"] == "交互式卡片"
        assert data["description"] == "一个精美的交互式卡片效果展示"
        assert data["category_id"] == "test-work-category-1"
        assert data["category_name"] == "创意设计"
        assert data["icon"] == "star"
        assert data["html_url"] == "/static/works/html/interactive-card/index.html"
        assert "created_at" in data
    
    def test_get_work_detail_not_found(
        self,
        test_client: TestClient,
        db_session: Session,
        test_user_token: str,
        setup_test_data
    ):
        """测试获取不存在的作品"""
        # 发送请求
        response = test_client.get(
            "/api/v1/works/non-existent-work",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # 验证返回404
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "作品不存在或已下线"
    
    def test_get_work_detail_unauthorized(
        self,
        test_client: TestClient,
        db_session: Session,
        setup_test_data
    ):
        """测试未授权访问作品详情"""
        # 不带Token发送请求
        response = test_client.get("/api/v1/works/test-work-1")
        
        # 验证返回401
        assert response.status_code == 401
