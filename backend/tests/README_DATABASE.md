# -*- coding: utf-8 -*-
"""
pytest 测试数据库配置说明

本测试套件支持两种数据库模式：
1. 内存 SQLite 模式（快速，用于单元测试）
2. MySQL 测试数据库模式（真实环境，用于集成测试）

=====================================================
模式1：内存 SQLite（默认，单元测试）
=====================================================

运行方式：
    pytest tests/unit/ --mock-db

特点：
- ✅ 快速：不需要外部数据库
- ✅ 隔离：每个测试独立数据库
- ✅ 并行：测试可以并行运行
- ⚠️ 限制：不支持 MySQL 特有功能

=====================================================
模式2：MySQL 测试数据库（集成测试）
=====================================================

首次运行前需要设置：

1. 创建测试数据库：
   cd backend
   chmod +x scripts/setup_test_db.sh
   ./scripts/setup_test_db.sh

2. 运行测试：
   pytest tests/integration/

特点：
- ✅ 真实环境：与生产环境一致
- ✅ 完整功能：支持所有 MySQL 特性
- ⚠️ 需要外部数据库
- ⚠️ 串行：测试需要串行运行

=====================================================
数据库隔离保证
=====================================================

✅ 测试数据库：ai_teacher_platform_test（独立）
✅ 开发数据库：ai_teacher_platform（不会被测试影响）
✅ 生产数据库：完全隔离

每次测试运行时：
- 单元测试：每个测试函数使用全新的内存数据库
- 集成测试：使用 pytest-testdb 插件自动回滚事务

=====================================================
环境变量配置
=====================================================

测试环境配置文件：backend/.env.test

必须设置：
    DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/ai_teacher_platform_test

可选设置：
    JWT_SECRET_KEY=测试密钥
    CURRENT_PROVIDER=mock

=====================================================
运行示例
=====================================================

# 运行所有单元测试（使用内存 SQLite）
pytest tests/unit/ --mock-db

# 运行集成测试（使用 MySQL 测试数据库）
pytest tests/integration/

# 运行所有测试
pytest tests/ --mock-db

# 查看测试覆盖率
pytest --cov=backend/src --cov-report=html
"""
import os
import sys
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 标记：是否使用内存数据库
USE_MEMORY_DB = False

def pytest_configure(config):
    """
    pytest 配置钩子
    在测试运行前被调用
    """
    global USE_MEMORY_DB

    # 检查是否使用 --mock-db 标记
    USE_MEMORY_DB = config.getoption("--mock-db") or config.getoption("-m") == "unit"

    if USE_MEMORY_DB:
        # 单元测试模式：使用内存 SQLite
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        print("\n🧪 使用内存 SQLite 数据库（单元测试模式）")
    else:
        # 集成测试模式：加载 .env.test
        env_test_file = backend_dir / ".env.test"
        if env_test_file.exists():
            # 读取并设置环境变量
            with open(env_test_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
            print(f"\n🗄️  使用测试数据库: {os.getenv('DATABASE_URL', '未设置')}")
        else:
            print("\n⚠️  警告：.env.test 不存在，使用默认配置")
            os.environ.setdefault('DATABASE_URL', 'mysql+pymysql://root:password@localhost:3306/ai_teacher_platform_test?charset=utf8mb4')


def pytest_addoption(parser):
    """添加自定义命令行选项"""
    parser.addoption(
        "--mock-db",
        action="store_true",
        default=False,
        help="使用内存 SQLite 数据库（用于单元测试）"
    )
