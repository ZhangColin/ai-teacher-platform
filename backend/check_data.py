import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 使用环境变量直接连接数据库
import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='truth',
    database='hcy_studio',
    charset='utf8mb4'
)

cursor = conn.cursor()

# 查询供应商
print('=== 供应商 ===')
cursor.execute('SELECT id, provider_code, provider_name, is_enabled FROM model_providers')
for row in cursor.fetchall():
    print(f'  {row[1]} - {row[2]} (启用:{row[3]})')

# 查询模型
print('\n=== 模型配置 ===')
cursor.execute('SELECT id, provider_id, model_code, model_name, capabilities, is_enabled FROM model_configs')
models = cursor.fetchall()
if not models:
    print('  (没有数据)')
for row in models:
    print(f'  {row[2]} - {row[3]} (能力:{row[4]}, 启用:{row[5]})')

cursor.close()
conn.close()
