#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/zhangcolin/workspace/ai-teacher-platform')

from backend.src.database import SessionLocal
from backend.src.db_models import ModelPointRateModel, ModelConfigModel, ModelProviderModel
from sqlalchemy import select

db = SessionLocal()
try:
    result = db.execute(
        select(
            ModelConfigModel.model_name,
            ModelConfigModel.model_code,
            ModelProviderModel.provider_code,
            ModelPointRateModel.tokens_per_point,
            ModelPointRateModel.is_enabled
        ).join(
            ModelConfigModel, ModelPointRateModel.model_config_id == ModelConfigModel.id
        ).join(
            ModelProviderModel, ModelConfigModel.provider_id == ModelProviderModel.id
        ).order_by(
            ModelProviderModel.provider_code,
            ModelConfigModel.model_code
        ))

    print('模型汇率配置：')
    print('-' * 80)
    for row in result:
        enabled = '✅' if row.is_enabled else '❌'
        print(f'{enabled} {row.provider_code:12} | {row.model_code:25} | {row.model_name:25} | {row.tokens_per_point} tokens/积分')
finally:
    db.close()
