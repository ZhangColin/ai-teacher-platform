"""作品展示服务测试"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from src.services.work_service import WorkService
from src.db_models import WorkCategoryModel, WorkModel
from src.database import SessionLocal, engine, Base


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
def work_service():
    """创建作品展示服务实例"""
    return WorkService()


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
    category3 = WorkCategoryModel(
        id="test-work-category-3",
        name="空分类",
        icon="photo",
        order=3,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db_session.add_all([category1, category2, category3])
    
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
        name="动画按钮集合",
        description="多种创意动画按钮效果",
        category_id="test-work-category-1",
        icon="cursor-arrow-rays",
        html_path="works/html/animated-button/index.html",
        order=2,
        visible=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    work3 = WorkModel(
        id="test-work-3",
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
    work4 = WorkModel(
        id="test-work-4",
        name="隐藏的作品",
        description="这个作品不应该显示",
        category_id="test-work-category-1",
        icon="eye-slash",
        html_path="works/html/hidden-work/index.html",
        order=3,
        visible=False,  # 不可见
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db_session.add_all([work1, work2, work3, work4])
    db_session.commit()
    
    yield
    
    # 清理数据（会话关闭时自动清理）


class TestWorkService:
    """测试 WorkService 类"""
    
    def test_get_categories_with_works_success(
        self,
        work_service: WorkService,
        db_session: Session,
        setup_test_data
    ):
        """测试成功获取分类及其作品列表"""
        # 调用服务方法
        result = work_service.get_categories_with_works()
        
        # 验证结果
        assert result is not None
        assert len(result.categories) == 2  # 只返回有可见作品的分类
        
        # 验证第一个分类
        category1 = result.categories[0]
        assert category1.id == "test-work-category-1"
        assert category1.name == "创意设计"
        assert category1.icon == "sparkles"
        assert category1.order == 1
        assert len(category1.works) == 2  # 只有2个可见作品
        
        # 验证第一个作品
        work1 = category1.works[0]
        assert work1.id == "test-work-1"
        assert work1.name == "交互式卡片"
        assert work1.description == "一个精美的交互式卡片效果展示"
        assert work1.icon == "star"
        assert work1.order == 1
        
        # 验证第二个分类
        category2 = result.categories[1]
        assert category2.id == "test-work-category-2"
        assert category2.name == "数据可视化"
        assert len(category2.works) == 1
        
        # 验证作品排序（按order升序）
        assert category1.works[0].order < category1.works[1].order
    
    def test_get_categories_with_works_only_visible(
        self,
        work_service: WorkService,
        db_session: Session,
        setup_test_data
    ):
        """测试只返回可见作品"""
        result = work_service.get_categories_with_works()
        
        # 验证不包含隐藏作品
        all_work_ids = []
        for category in result.categories:
            for work in category.works:
                all_work_ids.append(work.id)
        
        assert "test-work-4" not in all_work_ids  # 隐藏作品不应出现
    
    def test_get_categories_with_works_exclude_empty_categories(
        self,
        work_service: WorkService,
        db_session: Session,
        setup_test_data
    ):
        """测试不返回没有可见作品的分类"""
        result = work_service.get_categories_with_works()
        
        # 验证不包含空分类
        category_names = [cat.name for cat in result.categories]
        assert "空分类" not in category_names
    
    def test_get_categories_with_works_order_by_category(
        self,
        work_service: WorkService,
        db_session: Session,
        setup_test_data
    ):
        """测试分类按order字段排序"""
        result = work_service.get_categories_with_works()
        
        # 验证分类排序
        assert result.categories[0].order < result.categories[1].order
        assert result.categories[0].order == 1
        assert result.categories[1].order == 2
    
    def test_get_categories_with_works_empty_database(
        self,
        work_service: WorkService,
        db_session: Session
    ):
        """测试数据库为空时返回空列表"""
        result = work_service.get_categories_with_works()
        
        # 验证返回空列表
        assert result is not None
        assert len(result.categories) == 0
