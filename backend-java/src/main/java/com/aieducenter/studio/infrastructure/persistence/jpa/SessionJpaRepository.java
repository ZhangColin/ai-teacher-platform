package com.aieducenter.studio.infrastructure.persistence.jpa;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Session JPA Repository
 *
 * Spring Data JPA repository for SessionEntity
 *
 * @author AI Teacher Platform
 */
@Repository
public interface SessionJpaRepository extends JpaRepository<SessionEntity, String> {

    /**
     * 根据用户ID和工具ID获取会话列表（按更新时间倒序）
     *
     * @param userId 用户ID
     * @param toolId 工具ID
     * @return 会话列表
     */
    List<SessionEntity> findByUserIdAndToolIdOrderByUpdatedAtDesc(String userId, String toolId);

    /**
     * 根据用户ID获取所有会话（按更新时间倒序）
     *
     * @param userId 用户ID
     * @return 会话列表
     */
    List<SessionEntity> findByUserIdOrderByUpdatedAtDesc(String userId);
}
