# -*- coding: utf-8 -*-
"""测试用户列表API

TDD流程：先写失败的测试，再修复代码
"""
import pytest
import bcrypt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.database import get_db, Base
from src.db_models import UserModel

# 使用内存数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_users_list.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """测试数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# 重写数据库依赖
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """设置测试数据库"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # 清理测试数据库文件
    import os
    if os.path.exists(SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")):
        os.remove(SQLALCHEMY_DATABASE_URL.replace("sqlite:///", ""))


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


@pytest.fixture
def admin_client(client):
    """创建已登录的管理员客户端"""
    # 使用 bcrypt 生成密码哈希
    password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    db = TestingSessionLocal()
    admin = UserModel(
        username="admin_test",
        password_hash=password_hash,
        nickname="管理员",
        email="admin@test.com",
        is_admin=True
    )
    db.add(admin)
    db.commit()
    db.close()

    # 登录获取token
    response = client.post("/api/v1/auth/login", json={
        "account": "admin_test",
        "password": "admin123"
    })
    token = response.json()["token"]

    # 返回带认证头的客户端
    client.headers["Authorization"] = f"Bearer {token}"
    return client


def test_get_user_list_as_admin(admin_client):
    """测试管理员获取用户列表 - 应该返回200而不是500"""
    # 这个请求应该成功，不应该返回500错误
    response = admin_client.get("/api/v1/admin/users")

    # 断言：应该返回200 OK
    assert response.status_code == 200, f"期望200，实际{response.status_code}，响应: {response.text}"

    # 断言：返回正确的数据结构
    data = response.json()
    assert "users" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data

    # 应该至少有一个管理员用户
    assert len(data["users"]) >= 1
    assert data["total"] >= 1

    # 额外测试分页参数
    response2 = admin_client.get("/api/v1/admin/users?page=1&page_size=10")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["page"] == 1
    assert data2["page_size"] == 10
