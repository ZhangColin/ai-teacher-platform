#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型配置更新脚本

根据 builtin_models.py 中的最新配置更新数据库中的模型列表。
此脚本会删除所有现有的模型配置，然后根据 BUILTIN_MODELS 重新创建。
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db_models import Base, ModelProviderModel, ModelConfigModel
from src.services.encryption_service import EncryptionService
from src.services.builtin_models import BUILTIN_PROVIDERS, BUILTIN_MODELS


def get_database_url():
    """获取数据库 URL"""
    return os.getenv("DATABASE_URL", "mysql+pymysql://root:truth@localhost:3306/hcy_studio?charset=utf8mb4")


def update_model_configs():
    """更新模型配置"""
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()
    encryption_service = EncryptionService()

    try:
        # 检查现有配置
        existing_providers = session.query(ModelProviderModel).all()
        if not existing_providers:
            print("⚠️  数据库中没有供应商配置，请先运行 init_model_providers.py")
            return

        print(f"📊 找到 {len(existing_providers)} 个供应商配置")
        print("\n将要删除所有现有的模型配置并重新创建...")
        response = input("是否继续？(yes/no): ")
        if response.lower() != "yes":
            print("❌ 取消更新")
            return

        # 删除所有现有的模型配置
        deleted_count = session.query(ModelConfigModel).delete()
        session.commit()
        print(f"🗑️  已删除 {deleted_count} 个模型配置")

        # 重新创建模型配置
        created_count = 0
        for provider in existing_providers:
            provider_code = provider.provider_code
            if provider_code not in BUILTIN_MODELS:
                print(f"⚠️  跳过未知供应商: {provider_code}")
                continue

            print(f"\n📝 更新供应商: {provider.provider_name} ({provider_code})")

            for model_code, model_config in BUILTIN_MODELS[provider_code].items():
                model = ModelConfigModel(
                    provider_id=provider.id,
                    model_code=model_code,
                    model_name=model_config["name"],
                    capabilities=",".join(model_config["capabilities"]),
                    is_enabled=True,
                )
                session.add(model)
                created_count += 1
                print(f"   ➜ 添加模型: {model_config['name']} ({model_code})")

        session.commit()
        print(f"\n🎉 模型配置更新完成！")
        print(f"📊 共创建 {created_count} 个模型配置")

        # 显示最终统计
        total_providers = session.query(ModelProviderModel).count()
        total_models = session.query(ModelConfigModel).count()
        print(f"📊 数据库中共有 {total_providers} 个供应商，{total_models} 个模型")

    except Exception as e:
        session.rollback()
        print(f"❌ 更新失败: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 50)
    print("模型配置更新")
    print("=" * 50)
    update_model_configs()
