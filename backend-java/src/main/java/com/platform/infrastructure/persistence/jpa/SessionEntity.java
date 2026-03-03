package com.platform.infrastructure.persistence.jpa;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

/**
 * 会话JPA实体（占位实现）
 *
 * 对应Python: backend/src/db_models.py SessionModel
 * 完整实现将在后续Task中完成
 *
 * @author AI Teacher Platform
 */
@Entity
@Table(name = "sessions")
@Data
public class SessionEntity {

    @Id
    @Column(name = "session_id", columnDefinition = "CHAR(36)", length = 36)
    private String sessionId;

    @Column(name = "user_id", columnDefinition = "CHAR(36)", length = 36, nullable = false)
    private String userId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", insertable = false, updatable = false)
    private UserEntity user;

    @Column(name = "tool_id", nullable = false)
    private String toolId;

    @Column(name = "title", nullable = false)
    private String title;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
