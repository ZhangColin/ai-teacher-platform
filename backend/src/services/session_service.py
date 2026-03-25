# -*- coding: utf-8 -*-
"""会话服务：管理会话和消息"""
import logging
import uuid
from datetime import datetime
from typing import List, Optional
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models import Session as SessionDomain, Message as MessageDomain
from ..db_models import SessionModel, MessageModel, MessageRole

logger = logging.getLogger(__name__)


class SessionService:
    """会话管理服务"""
    
    def __init__(self):
        """初始化会话服务"""
        # 使用数据库的 get_db 函数
        from ..database import get_db
        self._get_db = get_db
    
    @contextmanager
    def _get_db_session(self):
        """
        获取数据库会话的上下文管理器
        确保数据库连接正确释放
        """
        db_gen = self._get_db()
        db = next(db_gen)
        try:
            yield db
        finally:
            try:
                next(db_gen, None)  # 触发生成器的 finally 块
            except StopIteration:
                pass
    
    def create_session(
        self, 
        user_id: str, 
        tool_id: str, 
        title: Optional[str] = None,
        first_message: Optional[str] = None
    ) -> SessionDomain:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            tool_id: 工具ID
            title: 会话标题（可选，如果不提供则基于 first_message 生成）
            first_message: 第一条用户消息（可选，用于自动生成标题）
            
        Returns:
            Session 领域模型实例
        """
        with self._get_db_session() as db:
            # 生成会话ID
            session_id = str(uuid.uuid4())
            
            # 生成标题
            if title is None:
                if first_message:
                    # 创建临时 Session 对象用于生成标题
                    temp_session = SessionDomain(
                        session_id=session_id,
                        user_id=user_id,
                        tool_id=tool_id,
                        title=""
                    )
                    title = temp_session.generate_title(first_message)
                else:
                    title = "新对话"
            
            # 创建数据库模型
            session_model = SessionModel(
                session_id=session_id,
                user_id=user_id,
                tool_id=tool_id,
                title=title,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(session_model)
            db.commit()
            db.refresh(session_model)
            
            # 转换为领域模型
            return self._to_domain_model(session_model)
    
    def get_session_by_id(self, session_id: str, user_id: Optional[str] = None) -> Optional[SessionDomain]:
        """
        根据ID获取会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID（可选，如果提供则验证会话是否属于该用户）
            
        Returns:
            Session 领域模型实例，如果不存在或不属于用户则返回 None
        """
        with self._get_db_session() as db:
            query = db.query(SessionModel).filter(SessionModel.session_id == session_id)
            
            if user_id:
                query = query.filter(SessionModel.user_id == user_id)
            
            session_model = query.first()
            
            if not session_model:
                return None
            
            return self._to_domain_model(session_model)
    
    def get_sessions_by_user_and_tool(
        self, 
        user_id: str, 
        tool_id: str
    ) -> List[SessionDomain]:
        """
        获取用户在某工具下的所有会话，按更新时间倒序
        
        Args:
            user_id: 用户ID
            tool_id: 工具ID
            
        Returns:
            会话列表（按 updated_at 倒序）
        """
        with self._get_db_session() as db:
            session_models = db.query(SessionModel).filter(
                SessionModel.user_id == user_id,
                SessionModel.tool_id == tool_id
            ).order_by(desc(SessionModel.updated_at)).all()
            
            return [self._to_domain_model(sm) for sm in session_models]
    
    def update_session_title(self, session_id: str, new_title: str, user_id: Optional[str] = None) -> Optional[SessionDomain]:
        """
        更新会话标题
        
        Args:
            session_id: 会话ID
            new_title: 新标题
            user_id: 用户ID（可选，如果提供则验证会话是否属于该用户）
            
        Returns:
            更新后的 Session 领域模型实例，如果不存在或不属于用户则返回 None
        """
        with self._get_db_session() as db:
            query = db.query(SessionModel).filter(SessionModel.session_id == session_id)
            
            if user_id:
                query = query.filter(SessionModel.user_id == user_id)
            
            session_model = query.first()
            
            if not session_model:
                return None
            
            # 更新标题和时间戳
            session_model.title = new_title
            session_model.updated_at = datetime.now()
            
            db.commit()
            db.refresh(session_model)
            
            return self._to_domain_model(session_model)
    
    def delete_session(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """
        删除会话（级联删除消息和成果物）
        
        Args:
            session_id: 会话ID
            user_id: 用户ID（可选，如果提供则验证会话是否属于该用户）
            
        Returns:
            是否删除成功
        """
        with self._get_db_session() as db:
            query = db.query(SessionModel).filter(SessionModel.session_id == session_id)
            
            if user_id:
                query = query.filter(SessionModel.user_id == user_id)
            
            session_model = query.first()
            
            if not session_model:
                return False
            
            db.delete(session_model)
            db.commit()
            
            return True
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        user_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None
    ) -> MessageDomain:
        """
        添加消息到会话

        Args:
            session_id: 会话ID
            role: 消息角色（'user' 或 'assistant'）
            content: 消息内容
            user_id: 用户ID（可选，如果提供则验证会话是否属于该用户）
            created_at: 消息创建时间（可选，如果不提供则使用当前时间）
            model_provider: AI服务提供商（可选，用于token记录）
            model_name: 模型名称（可选，用于token记录）
            prompt_tokens: 用户消息的token消耗（可选）
            completion_tokens: AI回复的token消耗（可选）
            total_tokens: 总token消耗（可选）

        Returns:
            Message 领域模型实例
        """
        with self._get_db_session() as db:
            # 验证会话存在且属于用户
            query = db.query(SessionModel).filter(SessionModel.session_id == session_id)
            if user_id:
                query = query.filter(SessionModel.user_id == user_id)

            session_model = query.first()
            if not session_model:
                raise ValueError(f"Session '{session_id}' not found")

            # 创建消息（使用传入的时间或当前时间）
            message_time = created_at if created_at is not None else datetime.now()
            message_id = str(uuid.uuid4())
            message_model = MessageModel(
                message_id=message_id,
                session_id=session_id,
                role=MessageRole(role),
                content=content,
                created_at=message_time,
                # 新增：模型和token字段
                model_provider=model_provider,
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )

            db.add(message_model)

            # 更新会话的 updated_at
            session_model.updated_at = datetime.now()

            # 如果提供了token信息，更新会话的token累计
            if total_tokens is not None:
                session_model.total_tokens = (session_model.total_tokens or 0) + total_tokens
                if prompt_tokens is not None:
                    session_model.total_prompt_tokens = (session_model.total_prompt_tokens or 0) + prompt_tokens
                if completion_tokens is not None:
                    session_model.total_completion_tokens = (session_model.total_completion_tokens or 0) + completion_tokens

            db.commit()
            db.refresh(message_model)

            # 转换为领域模型
            return self._to_domain_model_message(message_model)
    
    def get_messages_by_session(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> List[MessageDomain]:
        """
        获取会话的所有消息，按创建时间正序
        
        Args:
            session_id: 会话ID
            user_id: 用户ID（可选，如果提供则验证会话是否属于该用户）
            
        Returns:
            消息列表（按 created_at 正序）
        """
        with self._get_db_session() as db:
            # 验证会话存在且属于用户
            query = db.query(SessionModel).filter(SessionModel.session_id == session_id)
            if user_id:
                query = query.filter(SessionModel.user_id == user_id)
            
            session_model = query.first()
            if not session_model:
                return []
            
            # 获取消息
            message_models = db.query(MessageModel).filter(
                MessageModel.session_id == session_id
            ).order_by(MessageModel.created_at).all()
            
            return [self._to_domain_model_message(mm) for mm in message_models]

    # 别名方法：为了保持API一致性，提供 get_session_messages 别名
    def get_session_messages(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> List[MessageDomain]:
        """
        获取会话的所有消息（别名方法）

        这是 get_messages_by_session 的别名，用于保持API命名一致性。
        详见 get_messages_by_session 的文档。
        """
        return self.get_messages_by_session(session_id, user_id)

    def _to_domain_model(self, session_model: SessionModel) -> SessionDomain:
        """将数据库模型转换为领域模型"""
        return SessionDomain(
            session_id=session_model.session_id,
            user_id=session_model.user_id,
            tool_id=session_model.tool_id,
            title=session_model.title,
            created_at=session_model.created_at,
            updated_at=session_model.updated_at,
            model_provider=getattr(session_model, 'model_provider', None),
            model_name=getattr(session_model, 'model_name', None)
        )
    
    def _to_domain_model_message(self, message_model: MessageModel) -> MessageDomain:
        """将数据库模型转换为领域模型"""
        return MessageDomain(
            message_id=message_model.message_id,
            session_id=message_model.session_id,
            role=message_model.role.value,
            content=message_model.content,
            created_at=message_model.created_at,
            timestamp=message_model.created_at,  # 兼容前端
            artifacts=[],  # 成果物需要单独查询
            media_content=getattr(message_model, 'media_content', None),  # 多模态内容
            model_provider=getattr(message_model, 'model_provider', None),
            model_name=getattr(message_model, 'model_name', None),
            prompt_tokens=getattr(message_model, 'prompt_tokens', None),
            completion_tokens=getattr(message_model, 'completion_tokens', None),
            total_tokens=getattr(message_model, 'total_tokens', None)
        )
    
    # ==================== 多模态支持方法 ====================
    
    async def create_session_with_id(
        self, 
        session_id: str,
        user_id: str, 
        tool_id: str, 
        title: str
    ) -> SessionDomain:
        """
        创建新会话（异步版本，指定 session_id）
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            tool_id: 工具ID
            title: 会话标题
            
        Returns:
            Session 领域模型实例
        """
        with self._get_db_session() as db:
            # 创建数据库模型
            session_model = SessionModel(
                session_id=session_id,
                user_id=user_id,
                tool_id=tool_id,
                title=title,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(session_model)
            db.commit()
            db.refresh(session_model)
            
            return self._to_domain_model(session_model)
    
    async def get_session(self, session_id: str) -> Optional[SessionDomain]:
        """
        获取会话（异步版本，简化接口）
        
        Args:
            session_id: 会话ID
            
        Returns:
            Session 领域模型实例
        """
        return self.get_session_by_id(session_id)
    
    async def save_message(
        self,
        message_id: str,
        session_id: str,
        role: str,
        content: str
    ) -> MessageDomain:
        """
        保存消息（文本消息）
        
        Args:
            message_id: 消息ID
            session_id: 会话ID
            role: 角色（user/assistant）
            content: 消息内容
            
        Returns:
            Message 领域模型实例
        """
        with self._get_db_session() as db:
            # 创建消息模型
            message_model = MessageModel(
                message_id=message_id,
                session_id=session_id,
                role=MessageRole(role),
                content=content,
                created_at=datetime.now()
            )
            
            db.add(message_model)
            db.commit()
            db.refresh(message_model)
            
            # 更新会话的updated_at
            session_model = db.query(SessionModel).filter(
                SessionModel.session_id == session_id
            ).first()
            if session_model:
                session_model.updated_at = datetime.now()
                db.commit()
            
            return self._to_domain_model_message(message_model)
    
    async def save_message_with_media(
        self,
        message_id: str,
        session_id: str,
        role: str,
        content: str,
        media_content: str
    ) -> MessageDomain:
        """
        保存多模态消息

        Args:
            message_id: 消息ID
            session_id: 会话ID
            role: 角色（user/assistant）
            content: 文本内容（可为空）
            media_content: 多模态内容JSON字符串

        Returns:
            Message 领域模型实例
        """
        with self._get_db_session() as db:
            # 创建消息模型
            message_model = MessageModel(
                message_id=message_id,
                session_id=session_id,
                role=MessageRole(role),
                content=content,
                created_at=datetime.now()
            )

            # 设置多模态内容
            message_model.media_content = media_content

            db.add(message_model)
            db.commit()
            db.refresh(message_model)

            # 更新会话的updated_at
            session_model = db.query(SessionModel).filter(
                SessionModel.session_id == session_id
            ).first()
            if session_model:
                session_model.updated_at = datetime.now()
                db.commit()

            return self._to_domain_model_message(message_model)

    def update_session_model(
        self,
        session_id: str,
        model_provider: str,
        model_name: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        更新会话的模型选择

        Args:
            session_id: 会话ID
            model_provider: AI服务提供商
            model_name: 模型名称
            user_id: 用户ID（可选，用于权限验证）

        Returns:
            是否更新成功
        """
        try:
            with self._get_db_session() as db:
                # 构建查询
                query = db.query(SessionModel).filter(SessionModel.session_id == session_id)
                if user_id:
                    query = query.filter(SessionModel.user_id == user_id)

                session_model = query.first()
                if not session_model:
                    logger.warning(f"会话 {session_id} 不存在，无法更新模型")
                    return False

                # 更新模型信息
                session_model.model_provider = model_provider
                session_model.model_name = model_name
                session_model.updated_at = datetime.now()

                db.commit()
                logger.info(
                    f"会话 {session_id} 的模型已更新为 {model_provider}:{model_name}"
                )
                return True

        except Exception as e:
            logger.error(f"更新会话模型失败: {e}", exc_info=True)
            return False

    def update_session_tokens(
        self,
        session_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int
    ) -> bool:
        """
        更新会话的token累计（如果消息已单独保存，此方法用于更新会话级别的统计）

        Args:
            session_id: 会话ID
            prompt_tokens: 本次对话的prompt token数
            completion_tokens: 本次对话的completion token数
            total_tokens: 本次对话的总token数

        Returns:
            是否更新成功
        """
        try:
            with self._get_db_session() as db:
                session_model = db.query(SessionModel).filter(
                    SessionModel.session_id == session_id
                ).first()

                if not session_model:
                    logger.warning(f"会话 {session_id} 不存在，无法更新token统计")
                    return False

                # 累加token数
                session_model.total_prompt_tokens = (session_model.total_prompt_tokens or 0) + prompt_tokens
                session_model.total_completion_tokens = (session_model.total_completion_tokens or 0) + completion_tokens
                session_model.total_tokens = (session_model.total_tokens or 0) + total_tokens
                session_model.updated_at = datetime.now()

                db.commit()
                logger.debug(
                    f"会话 {session_id} 的token统计已更新: "
                    f"总计={session_model.total_tokens}"
                )
                return True

        except Exception as e:
            logger.error(f"更新会话token统计失败: {e}", exc_info=True)
            return False

