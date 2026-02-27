"""pytest配置文件"""
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import AsyncGenerator, Generator

from src.database import Base


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """
    创建内存数据库用于测试

    使用内存数据库，每个测试函数都会获得一个全新的数据库
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    # 创建所有表
    Base.metadata.create_all(engine)

    # 创建Session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    # 清理
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def event_loop() -> asyncio.AbstractEventLoop:
    """
    为异步测试创建事件循环
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    """
    配置自定义pytest标记
    """
    config.addinivalue_line(
        "markers", "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试标记"
    )
