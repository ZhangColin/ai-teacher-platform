"""Test admin permission functionality"""
import pytest
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database import Base
from src.db_models import UserModel
from src.services.user_service import UserService
from src.models import User


class TestAdminPermission:
    """Test admin permission related features"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        # Create test database
        test_engine = create_engine("sqlite:///:memory:?cache=shared", echo=False)
        Base.metadata.create_all(bind=test_engine)
        
        # Create test session maker
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        # Inject test database session
        from src import database
        self.original_session_local = database.SessionLocal
        database.SessionLocal = TestSessionLocal
        
        self.service = UserService()
    
    def teardown_method(self):
        """Cleanup after each test"""
        from src import database
        database.SessionLocal = self.original_session_local
    
    def test_create_admin_user(self):
        """Test creating admin user"""
        # Create admin user
        admin_user = self.service.create_user(
            username="admin_test",
            password="password123",
            email="admin@test.com",
            is_admin=True
        )
        
        assert admin_user.user_id is not None
        assert admin_user.username == "admin_test"
        assert admin_user.is_admin is True
        assert admin_user.is_administrator() is True
    
    def test_create_normal_user(self):
        """Test creating normal user (default is_admin=False)"""
        # Create normal user
        normal_user = self.service.create_user(
            username="normal_test",
            password="password123",
            email="normal@test.com"
        )
        
        assert normal_user.user_id is not None
        assert normal_user.username == "normal_test"
        assert normal_user.is_admin is False
        assert normal_user.is_administrator() is False
    
    def test_user_entity_is_administrator_method(self):
        """Test User entity's is_administrator method"""
        # Create admin user entity
        admin_user = User.create(
            username="admin",
            password="password123",
            email="admin@test.com",
            is_admin=True
        )
        assert admin_user.is_administrator() is True
        
        # Create normal user entity
        normal_user = User.create(
            username="normal",
            password="password123",
            email="normal@test.com",
            is_admin=False
        )
        assert normal_user.is_administrator() is False
