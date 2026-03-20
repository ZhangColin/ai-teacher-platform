"""Token使用服务 - 记录和查询token消耗"""
import logging
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..db_models import TokenUsageLogModel
from ..database import get_db

logger = logging.getLogger(__name__)


class TokenService:
    """Token使用服务"""

    def __init__(self, db: Session):
        """
        初始化Token服务

        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db

    def create_token_log(
        self,
        user_id: str,
        session_id: str,
        message_id: str,
        model_provider: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int
    ) -> Optional[TokenUsageLogModel]:
        """
        记录Token使用日志

        Args:
            user_id: 用户ID
            session_id: 会话ID
            message_id: 消息ID
            model_provider: AI服务提供商
            model_name: 模型名称
            prompt_tokens: Prompt token数
            completion_tokens: Completion token数
            total_tokens: 总token数

        Returns:
            创建的TokenUsageLogModel对象，失败返回None
        """
        try:
            token_log = TokenUsageLogModel(
                user_id=user_id,
                session_id=session_id,
                message_id=message_id,
                model_provider=model_provider,
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                created_at=datetime.now()
            )

            self.db.add(token_log)
            self.db.commit()
            self.db.refresh(token_log)

            logger.info(
                f"Token日志已记录 - 用户:{user_id}, 会话:{session_id}, "
                f"模型:{model_provider}:{model_name}, Tokens:{total_tokens}"
            )

            return token_log

        except Exception as e:
            logger.error(f"记录Token日志失败: {e}", exc_info=True)
            self.db.rollback()
            return None

    def get_user_token_stats(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        model_provider: Optional[str] = None
    ) -> Dict:
        """
        获取用户的Token统计信息

        Args:
            user_id: 用户ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            model_provider: 筛选服务商（可选）

        Returns:
            统计信息字典：{
                'total_tokens': int,
                'total_prompt_tokens': int,
                'total_completion_tokens': int,
                'message_count': int,
                'by_provider': {...},
                'by_model': {...}
            }
        """
        try:
            query = self.db.query(TokenUsageLogModel).filter(
                TokenUsageLogModel.user_id == user_id
            )

            # 时间范围筛选
            if start_date:
                query = query.filter(TokenUsageLogModel.created_at >= start_date)
            if end_date:
                query = query.filter(TokenUsageLogModel.created_at <= end_date)

            # 服务商筛选
            if model_provider:
                query = query.filter(TokenUsageLogModel.model_provider == model_provider)

            # 获取所有记录
            logs = query.all()

            if not logs:
                return {
                    'total_tokens': 0,
                    'total_prompt_tokens': 0,
                    'total_completion_tokens': 0,
                    'message_count': 0,
                    'by_provider': {},
                    'by_model': {}
                }

            # 计算总计
            total_tokens = sum(log.total_tokens for log in logs)
            total_prompt_tokens = sum(log.prompt_tokens for log in logs)
            total_completion_tokens = sum(log.completion_tokens for log in logs)
            message_count = len(logs)

            # 按服务商统计
            by_provider = {}
            for log in logs:
                provider = log.model_provider
                if provider not in by_provider:
                    by_provider[provider] = {
                        'total_tokens': 0,
                        'message_count': 0
                    }
                by_provider[provider]['total_tokens'] += log.total_tokens
                by_provider[provider]['message_count'] += 1

            # 按模型统计
            by_model = {}
            for log in logs:
                model = f"{log.model_provider}:{log.model_name}"
                if model not in by_model:
                    by_model[model] = {
                        'total_tokens': 0,
                        'message_count': 0
                    }
                by_model[model]['total_tokens'] += log.total_tokens
                by_model[model]['message_count'] += 1

            return {
                'total_tokens': total_tokens,
                'total_prompt_tokens': total_prompt_tokens,
                'total_completion_tokens': total_completion_tokens,
                'message_count': message_count,
                'by_provider': by_provider,
                'by_model': by_model
            }

        except Exception as e:
            logger.error(f"获取用户Token统计失败: {e}", exc_info=True)
            return {
                'total_tokens': 0,
                'total_prompt_tokens': 0,
                'total_completion_tokens': 0,
                'message_count': 0,
                'by_provider': {},
                'by_model': {}
            }

    def get_session_token_stats(self, session_id: str) -> Dict:
        """
        获取会话的Token统计信息

        Args:
            session_id: 会话ID

        Returns:
            统计信息字典：{
                'total_tokens': int,
                'total_prompt_tokens': int,
                'total_completion_tokens': int,
                'message_count': int
            }
        """
        try:
            logs = self.db.query(TokenUsageLogModel).filter(
                TokenUsageLogModel.session_id == session_id
            ).all()

            if not logs:
                return {
                    'total_tokens': 0,
                    'total_prompt_tokens': 0,
                    'total_completion_tokens': 0,
                    'message_count': 0
                }

            return {
                'total_tokens': sum(log.total_tokens for log in logs),
                'total_prompt_tokens': sum(log.prompt_tokens for log in logs),
                'total_completion_tokens': sum(log.completion_tokens for log in logs),
                'message_count': len(logs)
            }

        except Exception as e:
            logger.error(f"获取会话Token统计失败: {e}", exc_info=True)
            return {
                'total_tokens': 0,
                'total_prompt_tokens': 0,
                'total_completion_tokens': 0,
                'message_count': 0
            }
