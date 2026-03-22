#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配置数据迁移脚本

从本地数据库复制配置表数据到生产数据库
"""
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import pymysql

# 数据库配置
LOCAL_DB = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'truth',
    'database': 'hcy_studio'
}

PROD_DB = {
    'host': '39.97.6.179',
    'port': 3306,
    'user': 'root',
    'password': 'Hcy_mysql_2025',
    'database': 'studio'
}

# 需要迁移的表（按依赖顺序）
TABLES = [
    'model_providers',
    'model_configs',
    'navigation_modules',
    'tool_categories',
    'ai_tool_categories',
    'ai_tools',
]


def get_connection(db_config):
    """创建数据库连接"""
    return pymysql.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def migrate_table(src_conn, dst_conn, table_name):
    """迁移单个表的数据"""
    print(f"\n迁移表: {table_name}")

    # 读取源数据
    with src_conn.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        print(f"  源数据: {len(rows)} 条")

    if not rows:
        print(f"  跳过（无数据）")
        return

    # 获取列名
    columns = list(rows[0].keys())
    placeholders = ', '.join(['%s'] * len(columns))
    # 用反引号包裹列名（处理保留字如 order）
    columns_str = ', '.join([f'`{col}`' for col in columns])

    # 清空目标表（可选，根据需要决定是否清空）
    with dst_conn.cursor() as cursor:
        # 检查是否有数据
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
        count = cursor.fetchone()['cnt']
        print(f"  目标表现有: {count} 条")

        # 清空目标表
        cursor.execute(f"DELETE FROM {table_name}")
        print(f"  已清空目标表")

    # 插入数据
    inserted = 0
    for row in rows:
        values = [row[col] for col in columns]
        with dst_conn.cursor() as cursor:
            sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            cursor.execute(sql, values)
            inserted += 1

    dst_conn.commit()
    print(f"  已插入: {inserted} 条")


def main():
    """主函数"""
    print("=" * 60)
    print("配置数据迁移工具")
    print("=" * 60)
    print(f"\n源数据库: {LOCAL_DB['host']}:{LOCAL_DB['port']}/{LOCAL_DB['database']}")
    print(f"目标数据库: {PROD_DB['host']}:{PROD_DB['port']}/{PROD_DB['database']}")
    print(f"\n将迁移以下表:")
    for table in TABLES:
        print(f"  - {table}")

    input("\n按 Enter 继续，Ctrl+C 取消...")

    try:
        print("\n连接数据库...")
        src_conn = get_connection(LOCAL_DB)
        dst_conn = get_connection(PROD_DB)
        print("连接成功!")

        for table in TABLES:
            migrate_table(src_conn, dst_conn, table)

        print("\n" + "=" * 60)
        print("迁移完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)
    finally:
        if 'src_conn' in locals():
            src_conn.close()
        if 'dst_conn' in locals():
            dst_conn.close()


if __name__ == '__main__':
    main()
