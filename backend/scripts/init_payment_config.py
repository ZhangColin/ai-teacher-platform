# -*- coding: utf-8 -*-
"""初始化支付系统配置

Usage:
    cd backend
    python -m scripts.init_payment_config
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import SessionLocal
from src.db_models import SystemConfigModel


def init_payment_config():
    """初始化支付系统配置"""
    db = SessionLocal()

    try:
        # 检查配置是否已存在
        existing = db.query(SystemConfigModel).filter(
            SystemConfigModel.key == "points_per_yuan"
        ).first()

        if existing:
            print(f"配置已存在: points_per_yuan = {existing.value}")
            return

        # 创建默认配置
        config = SystemConfigModel(
            key="points_per_yuan",
            value="100",
            description="1元对应的积分数量"
        )

        db.add(config)
        db.commit()

        print("支付系统配置初始化成功:")
        print("  points_per_yuan = 100 (1元 = 100积分)")

    except Exception as e:
        print(f"初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_payment_config()
