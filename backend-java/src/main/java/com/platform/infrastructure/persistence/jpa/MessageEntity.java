package com.platform.infrastructure.persistence.jpa;

import com.platform.domain.ai.MessageRole;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * 消息JPA实体
 *
 * 对应Python: backend/src/db_models.py中的MessageModel
 * 对应数据库表: messages
 *
 * @author AI Teacher Platform
 */
@Entity
@Table(name = "messages", indexes = {
    @Index(name = "idx_session_id", columnList = "session_id"),
    @Index(name = "idx_created_at", columnList = "created_at")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
public class MessageEntity {

    /**
     * 消息ID（主键）
     * 对应Python: message_id: Column(CHAR(36), primary_key=True)
     */
    @Id
    @Column(name = "message_id", columnDefinition = "CHAR(36)", length = 36)
    private String messageId;

    /**
     * 所属会话ID（外键）
     * 对应Python: session_id: Column(CHAR(36), ForeignKey(...))
     */
    @Column(name = "session_id", columnDefinition = "CHAR(36)", length = 36, nullable = false)
    private String sessionId;

    /**
     * 消息角色
     * 对应Python: role: Column(Enum(MessageRole))
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "role", nullable = false)
    private MessageRole role;

    /**
     * 消息内容
     * 对应Python: content: Column(Text, nullable=False)
     */
    @Column(name = "content", columnDefinition = "TEXT", nullable = false)
    private String content;

    /**
     * 创建时间
     * 对应Python: created_at: Column(DateTime, default=func.now())
     */
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    /**
     * 关联的会话实体（多对一）
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "session_id", insertable = false, updatable = false)
    private SessionEntity session;

    /**
     * 创建前自动生成ID和时间戳
     */
    @PrePersist
    protected void onCreate() {
        if (messageId == null || messageId.isEmpty()) {
            messageId = UUID.randomUUID().toString();
        }
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
    }
}
