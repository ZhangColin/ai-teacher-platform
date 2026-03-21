#!/usr/bin/env python3
"""创建管理员用户"""
import sys
sys.path.insert(0, 'src')

from database import SessionLocal
from db_models import UserModel
import bcrypt

db = SessionLocal()
admin = db.query(UserModel).filter(UserModel.email == 'admin@example.com').first()
if not admin:
    hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin = UserModel(
        username='admin',
        email='admin@example.com',
        password_hash=hashed,
        is_admin=True
    )
    db.add(admin)
    db.commit()
    print('Created admin user: admin@example.com / admin123')
else:
    admin.is_admin = True
    db.commit()
    print('Admin user already exists, ensured is_admin=True')
db.close()
