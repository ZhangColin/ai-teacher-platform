package com.platform.domain.session;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 会话领域实体
 *
 * 对应Python: backend/src/domain/entities/session.py
 *
 * @author AI Teacher Platform
 */
@Data
public class Session {

    /**
     * 会话ID
     */
    private String sessionId;

    /**
     * 用户ID
     */
    private String userId;

    /**
     * 工具ID
     */
    private String toolId;

    /**
     * 会话标题
     */
    private String title;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}
