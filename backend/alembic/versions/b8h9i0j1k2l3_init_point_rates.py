"""init_model_point_rates

初始化模型积分汇率配置

定价参考 (2026年3月):
- DeepSeek: $0.345/M tokens (基准)
- Kimi: $1.375/M tokens (~4x)
- GLM-4: $1.40/M tokens (~4.1x)
- GPT-4o: $6.25/M tokens (~18x)

汇率规则:
- 1 元 = 100 积分
- DeepSeek 基准: 1000 tokens = 100 积分 (1 积分 = 10 tokens)

Revision ID: b8h9i0j1k2l3_init_point_rates
Revises: 20260323_init_hcy
Create Date: 2026-03-23

"""
from typing import Sequence, Union
import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = 'b8h9i0j1k2l3'
down_revision: Union[str, Sequence[str], None] = 'ef3a319b300c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 模型汇率配置数据
# tokens_per_point: 每积分对应的 token 数
# 计算逻辑: DeepSeek 10 tokens/积分，其他模型按价格比例调整
MODEL_POINT_RATES = {
    # DeepSeek 系列 (基准: 10 tokens/积分)
    "deepseek-chat": {
        "tokens_per_point": 10,
        "description": "DeepSeek Chat - 基准模型"
    },
    "deepseek-coder": {
        "tokens_per_point": 10,
        "description": "DeepSeek Coder - 代码生成"
    },

    # Kimi 系列 (约 4x 价格 → 2.5 tokens/积分)
    "moonshot-v1-8k": {
        "tokens_per_point": 2,
        "description": "Kimi Moonshot v1 8K"
    },

    # GLM 系列 (约 4x 价格 → 2.5 tokens/积分)
    "glm-4": {
        "tokens_per_point": 2,
        "description": "智谱 GLM-4"
    },
    "glm-4-voice": {
        "tokens_per_point": 2,
        "description": "智谱 GLM-4 Voice"
    },
    "cogview-4": {
        "tokens_per_point": 2,
        "description": "智谱 CogView-4 图像生成"
    },
    "cogvideox": {
        "tokens_per_point": 2,
        "description": "智谱 CogVideoX 视频生成"
    },

    # GPT 系列 (GPT-4o 约 18x 价格 → 0.5 tokens/积分)
    "gpt-4": {
        "tokens_per_point": 1,
        "description": "OpenAI GPT-4"
    },
    "gpt-4o": {
        "tokens_per_point": 1,
        "description": "OpenAI GPT-4o (多模态)"
    },
}


def upgrade() -> None:
    """Upgrade schema - 初始化模型积分汇率配置"""

    bind = op.get_bind()
    Session = sessionmaker(bind=bind)
    session = Session()

    try:
        # 获取所有模型配置
        model_configs_table = table('model_configs',
            column('id', sa.CHAR(36)),
            column('provider_id', sa.CHAR(36)),
            column('model_code', sa.String(50)),
            column('model_name', sa.String(100)),
            column('is_enabled', sa.Boolean),
        )

        model_providers_table = table('model_providers',
            column('id', sa.CHAR(36)),
            column('provider_code', sa.String(50)),
        )

        # 查询所有模型配置
        result = session.execute(
            sa.select(
                model_configs_table.c.id,
                model_configs_table.c.model_code,
                model_providers_table.c.provider_code,
            ).select_from(
                model_configs_table.join(
                    model_providers_table,
                    model_configs_table.c.provider_id == model_providers_table.c.id
                )
            ).where(
                model_configs_table.c.is_enabled == True
            )
        )

        models_map = {row.model_code: (row.id, row.provider_code) for row in result}

        # 准备汇率配置数据
        point_rates_data = []
        now = datetime.now()

        for model_code, rate_config in MODEL_POINT_RATES.items():
            if model_code not in models_map:
                print(f"⚠️  模型 {model_code} 不存在于数据库中，跳过")
                continue

            model_id, provider_code = models_map[model_code]

            point_rates_data.append({
                'id': str(uuid.uuid4()),
                'model_config_id': model_id,
                'tokens_per_point': rate_config['tokens_per_point'],
                'separate_io': False,
                'tokens_per_point_input': None,
                'tokens_per_point_output': None,
                'is_enabled': True,
                'created_at': now,
                'updated_at': now,
            })

            print(f"✅ {model_code} ({provider_code}): {rate_config['description']} - {rate_config['tokens_per_point']} tokens/积分")

        # 批量插入汇率配置
        if point_rates_data:
            point_rates_table = table('model_point_rates',
                column('id', sa.CHAR(36)),
                column('model_config_id', sa.CHAR(36)),
                column('tokens_per_point', sa.Integer),
                column('separate_io', sa.Boolean),
                column('tokens_per_point_input', sa.Integer),
                column('tokens_per_point_output', sa.Integer),
                column('is_enabled', sa.Boolean),
                column('created_at', sa.DateTime),
                column('updated_at', sa.DateTime),
            )

            # 使用 ON CONFLICT DO NOTHING 避免重复插入
            # 但 MySQL 不支持，所以先检查是否存在
            existing = session.execute(
                sa.select(sa.func.count()).select_from(point_rates_table)
            )
            existing_count = existing.scalar()

            if existing_count == 0:
                session.execute(point_rates_table.insert(), point_rates_data)
                session.commit()
                print(f"✅ 成功初始化 {len(point_rates_data)} 个模型的积分汇率配置")
            else:
                print(f"ℹ️  汇率配置已存在，跳过初始化（如需更新请使用 API）")

    except Exception as e:
        session.rollback()
        print(f"❌ 初始化失败: {e}")
        raise
    finally:
        session.close()


def downgrade() -> None:
    """Downgrade schema - 删除汇率配置数据"""

    # 删除所有汇率配置
    op.execute("DELETE FROM model_point_rates")
    print("✅ 已删除所有模型积分汇率配置")
