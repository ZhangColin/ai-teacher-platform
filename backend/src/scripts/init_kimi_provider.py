# -*- coding: utf-8 -*-
"""
Kimi 供应商初始化脚本

运行此脚本在数据库中创建 Kimi 供应商配置
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from sqlalchemy.orm import Session
from src.database import engine
from src.db_models import ModelProviderModel, ModelConfigModel
from datetime import datetime


def init_kimi_provider(db: Session):
    """初始化 Kimi 供应商配置"""

    # 检查是否已存在
    existing = db.query(ModelProviderModel).filter(
        ModelProviderModel.provider_code == "kimi"
    ).first()

    if existing:
        print("Kimi 供应商已存在，跳过创建")
        return existing.id

    # 创建供应商
    provider = ModelProviderModel(
        provider_code="kimi",
        provider_name="Moonshot AI (Kimi)",
        api_key_encrypted="",  # 用户在后台填入
        base_url="https://api.moonshot.cn",
        is_enabled=False,  # 默认禁用，用户配置后启用
        is_default=False,
        order=3,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(provider)
    db.flush()  # 获取 provider.id

    # 创建模型配置
    models = [
        {
            "model_code": "moonshot-v1-8k",
            "model_name": "Kimi 8K",
            "capabilities": "chat,file,image"
        },
        {
            "model_code": "moonshot-v1-32k",
            "model_name": "Kimi 32K",
            "capabilities": "chat,file,image"
        },
        {
            "model_code": "moonshot-v1-128k",
            "model_name": "Kimi 128K",
            "capabilities": "chat,file,image"
        },
    ]

    for model_config in models:
        model = ModelConfigModel(
            provider_id=provider.id,
            model_code=model_config["model_code"],
            model_name=model_config["model_name"],
            capabilities=model_config["capabilities"],
            is_enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(model)

    db.commit()

    print(f"Kimi 供应商创建成功: {provider.id}")
    print(f"  - 已创建 {len(models)} 个模型配置")
    print("  - 请在管理后台配置 API Key 后启用")

    return provider.id


if __name__ == "__main__":
    from src.database import SessionLocal

    db = SessionLocal()
    try:
        init_kimi_provider(db)
        print("\n初始化完成！")
    except Exception as e:
        print(f"初始化失败: {e}")
        db.rollback()
    finally:
        db.close()
