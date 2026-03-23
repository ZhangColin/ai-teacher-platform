# -*- coding: utf-8 -*-
"""企业管理服务"""
import logging
import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from ..db_models import (
    EnterpriseModel, UserModel, EnterpriseStatus,
    PointTransactionModel, PointTransactionType, PointSourceType
)

logger = logging.getLogger(__name__)


class EnterpriseService:
    """企业管理服务"""

    def __init__(self, db: Session):
        """
        初始化企业管理服务

        Args:
            db: SQLAlchemy 数据库会话
        """
        self.db = db

    def create_enterprise(
        self,
        name: str,
        code: str,
        initial_gratis: int = 0
    ) -> EnterpriseModel:
        """
        创建新企业

        Args:
            name: 企业名称
            code: 企业代码（唯一）
            initial_gratis: 初始赠送积分

        Returns:
            创建的企业模型

        Raises:
            ValueError: 企业代码已存在
        """
        # 检查代码是否重复
        existing = self.db.query(EnterpriseModel).filter(
            EnterpriseModel.code == code
        ).first()
        if existing:
            raise ValueError(f"企业代码 '{code}' 已存在")

        try:
            enterprise = EnterpriseModel(
                id=str(uuid.uuid4()),
                name=name,
                code=code,
                status=EnterpriseStatus.active,
                balance_gratis=0,  # 先设置为0，后面通过add_points添加
                balance_paid=0,
                debt_points=0
            )

            self.db.add(enterprise)
            self.db.flush()  # 获取enterprise.id，但不提交事务

            # 如果有初始赠送积分，创建交易记录
            if initial_gratis > 0:
                transaction = PointTransactionModel(
                    id=str(uuid.uuid4()),
                    enterprise_id=enterprise.id,
                    operator_id=None,
                    type=PointTransactionType.gift,
                    source_type=PointSourceType.admin_gift,
                    amount=initial_gratis,
                    balance_before=0,
                    balance_after=initial_gratis,
                    remark="创建企业时赠送的初始积分"
                )
                self.db.add(transaction)

                # 更新企业积分余额
                enterprise.balance_gratis = initial_gratis

            self.db.commit()
            self.db.refresh(enterprise)

            logger.info(f"创建企业成功: {name} ({code}), 初始赠送积分: {initial_gratis}")
            return enterprise

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建企业失败: {e}")
            raise

    def get_enterprise_by_id(self, enterprise_id: str) -> Optional[EnterpriseModel]:
        """根据ID获取企业"""
        return self.db.query(EnterpriseModel).filter(
            EnterpriseModel.id == enterprise_id
        ).first()

    def get_enterprise_by_code(self, code: str) -> Optional[EnterpriseModel]:
        """根据代码获取企业"""
        return self.db.query(EnterpriseModel).filter(
            EnterpriseModel.code == code
        ).first()

    def get_all_enterprises(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[EnterpriseStatus] = None
    ) -> Tuple[List[EnterpriseModel], int]:
        """
        获取企业列表（分页）

        Returns:
            (企业列表, 总数)
        """
        query = self.db.query(EnterpriseModel)

        if status:
            query = query.filter(EnterpriseModel.status == status)

        total = query.count()

        enterprises = query.order_by(desc(EnterpriseModel.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return enterprises, total

    def update_enterprise(
        self,
        enterprise_id: str,
        name: Optional[str] = None,
        status: Optional[EnterpriseStatus] = None
    ) -> Optional[EnterpriseModel]:
        """更新企业信息"""
        enterprise = self.get_enterprise_by_id(enterprise_id)
        if not enterprise:
            return None

        if name is not None:
            enterprise.name = name
        if status is not None:
            enterprise.status = status

        self.db.commit()
        self.db.refresh(enterprise)
        return enterprise

    def delete_enterprise(self, enterprise_id: str) -> bool:
        """
        删除企业

        注意：如果企业下有用户，无法删除
        """
        enterprise = self.get_enterprise_by_id(enterprise_id)
        if not enterprise:
            return False

        # 检查是否有用户
        user_count = self.db.query(UserModel).filter(
            UserModel.enterprise_id == enterprise_id
        ).count()

        if user_count > 0:
            raise ValueError(f"企业下还有 {user_count} 个用户，无法删除")

        try:
            self.db.delete(enterprise)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除企业失败: {e}")
            raise

    def get_user_enterprise(self, user_id: str) -> Optional[EnterpriseModel]:
        """获取用户所属企业"""
        user = self.db.query(UserModel).filter(
            UserModel.user_id == user_id
        ).first()

        if not user or not user.enterprise_id:
            return None

        return self.get_enterprise_by_id(user.enterprise_id)
