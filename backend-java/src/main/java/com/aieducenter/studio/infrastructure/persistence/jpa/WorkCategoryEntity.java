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
 * 作品分类JPA实体
 *
 * 对应Python: backend/src/db_models.py中的WorkCategoryModel
 */
@Entity
@Table(name = "work_categories", indexes = {
    @Index(name = "idx_order", columnList = "order")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
public class WorkCategoryEntity {

    @Id
    @Column(name = "id", columnDefinition = "CHAR(36)", length = 36)
    private String id;

    @Column(name = "name", nullable = false, unique = true, length = 50)
    private String name;

    @Column(name = "icon", length = 50)
    private String icon;

    @Column(name = "`order`", nullable = false)
    private Integer order;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @OneToMany(mappedBy = "category", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<WorkEntity> works = new ArrayList<>();

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
