package com.aieducenter.studio.infrastructure.persistence.jpa;

import com.aieducenter.studio.domain.ai.MessageRole;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Message JPA Repository
 *
 * Spring Data JPA repository for MessageEntity
 *
 * @author AI Teacher Platform
 */
@Repository
public interface MessageJpaRepository extends JpaRepository<MessageEntity, String> {

    /**
     * 根据会话ID获取所有消息（按创建时间正序）
     *
     * @param sessionId 会话ID
     * @return 消息列表
     */
    List<MessageEntity> findBySessionIdOrderByCreatedAtAsc(String sessionId);

    /**
     * 根据会话ID和角色获取消息
     *
     * @param sessionId 会话ID
     * @param role 消息角色
     * @return 消息列表
     */
    List<MessageEntity> findBySessionIdAndRole(String sessionId, MessageRole role);
}
