package com.aieducenter.studio.infrastructure.persistence.jpa;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * 会话JPA实体
 *
 * 对应Python: backend/src/db_models.py中的SessionModel
 * 对应数据库表: sessions
 *
 * @author AI Teacher Platform
 */
@Entity
@Table(name = "sessions", indexes = {
    @Index(name = "idx_user_id", columnList = "user_id"),
    @Index(name = "idx_tool_id", columnList = "tool_id"),
    @Index(name = "idx_updated_at", columnList = "updated_at")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SessionEntity {

    /**
     * 会话ID（主键）
     * 对应Python: session_id: Column(CHAR(36), primary_key=True)
     */
    @Id
    @Column(name = "session_id", columnDefinition = "CHAR(36)", length = 36)
    private String sessionId;

    /**
     * 用户ID（外键）
     * 对应Python: user_id: Column(CHAR(36), ForeignKey(...))
     */
    @Column(name = "user_id", columnDefinition = "CHAR(36)", length = 36, nullable = false)
    private String userId;

    /**
     * 关联的用户实体（多对一）
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", insertable = false, updatable = false)
    private UserEntity user;

    /**
     * 工具ID
     * 对应Python: tool_id: Column(String(50), nullable=False)
     */
    @Column(name = "tool_id", nullable = false)
    private String toolId;

    /**
     * 会话标题
     * 对应Python: title: Column(String(200), nullable=False)
     */
    @Column(name = "title", nullable = false)
    private String title;

    /**
     * 创建时间
     * 对应Python: created_at: Column(DateTime, default=func.now())
     */
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    /**
     * 更新时间
     * 对应Python: updated_at: Column(DateTime, default=func.now(), onupdate=func.now())
     */
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    /**
     * 关联的消息列表（一对多）
     * 级联删除：删除会话时自动删除所有消息
     */
    @OneToMany(mappedBy = "session", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<MessageEntity> messages = new ArrayList<>();

    /**
     * 创建前自动生成ID和时间戳
     */
    @PrePersist
    protected void onCreate() {
        if (sessionId == null || sessionId.isEmpty()) {
            sessionId = UUID.randomUUID().toString();
        }
        LocalDateTime now = LocalDateTime.now();
        if (createdAt == null) {
            createdAt = now;
        }
        updatedAt = now;
    }

    /**
     * 更新前自动更新时间戳
     */
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
