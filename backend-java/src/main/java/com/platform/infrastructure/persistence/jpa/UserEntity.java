package com.platform.infrastructure.persistence.jpa;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 用户JPA实体
 *
 * 对应Python: backend/src/db_models.py UserModel (第11-27行)
 * 对应数据库表: users
 *
 * @author AI Teacher Platform
 */
@Entity
@Table(name = "users", indexes = {
    @Index(name = "idx_username", columnList = "username"),
    @Index(name = "idx_email", columnList = "email"),
    @Index(name = "idx_phone", columnList = "phone"),
    @Index(name = "idx_is_admin", columnList = "is_admin")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserEntity {

    /**
     * 用户ID（主键）
     * 对应Python: user_id = Column(CHAR(36), primary_key=True)
     */
    @Id
    @Column(name = "user_id", columnDefinition = "CHAR(36)", length = 36)
    private String userId;

    /**
     * 用户名（唯一）
     * 对应Python: username = Column(String(50), unique=True, nullable=False, index=True)
     */
    @Column(name = "username", length = 50, unique = true, nullable = false)
    private String username;

    /**
     * 昵称
     * 对应Python: nickname = Column(String(50), nullable=True)
     */
    @Column(name = "nickname", length = 50)
    private String nickname;

    /**
     * 邮箱（唯一）
     * 对应Python: email = Column(String(255), unique=True, nullable=True, index=True)
     */
    @Column(name = "email", length = 255, unique = true)
    private String email;

    /**
     * 手机号（唯一）
     * 对应Python: phone = Column(String(11), unique=True, nullable=True, index=True)
     */
    @Column(name = "phone", length = 11, unique = true)
    private String phone;

    /**
     * 密码哈希
     * 对应Python: password_hash = Column(String(255), nullable=False)
     */
    @Column(name = "password_hash", nullable = false)
    private String passwordHash;

    /**
     * 头像URL
     * 对应Python: avatar = Column(String(500), nullable=True)
     */
    @Column(name = "avatar", length = 500)
    private String avatar;

    /**
     * 是否为管理员
     * 对应Python: is_admin = Column(Boolean, nullable=False, default=False, index=True)
     */
    @Column(name = "is_admin", nullable = false)
    private Boolean isAdmin = false;

    /**
     * 创建时间
     * 对应Python: created_at = Column(DateTime, nullable=False, default=datetime.now)
     */
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /**
     * 更新时间（数据库自动更新）
     * 注意：Python模型中没有此字段，但建议添加
     */
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    /**
     * 用户的关系映射
     * 注意：为了延迟加载，这些关系在查询时需要特殊处理
     */

    /**
     * 用户的会话列表（一对多）
     * 对应Python: sessions = relationship("SessionModel", back_populates="user", cascade="all, delete-orphan")
     */
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<SessionEntity> sessions = new ArrayList<>();

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
