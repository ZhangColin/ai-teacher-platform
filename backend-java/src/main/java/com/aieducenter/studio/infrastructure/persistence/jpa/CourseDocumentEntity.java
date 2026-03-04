package com.platform.infrastructure.persistence.jpa;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * 课程文档JPA实体
 *
 * 对应Python: backend/src/db_models.py中的CourseDocumentModel
 */
@Entity
@Table(name = "course_documents", indexes = {
    @Index(name = "idx_category_id", columnList = "category_id"),
    @Index(name = "idx_order", columnList = "order")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CourseDocumentEntity {

    @Id
    @Column(name = "id", columnDefinition = "CHAR(36)", length = 36)
    private String id;

    @Column(name = "title", nullable = false, length = 200)
    private String title;

    @Column(name = "category_id", nullable = false, columnDefinition = "CHAR(36)", length = 36)
    private String categoryId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id", insertable = false, updatable = false)
    private CourseCategoryEntity category;

    @Column(name = "content", columnDefinition = "TEXT")
    private String content;

    @Column(name = "`order`", nullable = false)
    private Integer order;

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
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
