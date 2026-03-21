"""init_model_providers

Revision ID: 705c676a8b9f
Revises: 4a83ebad1439
Create Date: 2026-03-21 11:36:30.039064

"""
from typing import Sequence, Union
import os
import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet


# revision identifiers, used by Alembic.
revision: str = '705c676a8b9f'
down_revision: Union[str, Sequence[str], None] = '4a83ebad1439'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 内置模型定义（与 builtin_models.py 保持一致）
BUILTIN_MODELS = {
    "deepseek": {
        "deepseek-chat": {"name": "DeepSeek Chat", "capabilities": ["chat"]},
        "deepseek-coder": {"name": "DeepSeek Coder", "capabilities": ["chat"]},
    },
    "openai": {
        "gpt-4": {"name": "GPT-4", "capabilities": ["chat"]},
        "gpt-4o": {"name": "GPT-4o", "capabilities": ["chat", "image"]},
    },
    "kimi": {
        "moonshot-v1-8k": {"name": "Moonshot v1 8K", "capabilities": ["chat"]},
    },
    "glm": {
        "glm-4": {"name": "GLM-4", "capabilities": ["chat"]},
        "glm-4-voice": {"name": "GLM-4 Voice", "capabilities": ["audio"]},
        "cogview-4": {"name": "CogView-4", "capabilities": ["image"]},
        "cogvideox": {"name": "CogVideoX", "capabilities": ["video"]},
    },
}


def encrypt_api_key(plaintext: str, key: str) -> str:
    """加密 API Key"""
    cipher = Fernet(key.encode())
    return cipher.encrypt(plaintext.encode()).decode()


def upgrade() -> None:
    """Upgrade schema - 初始化模型供应商配置"""

    # 获取加密密钥
    encryption_key = os.getenv("API_KEY_ENCRYPTION_KEY")
    if not encryption_key:
        # 如果没有配置加密密钥，生成一个临时密钥
        encryption_key = Fernet.generate_key().decode()
        print(f"⚠️  未配置 API_KEY_ENCRYPTION_KEY，使用临时密钥: {encryption_key}")

    # 获取当前默认供应商
    current_provider = os.getenv("CURRENT_PROVIDER", "deepseek")

    # 获取绑定引擎
    bind = op.get_bind()
    Session = sessionmaker(bind=bind)
    session = Session()

    try:
        # 准备供应商配置列表
        providers_data = []

        # DeepSeek 配置
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key and deepseek_key != "sk-your-deepseek-api-key-here":
            providers_data.append({
                "id": str(uuid.uuid4()),
                "provider_code": "deepseek",
                "provider_name": "DeepSeek",
                "api_key_encrypted": encrypt_api_key(deepseek_key, encryption_key),
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                "is_enabled": True,
                "is_default": current_provider == "deepseek",
                "order": 1,
            })

        # Kimi 配置
        kimi_key = os.getenv("KIMI_API_KEY")
        if kimi_key and kimi_key != "sk-your-kimi-api-key-here":
            providers_data.append({
                "id": str(uuid.uuid4()),
                "provider_code": "kimi",
                "provider_name": "Kimi (Moonshot)",
                "api_key_encrypted": encrypt_api_key(kimi_key, encryption_key),
                "base_url": os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1"),
                "is_enabled": True,
                "is_default": current_provider == "kimi",
                "order": 2,
            })

        # GLM 配置
        glm_key = os.getenv("GLM_API_KEY")
        if glm_key and glm_key != "sk-your-glm-api-key-here":
            providers_data.append({
                "id": str(uuid.uuid4()),
                "provider_code": "glm",
                "provider_name": "智谱 AI",
                "api_key_encrypted": encrypt_api_key(glm_key, encryption_key),
                "base_url": os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
                "is_enabled": True,
                "is_default": current_provider == "glm",
                "order": 3,
            })

        # OpenAI 配置
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key != "sk-your-openai-api-key-here":
            providers_data.append({
                "id": str(uuid.uuid4()),
                "provider_code": "openai",
                "provider_name": "OpenAI",
                "api_key_encrypted": encrypt_api_key(openai_key, encryption_key),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "is_enabled": True,
                "is_default": current_provider == "openai",
                "order": 4,
            })

        # 如果没有找到任何配置，至少创建一个示例配置
        if not providers_data:
            print("⚠️  未找到有效的 API Key 配置，跳过初始化")
            return

        # 确保有一个默认供应商
        if not any(p["is_default"] for p in providers_data):
            providers_data[0]["is_default"] = True

        # 插入供应商数据
        now = datetime.now()
        for provider_data in providers_data:
            provider_data["created_at"] = now
            provider_data["updated_at"] = now

        # 使用批量插入
        model_providers_table = sa.table(
            "model_providers",
            sa.column("id", sa.CHAR(36)),
            sa.column("provider_code", sa.String(50)),
            sa.column("provider_name", sa.String(100)),
            sa.column("api_key_encrypted", sa.Text),
            sa.column("base_url", sa.String(500)),
            sa.column("is_enabled", sa.Boolean),
            sa.column("is_default", sa.Boolean),
            sa.column("order", sa.Integer),
            sa.column("created_at", sa.DateTime),
            sa.column("updated_at", sa.DateTime),
        )
        session.execute(model_providers_table.insert(), providers_data)

        # 获取插入的供应商 ID 映射
        provider_ids = {}
        result = session.execute(
            sa.select(
                model_providers_table.c.id,
                model_providers_table.c.provider_code
            )
        )
        for row in result:
            provider_ids[row.provider_code] = row.id

        # 插入模型配置数据
        models_data = []
        for provider_code, models in BUILTIN_MODELS.items():
            if provider_code not in provider_ids:
                continue
            provider_id = provider_ids[provider_code]

            for model_code, model_config in models.items():
                models_data.append({
                    "id": str(uuid.uuid4()),
                    "provider_id": provider_id,
                    "model_code": model_code,
                    "model_name": model_config["name"],
                    "capabilities": ",".join(model_config["capabilities"]),
                    "is_enabled": True,
                    "created_at": now,
                    "updated_at": now,
                })

        # 批量插入模型配置
        if models_data:
            model_configs_table = sa.table(
                "model_configs",
                sa.column("id", sa.CHAR(36)),
                sa.column("provider_id", sa.CHAR(36)),
                sa.column("model_code", sa.String(50)),
                sa.column("model_name", sa.String(100)),
                sa.column("capabilities", sa.String(50)),
                sa.column("is_enabled", sa.Boolean),
                sa.column("created_at", sa.DateTime),
                sa.column("updated_at", sa.DateTime),
            )
            session.execute(model_configs_table.insert(), models_data)

        session.commit()
        print(f"✅ 初始化了 {len(providers_data)} 个供应商和 {len(models_data)} 个模型配置")

    except Exception as e:
        session.rollback()
        print(f"❌ 初始化失败: {e}")
        raise
    finally:
        session.close()


def downgrade() -> None:
    """Downgrade schema - 删除初始化的数据"""

    bind = op.get_bind()

    # 删除模型配置
    op.execute("DELETE FROM model_configs WHERE provider_id IN (SELECT id FROM model_providers WHERE provider_code IN ('deepseek', 'kimi', 'glm', 'openai'))")

    # 删除供应商
    op.execute("DELETE FROM model_providers WHERE provider_code IN ('deepseek', 'kimi', 'glm', 'openai')")
