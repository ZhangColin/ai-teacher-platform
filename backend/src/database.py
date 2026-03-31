"""数据库配置和连接管理"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取数据库连接字符串
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:password@localhost:3306/ai_teacher_platform?charset=utf8mb4"
)

# 创建数据库引擎
# 生产环境配置：支持最高 150 并发连接（50 pool_size + 100 max_overflow）
# 超过 150 并发时，新请求会等待最多 60 秒获取连接
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,     # 连接前检查连接是否有效
    pool_recycle=3600,      # 连接回收时间（秒），防止 MySQL 连接超时（默认 8 小时）
    pool_size=50,           # 连接池核心大小，保持常开的连接数
    max_overflow=100,       # 最大溢出连接数，超出 pool_size 后临时创建的最大连接数
    pool_timeout=60,        # 获取连接超时时间（秒），当连接池满时等待的时间
    echo=False              # 是否打印SQL语句（开发时可设为True）
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类，用于定义数据模型
Base = declarative_base()


def get_db():
    """获取数据库会话（用于依赖注入）"""
    db = SessionLocal()
    try:
        yield db
        # 操作成功，提交事务
        db.commit()
    except Exception:
        # 发生异常，回滚事务
        db.rollback()
        raise
    finally:
        db.close()

