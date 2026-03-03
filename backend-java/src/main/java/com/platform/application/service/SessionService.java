package com.platform.application.service;

import com.platform.domain.ai.Message;
import com.platform.domain.session.Session;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 会话服务（占位符）
 *
 * 对应Python: backend/src/services/session_service.py
 * TODO: Task 12 实现
 *
 * @author AI Teacher Platform
 */
@Service
public class SessionService {

    /**
     * 创建新会话
     *
     * @param userId 用户ID
     * @param toolId 工具ID
     * @param title 初始标题
     * @return 新会话
     */
    public Session createSession(String userId, String toolId, String title) {
        // TODO: 实现会话创建
        Session session = new Session();
        session.setSessionId("placeholder-session-id");
        session.setUserId(userId);
        session.setToolId(toolId);
        session.setTitle(title);
        return session;
    }

    /**
     * 获取会话消息历史
     *
     * @param sessionId 会话ID
     * @return 消息列表
     */
    public List<Message> getSessionMessages(String sessionId) {
        // TODO: 实现消息历史查询
        return List.of();
    }

    /**
     * 添加消息到会话
     *
     * @param sessionId 会话ID
     * @param role 消息角色
     * @param content 消息内容
     * @param userId 用户ID
     */
    public void addMessage(String sessionId, String role, String content, String userId) {
        // TODO: 实现消息添加
    }

    /**
     * 获取会话消息数量
     *
     * @param sessionId 会话ID
     * @param userId 用户ID
     * @return 消息数量
     */
    public int getMessageCount(String sessionId, String userId) {
        // TODO: 实现消息计数
        return 0;
    }
}
