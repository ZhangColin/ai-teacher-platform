#!/usr/bin/env python3
"""
迁移汇率配置：将 tokens_per_point 转换为 tokens_per_point_input/output

运行方式：
    cd backend && python3 migrate_rates_to_separate_io.py
"""
import os
import sys

# 确保 backend/src 在路径中
backend_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

# 导入之前设置包
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from database import DATABASE_URL

def migrate_rates():
    """将所有汇率配置转换为 separate_io=True 的格式"""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # 查询当前汇率配置状态
        result = conn.execute(text("""
            SELECT
                id,
                model_config_id,
                tokens_per_point,
                separate_io,
                tokens_per_point_input,
                tokens_per_point_output
            FROM model_point_rates
            LIMIT 10
        """)).fetchall()

        print(f"=== 当前汇率配置状态（前10条）===")
        for row in result:
            print(f"ID: {row[0][:8]}..., tokens_per_point: {row[2]}, separate_io: {row[3]}, input: {row[4]}, output: {row[5]}")

        print("\n=== 开始迁移 ===")

        # 更新所有 separate_io=False 的记录
        update_result = conn.execute(text("""
            UPDATE model_point_rates
            SET
                separate_io = True,
                tokens_per_point_input = tokens_per_point,
                tokens_per_point_output = tokens_per_point
            WHERE separate_io = FALSE
               OR (separate_io = TRUE AND tokens_per_point_input IS NULL)
        """))

        conn.commit()

        print(f"✅ 迁移完成！更新了 {update_result.rowcount} 条记录")

        # 验证迁移结果
        print("\n=== 迁移后状态（前5条）===")
        result = conn.execute(text("""
            SELECT
                id,
                tokens_per_point,
                separate_io,
                tokens_per_point_input,
                tokens_per_point_output
            FROM model_point_rates
            LIMIT 5
        """)).fetchall()

        for row in result:
            print(f"ID: {row[0][:8]}..., tokens_per_point: {row[1]}, separate_io: {row[2]}, input: {row[3]}, output: {row[4]}")

if __name__ == "__main__":
    migrate_rates()
