#!/usr/bin/env python3
"""
系统初始化用户创建脚本

用法：
    python scripts/create_initial_user.py

功能：
    - 创建系统初始化用户（如果不存在）
    - 用户信息：
        - 用户名：colin
        - 密码：Hcy@2026
        - 昵称：文野
        - 邮箱：zhangjinhua@aieducenter.com
        - 手机：18001828301
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uuid
import bcrypt
from datetime import datetime
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.db_models import UserModel


def create_initial_user():
    """创建系统初始化用户"""
    db: Session = SessionLocal()
    try:
        # 检查用户是否已存在
        existing_user = db.query(UserModel).filter(
            (UserModel.username == "colin") |
            (UserModel.email == "zhangjinhua@aieducenter.com") |
            (UserModel.phone == "18001828301")
        ).first()
        
        if existing_user:
            print(f"⚠️  用户已存在：{existing_user.username}")
            print(f"   用户ID：{existing_user.user_id}")
            print(f"   昵称：{existing_user.nickname or existing_user.username}")
            print(f"   邮箱：{existing_user.email or '未设置'}")
            print(f"   手机：{existing_user.phone or '未设置'}")
            return
        
        # 创建新用户
        user_id = str(uuid.uuid4())
        password_hash = bcrypt.hashpw("Hcy@2026".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        new_user = UserModel(
            user_id=user_id,
            username="colin",
            nickname="文野",
            email="zhangjinhua@aieducenter.com",
            phone="18001828301",
            password_hash=password_hash,
            avatar=None,
            created_at=datetime.now()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print("✅ 系统初始化用户创建成功！")
        print(f"   用户ID：{new_user.user_id}")
        print(f"   用户名：{new_user.username}")
        print(f"   昵称：{new_user.nickname}")
        print(f"   邮箱：{new_user.email}")
        print(f"   手机：{new_user.phone}")
        print("\n📝 登录信息：")
        print("   可以使用以下任意方式登录：")
        print(f"   - 用户名：{new_user.username}")
        print(f"   - 邮箱：{new_user.email}")
        print(f"   - 手机号：{new_user.phone}")
        print(f"   密码：Hcy@2026")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建用户失败：{str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 开始创建系统初始化用户...\n")
    create_initial_user()

