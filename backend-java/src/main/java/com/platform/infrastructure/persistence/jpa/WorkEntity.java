package com.platform.infrastructure.persistence.jpa;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * 作品JPA实体
 *
 * 对应Python: backend/src/db_models.py中的WorkModel
 */
@Entity
@Table(name = "works", indexes = {
    @Index(name = "idx_category_id", columnList = "category_id"),
    @Index(name = "idx_visible", columnList = "visible"),
    @Index(name = "idx_work_category_order", columnList = "category_id, `order`")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
public class WorkEntity {

    @Id
    @Column(name = "id", columnDefinition = "CHAR(36)", length = 36)
    private String id;

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    @Column(name = "description", nullable = false, length = 200)
    private String description;

    @Column(name = "category_id", nullable = false, columnDefinition = "CHAR(36)", length = 36)
    private String categoryId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id", insertable = false, updatable = false)
    private WorkCategoryEntity category;

    @Column(name = "icon", length = 50)
    private String icon;

    @Column(name = "html_path", nullable = false, length = 255)
    private String htmlPath;

    @Column(name = "`order`", nullable = false)
    private Integer order;

    @Column(name = "visible", nullable = false)
    private Boolean visible;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        if (id == null || id.isEmpty()) {
            id = UUID.randomUUID().toString();
        }
        LocalDateTime now = LocalDateTime.now();
        createdAt = now;
        updatedAt = now;
        if (visible == null) {
            visible = true;
        }
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
