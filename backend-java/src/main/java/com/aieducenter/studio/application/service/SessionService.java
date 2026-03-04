package com.platform.application.service;

import com.platform.domain.ai.Message;
import com.platform.domain.ai.MessageRole;
import com.platform.domain.session.Session;
import com.platform.infrastructure.persistence.jpa.MessageEntity;
import com.platform.infrastructure.persistence.jpa.MessageJpaRepository;
import com.platform.infrastructure.persistence.jpa.SessionEntity;
import com.platform.infrastructure.persistence.jpa.SessionJpaRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * 会话服务
 *
 * 对应Python: backend/src/services/session_service.py
 * 负责会话和消息的管理
 *
 * @author AI Teacher Platform
 */
@Service
public class SessionService {

    private static final Logger logger = LoggerFactory.getLogger(SessionService.class);

    private final SessionJpaRepository sessionJpaRepository;
    private final MessageJpaRepository messageJpaRepository;

    public SessionService(
            SessionJpaRepository sessionJpaRepository,
            MessageJpaRepository messageJpaRepository
    ) {
        this.sessionJpaRepository = sessionJpaRepository;
        this.messageJpaRepository = messageJpaRepository;
    }

    /**
     * 创建新会话
     *
     * 对应Python: def create_session(...)
     *
     * @param userId 用户ID
     * @param toolId 工具ID
     * @param title 会话标题
     * @return 新会话
     */
    @Transactional
    public Session createSession(String userId, String toolId, String title) {
        SessionEntity entity = new SessionEntity();
        entity.setUserId(userId);
        entity.setToolId(toolId);
        entity.setTitle(title != null ? title : "新对话");

        SessionEntity saved = sessionJpaRepository.save(entity);
        logger.info("创建会话成功: sessionId={}, userId={}, toolId={}",
            saved.getSessionId(), userId, toolId);

        return toDomainModel(saved);
    }

    /**
     * 根据ID获取会话
     *
     * 对应Python: def get_session_by_id(...)
     *
     * @param sessionId 会话ID
     * @param userId 用户ID（可选，用于验证权限）
     * @return 会话，不存在返回null
     */
    public Session getSessionById(String sessionId, String userId) {
        return sessionJpaRepository.findById(sessionId)
            .filter(entity -> userId == null || userId.equals(entity.getUserId()))
            .map(this::toDomainModel)
            .orElse(null);
    }

    /**
     * 获取用户在某工具下的所有会话
     *
     * 对应Python: def get_sessions_by_user_and_tool(...)
     *
     * @param userId 用户ID
     * @param toolId 工具ID
     * @return 会话列表（按更新时间倒序）
     */
    public List<Session> getSessionsByUserAndTool(String userId, String toolId) {
        return sessionJpaRepository.findByUserIdAndToolIdOrderByUpdatedAtDesc(userId, toolId)
            .stream()
            .map(this::toDomainModel)
            .collect(Collectors.toList());
    }

    /**
     * 更新会话标题
     *
     * 对应Python: def update_session_title(...)
     *
     * @param sessionId 会话ID
     * @param newTitle 新标题
     * @param userId 用户ID（可选，用于验证权限）
     * @return 更新后的会话，失败返回null
     */
    @Transactional
    public Session updateTitle(String sessionId, String newTitle, String userId) {
        return sessionJpaRepository.findById(sessionId)
            .filter(entity -> userId == null || userId.equals(entity.getUserId()))
            .map(entity -> {
                entity.setTitle(newTitle);
                SessionEntity saved = sessionJpaRepository.save(entity);
                return toDomainModel(saved);
            })
            .orElse(null);
    }

    /**
     * 删除会话（级联删除消息）
     *
     * 对应Python: def delete_session(...)
     *
     * @param sessionId 会话ID
     * @param userId 用户ID（可选，用于验证权限）
     * @return 是否删除成功
     */
    @Transactional
    public boolean deleteSession(String sessionId, String userId) {
        return sessionJpaRepository.findById(sessionId)
            .filter(entity -> userId == null || userId.equals(entity.getUserId()))
            .map(entity -> {
                sessionJpaRepository.delete(entity);
                logger.info("删除会话成功: sessionId={}", sessionId);
                return true;
            })
            .orElse(false);
    }

    /**
     * 添加消息到会话
     *
     * 对应Python: def add_message(...)
     *
     * @param sessionId 会话ID
     * @param role 消息角色
     * @param content 消息内容
     * @param userId 用户ID（可选，用于验证权限）
     * @return 创建的消息
     */
    @Transactional
    public Message addMessage(String sessionId, String role, String content, String userId) {
        // 验证会话存在
        SessionEntity sessionEntity = sessionJpaRepository.findById(sessionId)
            .filter(entity -> userId == null || userId.equals(entity.getUserId()))
            .orElseThrow(() -> new IllegalArgumentException("Session not found: " + sessionId));

        // 创建消息
        MessageEntity messageEntity = new MessageEntity();
        messageEntity.setSessionId(sessionId);
        messageEntity.setRole(MessageRole.fromValue(role));
        messageEntity.setContent(content);

        MessageEntity saved = messageJpaRepository.save(messageEntity);

        // 更新会话时间戳
        sessionEntity.setUpdatedAt(LocalDateTime.now());
        sessionJpaRepository.save(sessionEntity);

        logger.debug("添加消息成功: messageId={}, sessionId={}", saved.getMessageId(), sessionId);

        return toDomainModelMessage(saved);
    }

    /**
     * 获取会话的所有消息
     *
     * 对应Python: def get_messages_by_session(...)
     *
     * @param sessionId 会话ID
     * @param userId 用户ID（可选，用于验证权限）
     * @return 消息列表（按创建时间正序）
     */
    public List<Message> getMessagesBySession(String sessionId, String userId) {
        // 验证会话存在
        if (!sessionJpaRepository.existsById(sessionId)) {
            return List.of();
        }

        return messageJpaRepository.findBySessionIdOrderByCreatedAtAsc(sessionId)
            .stream()
            .map(this::toDomainModelMessage)
            .collect(Collectors.toList());
    }

    /**
     * 获取会话的所有消息（别名方法）
     *
     * 对应Python: def get_session_messages(...)
     */
    public List<Message> getSessionMessages(String sessionId) {
        return messageJpaRepository.findBySessionIdOrderByCreatedAtAsc(sessionId)
            .stream()
            .map(this::toDomainModelMessage)
            .collect(Collectors.toList());
    }

    /**
     * 获取会话消息数量
     *
     * @param sessionId 会话ID
     * @param userId 用户ID
     * @return 消息数量
     */
    public int getMessageCount(String sessionId, String userId) {
        // 验证会话存在
        if (!sessionJpaRepository.existsById(sessionId)) {
            return 0;
        }

        return messageJpaRepository.findBySessionIdOrderByCreatedAtAsc(sessionId).size();
    }

    /**
     * 将JPA实体转换为领域模型（Session）
     */
    private Session toDomainModel(SessionEntity entity) {
        Session session = new Session();
        session.setSessionId(entity.getSessionId());
        session.setUserId(entity.getUserId());
        session.setToolId(entity.getToolId());
        session.setTitle(entity.getTitle());
        session.setCreatedAt(entity.getCreatedAt());
        session.setUpdatedAt(entity.getUpdatedAt());
        return session;
    }

    /**
     * 将JPA实体转换为领域模型（Message）
     */
    private Message toDomainModelMessage(MessageEntity entity) {
        Message message = new Message();
        message.setId(entity.getMessageId());
        message.setSessionId(entity.getSessionId());
        message.setRole(entity.getRole());
        message.setContent(entity.getContent());
        message.setCreatedAt(entity.getCreatedAt());
        return message;
    }
}
