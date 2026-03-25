"""add_newapi_provider

Revision ID: 20260325_add_newapi
Revises: 0b1257162b77
Create Date: 2026-03-25 16:00:00.000000

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
revision: str = '20260325_add_newapi'
down_revision: Union[str, Sequence[str], None] = '0b1257162b77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# NewAPI 常用模型定义
NEWAPI_MODELS = {
    "gpt-4o": {"name": "GPT-4o", "capabilities": ["chat", "image", "code"]},
    "gpt-4o-mini": {"name": "GPT-4o Mini", "capabilities": ["chat", "image", "code"]},
    "gpt-4.1": {"name": "GPT-4.1", "capabilities": ["chat", "image", "code"]},
    "o3": {"name": "o3", "capabilities": ["chat", "code"]},
    "o3-mini": {"name": "o3-mini", "capabilities": ["chat", "code"]},
    "claude-opus-4.6": {"name": "Claude Opus 4.6", "capabilities": ["chat", "image", "code"]},
    "claude-sonnet-4.6": {"name": "Claude Sonnet 4.6", "capabilities": ["chat", "image", "code"]},
    "claude-haiku-4.6": {"name": "Claude Haiku 4.6", "capabilities": ["chat"]},
    "deepseek-v3": {"name": "DeepSeek V3", "capabilities": ["chat", "code"]},
    "deepseek-chat": {"name": "DeepSeek Chat", "capabilities": ["chat", "code"]},
    "deepseek-r1": {"name": "DeepSeek R1", "capabilities": ["chat", "code"]},
    "gemini-2.5-pro": {"name": "Gemini 2.5 Pro", "capabilities": ["chat", "image", "code"]},
    "gemini-2.5-flash": {"name": "Gemini 2.5 Flash", "capabilities": ["chat", "code"]},
    "glm-4.7": {"name": "GLM-4.7", "capabilities": ["chat", "code"]},
    "glm-4.6": {"name": "GLM-4.6", "capabilities": ["chat", "code"]},
}


def encrypt_api_key(plaintext: str, key: str) -> str:
    """加密 API Key"""
    cipher = Fernet(key.encode())
    return cipher.encrypt(plaintext.encode()).decode()


def upgrade() -> None:
    """Upgrade schema - 添加 NewAPI 供应商"""

    # 获取加密密钥
    encryption_key = os.getenv("API_KEY_ENCRYPTION_KEY")
    if not encryption_key:
        # 如果没有配置加密密钥，生成一个临时密钥
        encryption_key = Fernet.generate_key().decode()
        print(f"⚠️  未配置 API_KEY_ENCRYPTION_KEY，使用临时密钥")

    # 获取绑定引擎
    bind = op.get_bind()
    Session = sessionmaker(bind=bind)
    session = Session()

    try:
        # 检查 NewAPI 供应商是否已存在
        result = session.execute(
            sa.select(sa.text("*")).select_from(sa.text("model_providers")).where(
                sa.text("provider_code = 'newapi'")
            )
        )
        existing = result.fetchone()

        if existing:
            print("ℹ️  NewAPI 供应商已存在，跳过初始化")
            return

        # 获取 NewAPI 配置
        newapi_key = os.getenv("NEWAPI_API_KEY")
        newapi_base_url = os.getenv("NEWAPI_BASE_URL", "https://your-newapi-domain.com/v1")

        # 只有配置了 API Key 时才创建
        if not newapi_key or newapi_key == "sk-your-newapi-api-key-here":
            print("ℹ️  未配置 NEWAPI_API_KEY，跳过 NewAPI 供应商初始化")
            print("   如需使用 NewAPI，请在 .env 中配置 NEWAPI_API_KEY 和 NEWAPI_BASE_URL")
            return

        # 准备供应商数据
        now = datetime.now()
        provider_id = str(uuid.uuid4())
        provider_data = {
            "id": provider_id,
            "provider_code": "newapi",
            "provider_name": "NewAPI",
            "api_key_encrypted": encrypt_api_key(newapi_key, encryption_key),
            "base_url": newapi_base_url,
            "is_enabled": True,
            "is_default": False,
            "order": 10,
            "created_at": now,
            "updated_at": now,
        }

        # 插入供应商
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
        session.execute(model_providers_table.insert(), [provider_data])

        # 插入常用模型配置
        models_data = []
        for model_code, model_config in NEWAPI_MODELS.items():
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
        print(f"✅ 初始化 NewAPI 供应商和 {len(models_data)} 个常用模型配置")

    except Exception as e:
        session.rollback()
        print(f"❌ 初始化失败: {e}")
        raise
    finally:
        session.close()


def downgrade() -> None:
    """Downgrade schema - 删除 NewAPI 供应商"""

    bind = op.get_bind()

    # 删除模型配置
    op.execute("DELETE FROM model_configs WHERE provider_id IN (SELECT id FROM model_providers WHERE provider_code = 'newapi')")

    # 删除供应商
    op.execute("DELETE FROM model_providers WHERE provider_code = 'newapi'")

    print("✅ 已删除 NewAPI 供应商及相关配置")
