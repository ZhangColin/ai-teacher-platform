#!/usr/bin/env python3
"""
更新模型汇率配置（基于 2026年2-3月实际定价）

数据来源: https://github.com/syaoranwe/LLM-Price
汇率规则: 1元 = 100积分，即 1积分 = 1分钱
计算公式: tokens_per_point = 10000 / 平均价格(元/M tokens)
"""
import sys
sys.path.insert(0, '/Users/zhangcolin/workspace/ai-teacher-platform')

from backend.src.database import SessionLocal
from backend.src.db_models import ModelPointRateModel, ModelConfigModel, ModelProviderModel
from sqlalchemy import select
from datetime import datetime

# 模型定价配置（元/M tokens，数据更新至 2026-02-26）
# 格式: (输入价格, 输出价格)
MODEL_PRICING = {
    # === DeepSeek 系列 ===
    # deepseek-chat: 输入 2元, 输出 3元 → 平均 2.5 元/M → 4000 tokens/积分
    "deepseek-chat": (2, 3),
    "deepseek-coder": (2, 3),
    "deepseek-r1": (2, 3),
    "deepseek-v3": (2, 3),
    "deepseek-v3.2": (2, 3),
    "deepseek-v3.2-reasoning": (2, 3),
    "deepseek-r1-distill-llama-70b": (2, 3),
    "deepseek-r1-distill-qwen-32b": (2, 3),
    "deepseek-vl2": (2, 3),

    # === Kimi (Moonshot) 系列 ===
    # moonshot-v1-8k: 输入 2元, 输出 10元 → 平均 6 元/M → 1667 tokens/积分
    "moonshot-v1-8k": (2, 10),
    "moonshot-v1-32k": (5, 25),  # 推算: 32k约为8k的2.5倍
    "moonshot-v1-128k": (10, 50),  # 推算: 128k约为8k的5倍
    "moonshot-v1-1m": (20, 100),  # 推算: 1M约为8k的10倍
    # kimi-k2.5: 输入 4元, 输出 21元 → 平均 12.5 元/M → 800 tokens/积分
    "kimi-k2.5": (4, 21),
    "kimi-k2.5-thinking": (4, 21),
    "kimi-k2.5-vision": (4, 21),

    # === GLM 系列 ===
    # GLM-5: 输入 4元, 输出 18元 → 平均 11 元/M → 909 tokens/积分
    "glm-5": (4, 18),
    "glm-5-turbo": (4, 18),
    # GLM-4.7: 输入 3元, 输出 14元 → 平均 8.5 元/M → 1176 tokens/积分
    "glm-4.7": (3, 14),
    # GLM-4.6: 输入 1元, 输出 3元 → 平均 2 元/M → 5000 tokens/积分
    "glm-4.6": (1, 3),
    "glm-4.6v": (1, 3),
    # GLM-4.5-Air: 输入 0.8元, 输出 6元 → 平均 3.4 元/M → 2941 tokens/积分
    "glm-4.5-air": (0.8, 6),
    "glm-4.5-airx": (0.8, 6),
    # GLM-4.7-FlashX: 输入 0.5元, 输出 3元 → 平均 1.75 元/M → 5714 tokens/积分
    "glm-4.7-flash": (0, 0),  # 免费
    "glm-4.7-flashx": (0.5, 3),
    # GLM-4.6V-FlashX: 输入 0.15元, 输出 1.5元 → 平均 0.825 元/M → 12121 tokens/积分
    "glm-4.6v-flashx": (0.15, 1.5),
    # GLM-4-Air: 输入 0.5元, 输出 0.5元 → 平均 0.5 元/M → 20000 tokens/积分
    "glm-4-air": (0.5, 0.5),
    "glm-4-flashx": (0.1, 0.1),
    "glm-4-long": (1, 3),
    "glm-4-voice": (1, 3),
    # CogView-4: 图像生成，按张计费，暂定较高汇率
    "cogview-3-flash": (0.5, 0.5),
    "cogview-4": (5, 5),  # 图像生成模型，成本较高
    "cogvideox-3": (5, 5),
    "cogvideox-flash": (0.5, 0.5),
    "glm-image": (1, 1),
    "glm-ocr": (0.2, 0.2),
    "glm-tts": (2, 2),

    # === OpenAI GPT 系列 ===
    # GPT-5.2: 输入 12.25元, 输出 98元 → 平均 55.125 元/M → 181 tokens/积分
    "gpt-5.2-codex": (12.25, 98),
    # GPT-5.4: 推算约为 GPT-5.2 的 1.1 倍
    "gpt-5.3-codex": (11, 88),
    "gpt-5.4": (13.5, 108),
    "gpt-5.4-mini": (1.4, 11.2),
    "gpt-5.4-thinking": (10, 80),
    "gpt-5-codex": (10, 80),
    # GPT-4.1: 输入 2元, 输出 8元 → 平均 5 元/M → 2000 tokens/积分
    "gpt-4.1": (2, 8),
    "gpt-4.1-mini": (0.4, 1.6),
    # GPT-4o: 输入 2.5元, 输出 10元 → 平均 6.25 元/M → 1600 tokens/积分
    "gpt-4o": (2.5, 10),
    "gpt-4o-mini": (0.35, 1.4),
    "gpt-4-turbo": (2.8, 11.2),
    "gpt-3.5-turbo": (0.35, 1.4),
    # o3: OpenAI 推理模型
    "o3": (8, 64),
    "o3-mini": (1.4, 11.2),

    # === Claude 系列 ===
    # Claude Opus 4.6: 输入 35元, 输出 175元 → 平均 105 元/M → 95 tokens/积分
    "claude-opus-4.5": (35, 175),
    "claude-opus-4.6": (35, 175),
    # Claude Sonnet 4.6: 输入 21元, 输出 105元 → 平均 63 元/M → 159 tokens/积分
    "claude-sonnet-4": (21, 105),
    "claude-sonnet-4.5": (21, 105),
    "claude-sonnet-4.6": (21, 105),
    # Claude Haiku 4.5: 输入 7元, 输出 35元 → 平均 21 元/M → 476 tokens/积分
    "claude-haiku-4.5": (7, 35),
    "claude-haiku-4.6": (7, 35),

    # === Google Gemini 系列 ===
    # Gemini 3.1 Pro: 输入 14元, 输出 84元 → 平均 49 元/M → 204 tokens/积分
    "gemini-3.1-pro-preview": (14, 84),
    "gemini-3.1-flash-lite-preview": (0.35, 1.4),
    # Gemini 2.5 Flash: 输入 2.1元, 输出 17.5元 → 平均 9.8 元/M → 1020 tokens/积分
    "gemini-2.5-flash": (2.1, 17.5),
    "gemini-2.5-flash-lite": (0.7, 2.8),
    "gemini-2.5-pro": (8.75, 70),
    # Gemini 1.5 系列
    "gemini-1.5-flash": (1.75, 7),
    "gemini-1.5-pro": (3.5, 21),
    # Gemini 2.0 Flash
    "gemini-2.0-flash": (2.1, 17.5),
    "gemini-2.0-flash-lite": (0.7, 2.8),
    "gemini-2.5-flash": (2.1, 17.5),
    "gemini-2.5-pro": (8.75, 70),

    # === 字节豆包系列 ===
    # doubao-seed-2.0-pro: 输入 3.2元, 输出 16元 → 平均 9.6 元/M → 1041 tokens/积分
    "ep-20260322151359-pk8n2": (3.2, 16),  # doubao-seed-2.0-pro
    # doubao-seed-2.0-lite: 输入 0.6元, 输出 3.6元 → 平均 2.1 元/M → 4762 tokens/积分
    "ep-20260322151700-vnb6f": (0.6, 3.6),  # doubao-seed-2.0-lite
    # doubao-seed-2.0-mini: 输入 0.2元, 输出 2.0元 → 平均 1.1 元/M → 9091 tokens/积分
    "ep-20260322151739-6zm8m": (0.2, 2.0),  # doubao-seed-2.0-mini
    "ep-20260322151811-9wmc5": (0.6, 3.6),  # doubao-seed-2.0-code
}

# AWS Bedrock Claude 模型（使用 Claude 定价）
BEDROCK_CLAUDE_PRICING = {
    "global.anthropic.claude-haiku-4.5-20251001-v1:0": (7, 35),
    "global.anthropic.claude-opus-4.6-v1": (35, 175),
    "global.anthropic.claude-sonnet-4.6": (21, 105),
    "anthropic.claude-haiku-4.5-20251001-v1:0": (7, 35),
    "anthropic.claude-opus-4.6-v1:0": (35, 175),
    "anthropic.claude-sonnet-4.5-20250929-v1:0": (21, 105),
    "anthropic.claude-sonnet-4.6": (21, 105),
}


def calculate_tokens_per_point(input_price: float, output_price: float) -> int:
    """
    计算每积分对应的 token 数

    公式: tokens_per_point = 10000 / ((input_price + output_price) / 2)

    Args:
        input_price: 输入价格（元/M tokens）
        output_price: 输出价格（元/M tokens）

    Returns:
        tokens_per_point: 每积分对应的 token 数
    """
    if input_price == 0 and output_price == 0:
        return 100000  # 免费模型给一个很高的汇率
    avg_price = (input_price + output_price) / 2
    return int(10000 / avg_price)


def main():
    db = SessionLocal()
    try:
        # 获取所有启用的模型配置
        result = db.execute(
            select(
                ModelConfigModel.id,
                ModelConfigModel.model_code,
                ModelConfigModel.model_name,
                ModelProviderModel.provider_code,
            ).join(
                ModelProviderModel,
                ModelConfigModel.provider_id == ModelProviderModel.id
            ).where(
                ModelConfigModel.is_enabled == True
            )
        )

        models = result.fetchall()

        print(f"=== 模型汇率配置更新（基于 2026年2-3月定价）===\n")
        print(f"规则: 1元 = 100积分，即 1积分 = 1分钱\n")
        print(f"{'供应商':<12} {'模型代码':<35} {'模型名称':<25} {'输入':<8} {'输出':<8} {'汇率':<15} {'状态'}")
        print("-" * 120)

        updated_count = 0
        created_count = 0
        skipped_count = 0

        for model_id, model_code, model_name, provider_code in models:
            # 查找定价
            pricing = None
            if provider_code == "bedrock":
                pricing = BEDROCK_CLAUDE_PRICING.get(model_code)
            else:
                pricing = MODEL_PRICING.get(model_code)

            if not pricing:
                print(f"{provider_code:<12} {model_code:<35} {model_name:<25} {'未找到定价':<55} 跳过")
                skipped_count += 1
                continue

            input_price, output_price = pricing
            tokens_per_point = calculate_tokens_per_point(input_price, output_price)

            # 检查是否已有汇率配置
            existing_rate = db.execute(
                select(ModelPointRateModel).where(
                    ModelPointRateModel.model_config_id == model_id
                )
            ).scalar_one_or_none()

            now = datetime.now()

            if existing_rate:
                # 更新现有配置
                existing_rate.tokens_per_point = tokens_per_point
                existing_rate.updated_at = now
                status = "更新"
                updated_count += 1
            else:
                # 创建新配置
                new_rate = ModelPointRateModel(
                    id=str(uuid.uuid4()),
                    model_config_id=model_id,
                    tokens_per_point=tokens_per_point,
                    separate_io=False,
                    tokens_per_point_input=None,
                    tokens_per_point_output=None,
                    is_enabled=True,
                    created_at=now,
                    updated_at=now,
                )
                db.add(new_rate)
                status = "新增"
                created_count += 1

            print(f"{provider_code:<12} {model_code:<35} {model_name:<25} {input_price:<8} {output_price:<8} {tokens_per_point} tokens/积分 {status}")

        db.commit()
        print("\n" + "=" * 120)
        print(f"更新完成: 新增 {created_count} 个, 更新 {updated_count} 个, 跳过 {skipped_count} 个")
        print("=" * 120)

    except Exception as e:
        db.rollback()
        print(f"❌ 更新失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import uuid
    main()
