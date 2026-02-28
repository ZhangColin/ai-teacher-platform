"""UserService 单元测试"""
import pytest
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.user_service import UserService
from src.models import User
from src.db_models import Base


class TestUserService:
    """测试 UserService 类"""
    
    def setup_method(self):
        """每个测试方法前执行：创建测试数据库"""
        # 使用SQLite内存数据库进行测试（不依赖MySQL环境）
        test_engine = create_engine("sqlite:///:memory:?cache=shared", echo=False, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=test_engine)
        
        # 创建测试会话
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        # 创建服务实例，并注入测试数据库会话
        self.service = UserService()
        # 临时替换_get_db方法，使用测试数据库（返回生成器）
        def test_get_db():
            db = TestSessionLocal()
            try:
                yield db
            finally:
                db.close()
        self.service._get_db = test_get_db
        self.test_engine = test_engine
    
    def teardown_method(self):
        """每个测试方法后执行：清理数据库"""
        # SQLite内存数据库会自动清理，无需手动删除
        pass
    
    def test_create_user(self):
        """测试创建用户"""
        user = self.service.create_user(
            username="测试用户",
            email="test@example.com",
            password="password123"
        )
        
        assert user.username == "测试用户"
        assert user.email == "test@example.com"
        assert user.user_id is not None
        assert user.verify_password("password123") is True
    
    def test_get_user_by_email(self):
        """测试根据邮箱获取用户"""
        # 先创建用户
        created_user = self.service.create_user(
            username="测试用户",
            email="test@example.com",
            password="password123"
        )
        
        # 根据邮箱查询
        found_user = self.service.get_user_by_email("test@example.com")
        
        assert found_user is not None
        assert found_user.user_id == created_user.user_id
        assert found_user.email == "test@example.com"
        assert found_user.username == "测试用户"
    
    def test_get_user_by_email_not_found(self):
        """测试根据邮箱获取用户（用户不存在）"""
        found_user = self.service.get_user_by_email("notfound@example.com")
        assert found_user is None
    
    def test_get_user_by_id(self):
        """测试根据用户ID获取用户"""
        # 先创建用户
        created_user = self.service.create_user(
            username="测试用户",
            email="test@example.com",
            password="password123"
        )
        
        # 根据ID查询
        found_user = self.service.get_user_by_id(created_user.user_id)
        
        assert found_user is not None
        assert found_user.user_id == created_user.user_id
        assert found_user.email == "test@example.com"
    
    def test_get_user_by_id_not_found(self):
        """测试根据用户ID获取用户（用户不存在）"""
        found_user = self.service.get_user_by_id("00000000-0000-0000-0000-000000000000")
        assert found_user is None
    
    def test_create_user_duplicate_email(self):
        """测试创建用户时邮箱重复"""
        # 先创建用户
        self.service.create_user(
            username="用户1",
            email="test@example.com",
            password="password123"
        )
        
        # 尝试用相同邮箱创建用户
        with pytest.raises(ValueError, match="邮箱已存在"):
            self.service.create_user(
                username="用户2",
                email="test@example.com",
                password="password456"
            )

