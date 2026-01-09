"""常用工具服务测试"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from src.services.common_tool_service import CommonToolService
from src.db_models import ToolCategoryModel, CommonToolModel, CommonToolType
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
def common_tool_service():
    """创建常用工具服务实例"""
    return CommonToolService()


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
    category3 = ToolCategoryModel(
        id="test-category-3",
        name="空分类",
        icon="test-icon-3",
        order=3,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db_session.add_all([category1, category2, category3])
    
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
        name="测试工具2",
        description="这是测试工具2的描述",
        category_id="test-category-1",
        type=CommonToolType.html,
        icon="tool-icon-2",
        html_path="common_tools/html/test-tool-2/index.html",
        order=2,
        visible=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    tool3 = CommonToolModel(
        id="test-tool-3",
        name="测试工具3",
        description="这是测试工具3的描述",
        category_id="test-category-2",
        type=CommonToolType.built_in,
        icon="tool-icon-3",
        html_path=None,
        order=1,
        visible=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    tool4 = CommonToolModel(
        id="test-tool-4-hidden",
        name="隐藏工具",
        description="这是隐藏工具的描述",
        category_id="test-category-1",
        type=CommonToolType.built_in,
        icon="tool-icon-4",
        html_path=None,
        order=3,
        visible=False,  # 不可见
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db_session.add_all([tool1, tool2, tool3, tool4])
    db_session.commit()
    
    return {
        "categories": [category1, category2, category3],
        "tools": [tool1, tool2, tool3, tool4]
    }


class TestCommonToolService:
    """常用工具服务测试类"""
    
    def test_get_categories_with_tools_success(self, common_tool_service, setup_test_data):
        """测试获取分类和工具列表 - 成功"""
        # 执行
        result = common_tool_service.get_categories_with_tools()
        
        # 验证
        assert result is not None
        assert len(result.categories) == 2  # 只有2个分类有可见工具
        
        # 验证第一个分类
        cat1 = result.categories[0]
        assert cat1.id == "test-category-1"
        assert cat1.name == "测试分类1"
        assert cat1.icon == "test-icon-1"
        assert cat1.order == 1
        assert len(cat1.tools) == 2  # 有2个可见工具
        
        # 验证工具按order排序
        assert cat1.tools[0].id == "test-tool-1"
        assert cat1.tools[0].order == 1
        assert cat1.tools[1].id == "test-tool-2"
        assert cat1.tools[1].order == 2
        
        # 验证第二个分类
        cat2 = result.categories[1]
        assert cat2.id == "test-category-2"
        assert len(cat2.tools) == 1
    
    def test_get_categories_excludes_empty_categories(self, common_tool_service, setup_test_data):
        """测试获取分类列表 - 排除没有可见工具的分类"""
        # 执行
        result = common_tool_service.get_categories_with_tools()
        
        # 验证：category-3 是空分类，不应该返回
        category_ids = [cat.id for cat in result.categories]
        assert "test-category-3" not in category_ids
    
    def test_get_categories_excludes_invisible_tools(self, common_tool_service, setup_test_data):
        """测试获取分类列表 - 排除不可见工具"""
        # 执行
        result = common_tool_service.get_categories_with_tools()
        
        # 验证：test-tool-4-hidden 是隐藏工具，不应该返回
        cat1 = result.categories[0]
        tool_ids = [tool.id for tool in cat1.tools]
        assert "test-tool-4-hidden" not in tool_ids
    
    def test_get_tool_detail_built_in_success(self, common_tool_service, setup_test_data):
        """测试获取工具详情 - 内置工具成功"""
        # 执行
        result = common_tool_service.get_tool_detail("test-tool-1")
        
        # 验证
        assert result is not None
        assert result.id == "test-tool-1"
        assert result.name == "测试工具1"
        assert result.description == "这是测试工具1的描述"
        assert result.category_id == "test-category-1"
        assert result.category_name == "测试分类1"
        assert result.type == "built-in"
        assert result.icon == "tool-icon-1"
        assert result.html_url is None  # 内置工具没有html_url
    
    def test_get_tool_detail_html_success(self, common_tool_service, setup_test_data):
        """测试获取工具详情 - HTML工具成功"""
        # 执行
        result = common_tool_service.get_tool_detail("test-tool-2")
        
        # 验证
        assert result is not None
        assert result.id == "test-tool-2"
        assert result.type == "html"
        assert result.html_url == "/static/common_tools/html/test-tool-2/index.html"
    
    def test_get_tool_detail_not_found(self, common_tool_service, setup_test_data):
        """测试获取工具详情 - 工具不存在"""
        # 执行
        result = common_tool_service.get_tool_detail("non-existent-tool")
        
        # 验证
        assert result is None
    
    def test_get_tool_detail_invisible(self, common_tool_service, setup_test_data):
        """测试获取工具详情 - 隐藏工具不可见"""
        # 执行
        result = common_tool_service.get_tool_detail("test-tool-4-hidden")
        
        # 验证
        assert result is None  # 隐藏工具不应返回
