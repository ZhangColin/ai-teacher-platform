# -*- coding: utf-8 -*-
"""pytest统一配置和fixtures"""
import sys
from pathlib import Path

# 添加backend目录到Python路径，确保无论从哪个目录运行都能找到src模块
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, AsyncGenerator
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from src.database import Base
from src.main import app
from src.db_models import UserModel


# ==================== 数据库 Fixtures ====================

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    统一的数据库会话fixture
    - 使用内存SQLite
    - 每个测试函数独立数据库
    - 自动清理
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


# ==================== HTTP Client Fixtures ====================

@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    异步HTTP客户端（用于FastAPI集成测试）
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


# ==================== 认证 Fixtures ====================

@pytest.fixture(scope="function")
def test_user(db_session: Session) -> UserModel:
    """创建测试用户（非管理员）"""
    from src.services.auth_service import AuthService

    user = UserModel(
        username="testuser",
        email="test@example.com",
        hashed_password=AuthService.hash_password("password123"),
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_user(db_session: Session) -> UserModel:
    """创建测试管理员用户"""
    from src.services.auth_service import AuthService

    user = UserModel(
        username="admin",
        email="admin@example.com",
        hashed_password=AuthService.hash_password("admin123"),
        is_admin=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user: UserModel) -> dict:
    """普通用户认证头"""
    from src.services.auth_service import AuthService
    token = AuthService.generate_token(user_id=test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_headers(admin_user: UserModel) -> dict:
    """管理员认证头"""
    from src.services.auth_service import AuthService
    token = AuthService.generate_token(user_id=admin_user.id)
    return {"Authorization": f"Bearer {token}"}


# ==================== AI Provider Mock Fixtures ====================

@pytest.fixture(scope="function")
def mock_openai_provider():
    """Mock OpenAI Provider（用于单元测试）"""
    from src.infrastructure.providers.openai_provider import OpenAIProvider

    provider = OpenAIProvider(api_key="test-key")

    # Mock客户端
    provider._client = AsyncMock()

    return provider


@pytest.fixture(scope="function")
def mock_deepseek_provider():
    """Mock DeepSeek Provider（用于单元测试）"""
    from src.infrastructure.providers.deepseek_provider import DeepSeekProvider

    provider = DeepSeekProvider(api_key="test-key")

    # Mock客户端
    provider._client = AsyncMock()

    return provider
