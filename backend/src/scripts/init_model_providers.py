#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型供应商配置初始化脚本

将原来通过环境变量配置的模型供应商初始化到数据库中。
在生产环境部署时，可以直接配置数据库中的供应商，无需再配置环境变量。
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


def init_model_providers():
    """初始化模型供应商配置"""
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()
    encryption_service = EncryptionService()

    try:
        # 检查是否已经有配置
        existing_count = session.query(ModelProviderModel).count()
        if existing_count > 0:
            print(f"⚠️  数据库中已有 {existing_count} 个供应商配置")
            response = input("是否要清空并重新初始化？(yes/no): ")
            if response.lower() != "yes":
                print("❌ 取消初始化")
                return

            # 清空现有配置
            session.query(ModelConfigModel).delete()
            session.query(ModelProviderModel).delete()
            session.commit()
            print("🗑️  已清空现有配置")

        # 从环境变量获取配置
        configs = []

        # DeepSeek 配置（当前使用的）
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key and deepseek_key != "sk-your-deepseek-api-key-here":
            configs.append({
                "code": "deepseek",
                "name": "DeepSeek",
                "api_key": deepseek_key,
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                "is_default": os.getenv("CURRENT_PROVIDER") == "deepseek",
                "order": 1,
            })

        # Kimi 配置
        kimi_key = os.getenv("KIMI_API_KEY")
        if kimi_key and kimi_key != "sk-your-kimi-api-key-here":
            configs.append({
                "code": "kimi",
                "name": "Kimi (Moonshot)",
                "api_key": kimi_key,
                "base_url": os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1"),
                "is_default": os.getenv("CURRENT_PROVIDER") == "kimi",
                "order": 2,
            })

        # GLM 配置
        glm_key = os.getenv("GLM_API_KEY")
        if glm_key and glm_key != "sk-your-glm-api-key-here":
            configs.append({
                "code": "glm",
                "name": "智谱 AI",
                "api_key": glm_key,
                "base_url": os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
                "is_default": os.getenv("CURRENT_PROVIDER") == "glm",
                "order": 3,
            })

        # OpenAI 配置
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key != "sk-your-openai-api-key-here":
            configs.append({
                "code": "openai",
                "name": "OpenAI",
                "api_key": openai_key,
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "is_default": os.getenv("CURRENT_PROVIDER") == "openai",
                "order": 4,
            })

        if not configs:
            print("⚠️  未找到有效的 API Key 配置，请在 .env 文件中配置以下变量：")
            print("   - DEEPSEEK_API_KEY")
            print("   - KIMI_API_KEY")
            print("   - GLM_API_KEY")
            print("   - OPENAI_API_KEY")
            return

        # 如果没有设置默认供应商，将第一个设为默认
        if not any(c["is_default"] for c in configs):
            configs[0]["is_default"] = True

        # 创建供应商配置
        for config in configs:
            # 检查是否是内置供应商
            if config["code"] not in BUILTIN_PROVIDERS:
                print(f"⚠️  跳过未知供应商: {config['code']}")
                continue

            # 创建供应商
            provider = ModelProviderModel(
                provider_code=config["code"],
                provider_name=config["name"],
                api_key_encrypted=encryption_service.encrypt(config["api_key"]),
                base_url=config["base_url"],
                is_enabled=True,
                is_default=config["is_default"],
                order=config["order"],
            )
            session.add(provider)
            session.flush()  # 获取 ID

            print(f"✅ 创建供应商: {config['name']} ({config['code']})")

            # 创建该供应商的模型配置
            if config["code"] in BUILTIN_MODELS:
                for model_code, model_config in BUILTIN_MODELS[config["code"]].items():
                    model = ModelConfigModel(
                        provider_id=provider.id,
                        model_code=model_code,
                        model_name=model_config["name"],
                        capabilities=",".join(model_config["capabilities"]),
                        is_enabled=True,
                    )
                    session.add(model)
                    print(f"   ➜ 添加模型: {model_config['name']} ({model_code})")

        session.commit()
        print("\n🎉 模型供应商配置初始化完成！")

        # 显示摘要
        total_providers = session.query(ModelProviderModel).count()
        total_models = session.query(ModelConfigModel).count()
        print(f"📊 共初始化 {total_providers} 个供应商，{total_models} 个模型")

    except Exception as e:
        session.rollback()
        print(f"❌ 初始化失败: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 50)
    print("模型供应商配置初始化")
    print("=" * 50)
    init_model_providers()
