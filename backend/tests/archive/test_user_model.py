"""User实体类单元测试"""
import pytest
import uuid
from datetime import datetime
from src.models import User


class TestUser:
    """User实体类测试"""
    
    def test_create_user_with_password_encryption(self):
        """测试创建用户时密码自动加密"""
        user = User.create(
            username="测试用户",
            email="test@example.com",
            password="password123"
        )
        
        # 验证用户属性
        assert user.username == "测试用户"
        assert user.email == "test@example.com"
        assert user.password_hash != "password123"  # 密码应该被加密
        assert len(user.password_hash) > 0  # 应该有加密后的哈希值
        assert user.user_id is not None  # 应该有用户ID
        assert isinstance(user.user_id, str)  # 用户ID应该是字符串（UUID）
        assert user.avatar is None  # 默认头像为None
        assert user.created_at is not None  # 应该有创建时间
    
    def test_create_user_with_avatar(self):
        """测试创建用户时指定头像"""
        user = User.create(
            username="测试用户",
            email="test@example.com",
            password="password123",
            avatar="https://example.com/avatar.jpg"
        )
        
        assert user.avatar == "https://example.com/avatar.jpg"
    
    def test_verify_password_correct(self):
        """测试验证正确密码"""
        user = User.create(
            username="测试用户",
            email="test@example.com",
            password="password123"
        )
        
        assert user.verify_password("password123") is True
    
    def test_verify_password_incorrect(self):
        """测试验证错误密码"""
        user = User.create(
            username="测试用户",
            email="test@example.com",
            password="password123"
        )
        
        assert user.verify_password("wrong_password") is False
    
    def test_user_id_is_uuid(self):
        """测试用户ID是有效的UUID格式"""
        user = User.create(
            username="测试用户",
            email="test@example.com",
            password="password123"
        )
        
        # 验证UUID格式
        try:
            uuid.UUID(user.user_id)
        except ValueError:
            pytest.fail("user_id应该是有效的UUID格式")
    
    def test_password_hash_is_different_for_same_password(self):
        """测试相同密码生成不同的哈希值（bcrypt的salt机制）"""
        user1 = User.create(
            username="用户1",
            email="user1@example.com",
            password="password123"
        )
        
        user2 = User.create(
            username="用户2",
            email="user2@example.com",
            password="password123"
        )
        
        # 相同密码应该生成不同的哈希值（因为bcrypt使用随机salt）
        assert user1.password_hash != user2.password_hash
        # 但都能验证通过
        assert user1.verify_password("password123") is True
        assert user2.verify_password("password123") is True

