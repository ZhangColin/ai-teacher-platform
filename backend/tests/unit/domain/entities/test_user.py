"""
User实体单元测试
"""
import pytest
from datetime import datetime
from src.domain.entities.user import User


class TestUser:
    """User实体测试类"""

    def test_admin_can_access_all_tools(self):
        """测试管理员可以访问所有工具"""
        # Arrange
        admin = User(
            id=1,
            username="admin",
            email="admin@example.com",
            is_admin=True,
            created_at=datetime.now()
        )

        # Act & Assert
        assert admin.can_access_tool("any_tool") is True
        assert admin.can_access_tool("restricted_tool") is True

    def test_regular_user_can_access_tools(self):
        """测试普通用户权限检查（当前默认返回True）"""
        # Arrange
        user = User(
            id=2,
            username="user",
            email="user@example.com",
            is_admin=False,
            created_at=datetime.now()
        )

        # Act & Assert
        # 当前实现默认返回True，后续添加权限逻辑
        assert user.can_access_tool("public_tool") is True

    def test_is_premium_user(self):
        """测试付费用户检查（当前默认返回False）"""
        # Arrange
        user = User(
            id=3,
            username="user",
            email="user@example.com",
            is_admin=False,
            created_at=datetime.now()
        )

        # Act & Assert
        # 当前实现默认返回False，后续添加付费逻辑
        assert user.is_premium_user() is False

    def test_create_new_user_factory_method(self):
        """测试创建新用户的工厂方法"""
        # Act
        new_user = User.create_new(
            username="newuser",
            email="new@example.com"
        )

        # Assert
        assert new_user.username == "newuser"
        assert new_user.email == "new@example.com"
        assert new_user.is_admin is False
        assert new_user.id == 0  # 数据库生成
        assert isinstance(new_user.created_at, datetime)

    def test_user_dataclass_attributes(self):
        """测试User数据类属性"""
        # Arrange
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            is_admin=False,
            created_at=created_at
        )

        # Assert
        assert user.id == 1
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_admin is False
        assert user.created_at == created_at
