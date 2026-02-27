"""pytest配置文件"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from src.database import Base


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    数据库会话fixture（内存SQLite）

    用于新编写的DDD测试
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


def pytest_configure(config):
    """
    配置自定义pytest标记

    标记已在pytest.ini中定义，此处保留函数用于未来扩展
    """
    pass
