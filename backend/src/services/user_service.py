"""用户服务：管理用户数据"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
from ..database import SessionLocal
from ..db_models import UserModel
from ..models import User


class UserService:
    """用户服务类"""
    
    def __init__(self):
        """初始化用户服务"""
        pass
    
    def _get_db(self):
        """获取数据库会话（生成器）"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def create_user(self, username: str, password: str, nickname: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None, avatar: Optional[str] = None) -> User:
        """
        创建新用户
        
        Args:
            username: 用户名（必填，必须唯一）
            password: 用户密码（明文）
            nickname: 用户昵称（可选，用于显示）
            email: 用户邮箱（可选，用于登录）
            phone: 用户手机号（可选，用于登录）
            avatar: 用户头像URL（可选）
            
        Returns:
            User: 创建的用户实体
            
        Raises:
            ValueError: 用户名、邮箱或手机号已存在
        """
        # 使用User.create方法创建用户实体（密码自动加密）
        user_entity = User.create(username=username, password=password, nickname=nickname, email=email, phone=phone, avatar=avatar)
        
        db_gen = self._get_db()
        db = next(db_gen)
        try:
            # 转换为SQLAlchemy模型
            user_model = UserModel(
                user_id=user_entity.user_id,
                username=user_entity.username,
                nickname=user_entity.nickname,
                email=user_entity.email,
                phone=user_entity.phone,
                password_hash=user_entity.password_hash,
                avatar=user_entity.avatar,
                created_at=user_entity.created_at
            )
            
            db.add(user_model)
            db.commit()
            db.refresh(user_model)
            
            # 转换回User实体
            return User(
                user_id=user_model.user_id,
                username=user_model.username,
                nickname=user_model.nickname,
                email=user_model.email,
                phone=user_model.phone,
                password_hash=user_model.password_hash,
                avatar=user_model.avatar,
                created_at=user_model.created_at
            )
        except IntegrityError as e:
            db.rollback()
            # 判断是用户名、邮箱还是手机号冲突
            if db.query(UserModel).filter(UserModel.username == username).first():
                raise ValueError("用户名已存在")
            if email and db.query(UserModel).filter(UserModel.email == email).first():
                raise ValueError("邮箱已存在")
            if phone and db.query(UserModel).filter(UserModel.phone == phone).first():
                raise ValueError("手机号已存在")
            raise ValueError("创建用户失败")
        finally:
            try:
                next(db_gen, None)  # 完成生成器
            except StopIteration:
                pass
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        
        Args:
            email: 用户邮箱
            
        Returns:
            User: 用户实体，如果不存在返回None
        """
        db_gen = self._get_db()
        db = next(db_gen)
        try:
            user_model = db.query(UserModel).filter(UserModel.email == email).first()
            if user_model is None:
                return None
            
            return User(
                user_id=user_model.user_id,
                username=user_model.username,
                nickname=user_model.nickname,
                email=user_model.email,
                phone=user_model.phone,
                password_hash=user_model.password_hash,
                avatar=user_model.avatar,
                created_at=user_model.created_at
            )
        finally:
            try:
                next(db_gen, None)  # 完成生成器
            except StopIteration:
                pass
    
    def get_user_by_phone(self, phone: str) -> Optional[User]:
        """
        根据手机号获取用户
        
        Args:
            phone: 用户手机号
            
        Returns:
            User: 用户实体，如果不存在返回None
        """
        db_gen = self._get_db()
        db = next(db_gen)
        try:
            user_model = db.query(UserModel).filter(UserModel.phone == phone).first()
            if user_model is None:
                return None
            
            return User(
                user_id=user_model.user_id,
                username=user_model.username,
                nickname=user_model.nickname,
                email=user_model.email,
                phone=user_model.phone,
                password_hash=user_model.password_hash,
                avatar=user_model.avatar,
                created_at=user_model.created_at
            )
        finally:
            try:
                next(db_gen, None)  # 完成生成器
            except StopIteration:
                pass
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            User: 用户实体，如果不存在返回None
        """
        db_gen = self._get_db()
        db = next(db_gen)
        try:
            user_model = db.query(UserModel).filter(UserModel.username == username).first()
            if user_model is None:
                return None
            
            return User(
                user_id=user_model.user_id,
                username=user_model.username,
                nickname=user_model.nickname,
                email=user_model.email,
                phone=user_model.phone,
                password_hash=user_model.password_hash,
                avatar=user_model.avatar,
                created_at=user_model.created_at
            )
        finally:
            try:
                next(db_gen, None)  # 完成生成器
            except StopIteration:
                pass
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        根据用户ID获取用户
        
        Args:
            user_id: 用户ID（UUID）
            
        Returns:
            User: 用户实体，如果不存在返回None
        """
        db_gen = self._get_db()
        db = next(db_gen)
        try:
            user_model = db.query(UserModel).filter(UserModel.user_id == user_id).first()
            if user_model is None:
                return None
            
            return User(
                user_id=user_model.user_id,
                username=user_model.username,
                nickname=user_model.nickname,
                email=user_model.email,
                phone=user_model.phone,
                password_hash=user_model.password_hash,
                avatar=user_model.avatar,
                created_at=user_model.created_at
            )
        finally:
            try:
                next(db_gen, None)  # 完成生成器
            except StopIteration:
                pass
    
    def get_all_users(self, page: int = 1, page_size: int = 20) -> Tuple[List[User], int]:
        """
        获取所有用户列表（支持分页）
        
        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            
        Returns:
            Tuple[List[User], int]: (用户列表, 总数)
        """
        db_gen = self._get_db()
        db = next(db_gen)
        try:
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 获取总数
            total = db.query(UserModel).count()
            
            # 获取分页数据（按创建时间倒序）
            user_models = db.query(UserModel).order_by(desc(UserModel.created_at)).offset(offset).limit(page_size).all()
            
            # 转换为User实体列表
            users = [
                User(
                    user_id=user_model.user_id,
                    username=user_model.username,
                    nickname=user_model.nickname,
                    email=user_model.email,
                    phone=user_model.phone,
                    password_hash=user_model.password_hash,
                    avatar=user_model.avatar,
                    created_at=user_model.created_at
                )
                for user_model in user_models
            ]
            
            return users, total
        finally:
            try:
                next(db_gen, None)  # 完成生成器
            except StopIteration:
                pass

