"""会话服务：管理 Agent 会话"""
import uuid
from datetime import datetime
from typing import Dict, Optional
from ..models import Agent


class SessionService:
    """会话管理服务"""
    
    def __init__(self):
        """初始化会话服务"""
        # MVP 阶段：使用内存存储会话信息
        # 未来扩展：可改为数据库存储
        self.sessions: Dict[str, dict] = {}  # {session_id: {agent_id, created_at, ...}}
    
    def create_session(self, agent: Agent) -> str:
        """
        创建新会话
        
        Args:
            agent: Agent 实例
            
        Returns:
            会话 ID (UUID)
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "agent_id": agent.agent_id,
            "created_at": datetime.now()
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """
        获取会话信息
        
        Args:
            session_id: 会话 ID
            
        Returns:
            会话信息字典，如果不存在返回 None
        """
        return self.sessions.get(session_id)
    
    def session_exists(self, session_id: str) -> bool:
        """
        检查会话是否存在
        
        Args:
            session_id: 会话 ID
            
        Returns:
            是否存在
        """
        return session_id in self.sessions

