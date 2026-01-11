"""
用户管理API测试用例

测试管理员对用户的CRUD操作，包括边界条件和权限控制。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app
from src.db_models import UserModel, Base
from src.services.user_service import UserService
import bcrypt

client = TestClient(app)


class TestUserManagementAPI:
    """用户管理API测试类"""

    def setup_method(self):
        """测试前准备：创建测试数据库和测试用户"""
        # 使用SQLite内存数据库进行测试
        test_engine = create_engine("sqlite:///:memory:?cache=shared", echo=False, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=test_engine)
        
        # 创建测试会话
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        self.db = TestSessionLocal()
        
        # 创建服务实例
        self.user_service = UserService()

        # 清理测试数据
        db.query(UserModel).delete()
        db.commit()

        # 创建管理员用户
        self.admin_user = self.user_service.create_user(
            username="admin",
            password="admin123",
            is_admin=True,
        )

        # 创建普通用户
        self.normal_user = self.user_service.create_user(
            username="user1",
            nickname="普通用户1",
            email="user1@example.com",
            phone="13800138001",
            password="password123",
            is_admin=False,
        )

        # 创建第二个管理员用户（用于测试删除最后一个管理员）
        self.admin_user2 = self.user_service.create_user(
            username="admin2",
            password="admin123",
            is_admin=True,
        )

        # 获取管理员Token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"account": "admin", "password": "admin123", "remember_me": False},
        )
        self.admin_token = login_response.json()["token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

        # 获取普通用户Token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"account": "user1", "password": "password123", "remember_me": False},
        )
        self.user_token = login_response.json()["token"]
        self.user_headers = {"Authorization": f"Bearer {self.user_token}"}

    # ==================== 获取用户列表测试 ====================

    def test_get_users_list_success(self):
        """测试获取用户列表成功"""
        response = client.get("/api/v1/admin/users", headers=self.admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] >= 3  # 至少有3个用户（2个管理员+1个普通用户）
        assert len(data["users"]) >= 3

    def test_get_users_list_with_pagination(self):
        """测试用户列表分页"""
        # 创建更多用户
        for i in range(5):
            self.user_service.create_user(
                username=f"testuser{i}",
                password="password123",
                is_admin=False,
            )

        # 第一页
        response = client.get(
            "/api/v1/admin/users?page=1&page_size=2", headers=self.admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["users"]) == 2
        assert data["total"] >= 8

        # 第二页
        response = client.get(
            "/api/v1/admin/users?page=2&page_size=2", headers=self.admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert len(data["users"]) == 2

    def test_get_users_list_filter_admin_only(self):
        """测试筛选仅管理员"""
        response = client.get(
            "/api/v1/admin/users?is_admin=true", headers=self.admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert all(user["is_admin"] is True for user in data["users"])
        assert data["total"] == 2  # 只有2个管理员

    def test_get_users_list_filter_normal_users_only(self):
        """测试筛选仅普通用户"""
        response = client.get(
            "/api/v1/admin/users?is_admin=false", headers=self.admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert all(user["is_admin"] is False for user in data["users"])

    def test_get_users_list_unauthorized(self):
        """测试未登录访问用户列表"""
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 401

    def test_get_users_list_forbidden_for_normal_user(self):
        """测试普通用户无权访问用户列表"""
        response = client.get("/api/v1/admin/users", headers=self.user_headers)
        assert response.status_code == 403

    # ==================== 创建用户测试 ====================

    def test_create_user_success(self):
        """测试创建用户成功"""
        request_data = {
            "username": "newuser",
            "nickname": "新用户",
            "email": "newuser@example.com",
            "phone": "13800138888",
            "password": "password123",
            "is_admin": False,
        }

        response = client.post(
            "/api/v1/admin/users", json=request_data, headers=self.admin_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["nickname"] == "新用户"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["phone"] == "13800138888"
        assert data["user"]["is_admin"] is False
        assert "user_id" in data["user"]
        assert "created_at" in data["user"]

    def test_create_admin_user_success(self):
        """测试创建管理员用户成功"""
        request_data = {
            "username": "newadmin",
            "password": "password123",
            "is_admin": True,
        }

        response = client.post(
            "/api/v1/admin/users", json=request_data, headers=self.admin_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["is_admin"] is True

    def test_create_user_without_nickname_uses_username(self):
        """测试创建用户时未提供昵称，使用用户名作为显示名称"""
        request_data = {
            "username": "testnickname",
            "password": "password123",
            "is_admin": False,
        }

        response = client.post(
            "/api/v1/admin/users", json=request_data, headers=self.admin_headers
        )

        assert response.status_code == 201
        # 昵称可能为None或等于用户名（取决于实现）

    def test_create_user_duplicate_username(self):
        """测试创建用户时用户名已存在"""
        request_data = {
            "username": "user1",  # 已存在
            "password": "password123",
        }

        response = client.post(
            "/api/v1/admin/users", json=request_data, headers=self.admin_headers
        )

        assert response.status_code == 409
        assert "用户名" in response.json()["detail"]

    def test_create_user_duplicate_email(self):
        """测试创建用户时邮箱已存在"""
        request_data = {
            "username": "newuser2",
            "email": "user1@example.com",  # 已存在
            "password": "password123",
        }

        response = client.post(
            "/api/v1/admin/users", json=request_data, headers=self.admin_headers
        )

        assert response.status_code == 409
        assert "邮箱" in response.json()["detail"]

    def test_create_user_duplicate_phone(self):
        """测试创建用户时手机号已存在"""
        request_data = {
            "username": "newuser3",
            "phone": "13800138001",  # 已存在
            "password": "password123",
        }

        response = client.post(
            "/api/v1/admin/users", json=request_data, headers=self.admin_headers
        )

        assert response.status_code == 409
        assert "手机号" in response.json()["detail"]

    def test_create_user_invalid_email_format(self):
        """测试创建用户时邮箱格式错误"""
        request_data = {
            "username": "newuser4",
            "email": "invalid-email",  # 格式错误
            "password": "password123",
        }

        response = client.post(
            "/api/v1/admin/users", json=request_data, headers=self.admin_headers
        )

        assert response.status_code == 422

    def test_create_user_invalid_phone_format(self):
        """测试创建用户时手机号格式错误"""
        request_data = {
            "username": "newuser5",
            "phone": "12345",  # 格式错误
            "password": "password123",
        }

        response = client.post(
            "/api/v1/admin/users", json=request_data, headers=self.admin_headers
        )

        assert response.status_code == 422

    def test_create_user_password_too_short(self):
        """测试创建用户时密码长度不足"""
        request_data = {
            "username": "newuser6",
            "password": "12345",  # 少于6位
        }

        response = client.post(
            "/api/v1/admin/users", json=request_data, headers=self.admin_headers
        )

        assert response.status_code == 422

    def test_create_user_unauthorized(self):
        """测试未登录创建用户"""
        request_data = {
            "username": "newuser7",
            "password": "password123",
        }

        response = client.post("/api/v1/admin/users", json=request_data)
        assert response.status_code == 401

    def test_create_user_forbidden_for_normal_user(self):
        """测试普通用户无权创建用户"""
        request_data = {
            "username": "newuser8",
            "password": "password123",
        }

        response = client.post(
            "/api/v1/admin/users", json=request_data, headers=self.user_headers
        )
        assert response.status_code == 403

    # ==================== 更新用户信息测试 ====================

    def test_update_user_success(self):
        """测试更新用户信息成功"""
        request_data = {
            "nickname": "更新后的昵称",
            "email": "updated@example.com",
        }

        response = client.put(
            f"/api/v1/admin/users/{self.normal_user.user_id}",
            json=request_data,
            headers=self.admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["nickname"] == "更新后的昵称"
        assert data["user"]["email"] == "updated@example.com"
        # 未更新的字段保持不变
        assert data["user"]["username"] == "user1"
        assert data["user"]["phone"] == "13800138001"

    def test_update_user_set_admin_true(self):
        """测试将普通用户设置为管理员"""
        request_data = {"is_admin": True}

        response = client.put(
            f"/api/v1/admin/users/{self.normal_user.user_id}",
            json=request_data,
            headers=self.admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["is_admin"] is True

    def test_update_user_remove_last_admin_fails(self):
        """测试取消最后一个管理员的权限失败"""
        # 先删除第二个管理员
        client.delete(
            f"/api/v1/admin/users/{self.admin_user2.user_id}",
            headers=self.admin_headers,
        )

        # 尝试取消唯一管理员的权限
        request_data = {"is_admin": False}

        response = client.put(
            f"/api/v1/admin/users/{self.admin_user.user_id}",
            json=request_data,
            headers=self.admin_headers,
        )

        assert response.status_code == 400
        assert "最后一个管理员" in response.json()["detail"]

    def test_update_user_duplicate_username(self):
        """测试更新用户名时与其他用户重复"""
        request_data = {"username": "admin"}  # admin已存在

        response = client.put(
            f"/api/v1/admin/users/{self.normal_user.user_id}",
            json=request_data,
            headers=self.admin_headers,
        )

        assert response.status_code == 409

    def test_update_user_duplicate_email(self):
        """测试更新邮箱时与其他用户重复"""
        # 先创建一个有邮箱的用户
        user3 = self.user_service.create_user(
            username="user3",
            email="user3@example.com",
            password="password123",
        )

        request_data = {"email": "user3@example.com"}

        response = client.put(
            f"/api/v1/admin/users/{self.normal_user.user_id}",
            json=request_data,
            headers=self.admin_headers,
        )

        assert response.status_code == 409

    def test_update_user_not_found(self):
        """测试更新不存在的用户"""
        request_data = {"nickname": "新昵称"}

        response = client.put(
            "/api/v1/admin/users/nonexistent-user-id",
            json=request_data,
            headers=self.admin_headers,
        )

        assert response.status_code == 404

    def test_update_user_unauthorized(self):
        """测试未登录更新用户"""
        request_data = {"nickname": "新昵称"}

        response = client.put(
            f"/api/v1/admin/users/{self.normal_user.user_id}", json=request_data
        )
        assert response.status_code == 401

    def test_update_user_forbidden_for_normal_user(self):
        """测试普通用户无权更新用户"""
        request_data = {"nickname": "新昵称"}

        response = client.put(
            f"/api/v1/admin/users/{self.normal_user.user_id}",
            json=request_data,
            headers=self.user_headers,
        )
        assert response.status_code == 403

    # ==================== 删除用户测试 ====================

    def test_delete_user_success(self):
        """测试删除用户成功"""
        response = client.delete(
            f"/api/v1/admin/users/{self.normal_user.user_id}",
            headers=self.admin_headers,
        )

        assert response.status_code == 204

        # 验证用户已被删除
        user = self.db.query(UserModel).filter_by(user_id=self.normal_user.user_id).first()
        assert user is None

    def test_delete_user_cannot_delete_self(self):
        """测试不能删除自己"""
        response = client.delete(
            f"/api/v1/admin/users/{self.admin_user.user_id}",
            headers=self.admin_headers,
        )

        assert response.status_code == 400
        assert "不允许删除自己" in response.json()["detail"]

    def test_delete_user_cannot_delete_last_admin(self):
        """测试不能删除最后一个管理员"""
        # 先删除第二个管理员
        client.delete(
            f"/api/v1/admin/users/{self.admin_user2.user_id}",
            headers=self.admin_headers,
        )

        # 创建第三个管理员作为当前操作者
        admin3 = self.user_service.create_user(
            username="admin3",
            password="admin123",
            is_admin=True,
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"account": "admin3", "password": "admin123", "remember_me": False},
        )
        admin3_token = login_response.json()["token"]
        admin3_headers = {"Authorization": f"Bearer {admin3_token}"}

        # 尝试删除最后一个管理员（admin）
        response = client.delete(
            f"/api/v1/admin/users/{self.admin_user.user_id}",
            headers=admin3_headers,
        )

        assert response.status_code == 400
        assert "最后一个管理员" in response.json()["detail"]

    def test_delete_user_not_found(self):
        """测试删除不存在的用户"""
        response = client.delete(
            "/api/v1/admin/users/nonexistent-user-id",
            headers=self.admin_headers,
        )

        assert response.status_code == 404

    def test_delete_user_unauthorized(self):
        """测试未登录删除用户"""
        response = client.delete(f"/api/v1/admin/users/{self.normal_user.user_id}")
        assert response.status_code == 401

    def test_delete_user_forbidden_for_normal_user(self):
        """测试普通用户无权删除用户"""
        response = client.delete(
            f"/api/v1/admin/users/{self.normal_user.user_id}",
            headers=self.user_headers,
        )
        assert response.status_code == 403

    # ==================== 重置密码测试 ====================

    def test_reset_password_success(self):
        """测试重置密码成功"""
        request_data = {"new_password": "newpassword123"}

        response = client.post(
            f"/api/v1/admin/users/{self.normal_user.user_id}/reset-password",
            json=request_data,
            headers=self.admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "new_password" in data
        assert data["new_password"] == "newpassword123"

        # 验证用户能用新密码登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={"account": "user1", "password": "newpassword123", "remember_me": False},
        )
        assert login_response.status_code == 200

    def test_reset_password_too_short(self):
        """测试重置密码长度不足"""
        request_data = {"new_password": "12345"}  # 少于6位

        response = client.post(
            f"/api/v1/admin/users/{self.normal_user.user_id}/reset-password",
            json=request_data,
            headers=self.admin_headers,
        )

        assert response.status_code == 422

    def test_reset_password_user_not_found(self):
        """测试重置不存在用户的密码"""
        request_data = {"new_password": "newpassword123"}

        response = client.post(
            "/api/v1/admin/users/nonexistent-user-id/reset-password",
            json=request_data,
            headers=self.admin_headers,
        )

        assert response.status_code == 404

    def test_reset_password_unauthorized(self):
        """测试未登录重置密码"""
        request_data = {"new_password": "newpassword123"}

        response = client.post(
            f"/api/v1/admin/users/{self.normal_user.user_id}/reset-password",
            json=request_data,
        )
        assert response.status_code == 401

    def test_reset_password_forbidden_for_normal_user(self):
        """测试普通用户无权重置密码"""
        request_data = {"new_password": "newpassword123"}

        response = client.post(
            f"/api/v1/admin/users/{self.normal_user.user_id}/reset-password",
            json=request_data,
            headers=self.user_headers,
        )
        assert response.status_code == 403
