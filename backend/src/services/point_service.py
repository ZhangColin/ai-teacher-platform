# -*- coding: utf-8 -*-
"""积分管理服务"""
import logging
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db_models import (
    EnterpriseModel, PointTransactionModel, AIConsumptionModel,
    ModelPointRateModel, ModelConfigModel, ModelProviderModel,
    PointTransactionType, PointSourceType, UserModel
)

logger = logging.getLogger(__name__)


class PointService:
    """积分管理服务"""

    def __init__(self, db: Session):
        """
        初始化积分服务

        Args:
            db: SQLAlchemy 数据库会话
        """
        self.db = db

    def check_points_before_request(self, user_id: str) -> bool:
        """
        请求前检查积分是否足够

        Args:
            user_id: 用户ID

        Returns:
            True 表示可以发起请求，False 表示积分不足
        """
        enterprise = self._get_user_enterprise(user_id)
        if not enterprise:
            raise ValueError("用户未关联企业")

        return enterprise.total_points > 0

    def calculate_points_from_tokens(
        self,
        provider_code: str,
        model_code: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> int:
        """
        根据 token 计算积分

        Args:
            provider_code: 供应商代码
            model_code: 模型代码
            prompt_tokens: 输入 token 数
            completion_tokens: 输出 token 数

        Returns:
            消耗的积分数量
        """
        rate = self._get_model_rate(provider_code, model_code)
        if not rate:
            # 默认汇率
            tokens_per_point = 1000
        else:
            if rate.separate_io:
                # 区分输入输出（暂不实现，使用统一汇率）
                tokens_per_point = rate.tokens_per_point
            else:
                tokens_per_point = rate.tokens_per_point

        total_tokens = prompt_tokens + completion_tokens
        # 向上取整
        points = (total_tokens + tokens_per_point - 1) // tokens_per_point
        return max(1, points)  # 至少消耗1积分

    def add_points(
        self,
        enterprise_id: str,
        amount: int,
        source_type: PointSourceType,
        operator_id: str = None,
        remark: str = None
    ) -> PointTransactionModel:
        """
        增加积分（充值/赠送）

        优先抵扣负债，剩余部分增加余额

        Args:
            enterprise_id: 企业ID
            amount: 增加的积分数量
            source_type: 来源类型
            operator_id: 操作人ID
            remark: 备注

        Returns:
            创建的交易记录
        """
        try:
            with self.db.begin():
                # 1. 获取企业（加锁）
                enterprise = self._get_enterprise_for_update(enterprise_id)

                if not enterprise:
                    raise ValueError("企业不存在")

                balance_before = enterprise.total_points

                # 2. 优先抵扣负债
                if enterprise.debt_points > 0:
                    debt_to_clear = min(enterprise.debt_points, amount)
                    enterprise.debt_points -= debt_to_clear
                    remaining = amount - debt_to_clear
                else:
                    remaining = amount

                # 3. 剩余部分增加余额
                if remaining > 0:
                    if source_type == PointSourceType.admin_gift:
                        enterprise.balance_gratis += remaining
                    else:
                        enterprise.balance_paid += remaining

                # 4. 创建交易记录
                transaction = PointTransactionModel(
                    id=str(uuid.uuid4()),
                    enterprise_id=enterprise_id,
                    operator_id=operator_id,
                    type=PointTransactionType.recharge if source_type != PointSourceType.admin_gift else PointTransactionType.gift,
                    source_type=source_type,
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=enterprise.total_points,
                    remark=remark
                )

                self.db.add(transaction)
                self.db.flush()

                logger.info(
                    f"积分增加成功 - 企业:{enterprise_id}, 金额:{amount}, "
                    f"来源:{source_type}, 操作人:{operator_id}"
                )

                return transaction

        except Exception as e:
            self.db.rollback()
            logger.error(f"增加积分失败: {e}", exc_info=True)
            raise

    def deduct_points(
        self,
        enterprise_id: str,
        user_id: str,
        session_id: str,
        message_id: str,
        model_provider: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        points: int
    ) -> AIConsumptionModel:
        """
        扣减积分（事务）

        先扣赠送积分，再扣充值积分，不够则产生负债

        Args:
            enterprise_id: 企业ID
            user_id: 用户ID
            session_id: 会话ID
            message_id: 消息ID
            model_provider: 模型供应商
            model_name: 模型名称
            prompt_tokens: 输入token数
            completion_tokens: 输出token数
            points: 需扣减的积分

        Returns:
            创建的消费记录
        """
        try:
            with self.db.begin():
                # 1. 获取企业（加锁）
                enterprise = self._get_enterprise_for_update(enterprise_id)

                if not enterprise:
                    raise ValueError("企业不存在")

                # 2. 计算扣减分配
                gratis_to_deduct = min(enterprise.balance_gratis, points)
                paid_to_deduct = points - gratis_to_deduct

                # 3. 执行扣减
                enterprise.balance_gratis -= gratis_to_deduct

                if paid_to_deduct <= enterprise.balance_paid:
                    # 充值积分足够
                    enterprise.balance_paid -= paid_to_deduct
                    actual_paid_used = paid_to_deduct
                else:
                    # 充值积分不够，产生负债
                    remaining = paid_to_deduct - enterprise.balance_paid
                    enterprise.balance_paid = 0
                    enterprise.debt_points += remaining
                    actual_paid_used = enterprise.balance_paid + (paid_to_deduct - remaining)

                # 4. 创建消费记录
                consumption = AIConsumptionModel(
                    id=str(uuid.uuid4()),
                    enterprise_id=enterprise_id,
                    user_id=user_id,
                    session_id=session_id,
                    message_id=message_id,
                    model_provider=model_provider,
                    model_name=model_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    gratis_points_used=gratis_to_deduct,
                    paid_points_used=actual_paid_used,
                    total_points=points
                )

                self.db.add(consumption)
                self.db.flush()

                logger.info(
                    f"积分扣减成功 - 企业:{enterprise_id}, 用户:{user_id}, "
                    f"积分:{points} (赠送:{gratis_to_deduct}, 充值:{actual_paid_used})"
                )

                return consumption

        except Exception as e:
            self.db.rollback()
            logger.error(f"积分扣减失败: {e}", exc_info=True)
            raise

    def get_enterprise_balance(self, enterprise_id: str) -> Optional[dict]:
        """获取企业积分余额"""
        enterprise = self.db.query(EnterpriseModel).filter(
            EnterpriseModel.id == enterprise_id
        ).first()

        if not enterprise:
            return None

        return {
            "balance_gratis": enterprise.balance_gratis,
            "balance_paid": enterprise.balance_paid,
            "debt_points": enterprise.debt_points,
            "total_points": enterprise.total_points
        }

    def get_transactions(
        self,
        enterprise_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple:
        """获取交易记录列表"""
        query = self.db.query(PointTransactionModel).filter(
            PointTransactionModel.enterprise_id == enterprise_id
        )

        total = query.count()

        transactions = query.order_by(
            PointTransactionModel.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return transactions, total

    def get_consumptions(
        self,
        enterprise_id: str,
        page: int = 1,
        page_size: int = 20,
        user_id: str = None,
        start_date = None,
        end_date = None
    ) -> tuple:
        """获取消费记录列表"""
        query = self.db.query(AIConsumptionModel).filter(
            AIConsumptionModel.enterprise_id == enterprise_id
        )

        if user_id:
            query = query.filter(AIConsumptionModel.user_id == user_id)
        if start_date:
            query = query.filter(AIConsumptionModel.created_at >= start_date)
        if end_date:
            query = query.filter(AIConsumptionModel.created_at <= end_date)

        total = query.count()

        consumptions = query.order_by(
            AIConsumptionModel.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return consumptions, total

    # 私有方法

    def _get_user_enterprise(self, user_id: str) -> Optional[EnterpriseModel]:
        """获取用户所属企业"""
        user = self.db.query(UserModel).filter(
            UserModel.user_id == user_id
        ).first()

        if not user or not user.enterprise_id:
            return None

        return self.db.query(EnterpriseModel).filter(
            EnterpriseModel.id == user.enterprise_id
        ).first()

    def _get_enterprise_for_update(self, enterprise_id: str) -> Optional[EnterpriseModel]:
        """获取企业（加锁）"""
        return self.db.query(EnterpriseModel).filter(
            EnterpriseModel.id == enterprise_id
        ).with_for_update().first()

    def _get_model_rate(self, provider_code: str, model_code: str) -> Optional[ModelPointRateModel]:
        """获取模型汇率配置"""
        return self.db.query(ModelPointRateModel).join(
            ModelConfigModel, ModelPointRateModel.model_config_id == ModelConfigModel.id
        ).join(
            ModelProviderModel, ModelConfigModel.provider_id == ModelProviderModel.id
        ).filter(
            ModelProviderModel.provider_code == provider_code,
            ModelConfigModel.model_code == model_code,
            ModelPointRateModel.is_enabled == True
        ).first()
