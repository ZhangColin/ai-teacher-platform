package com.aieducenter.studio.infrastructure.persistence.jpa;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Work JPA Repository
 */
@Repository
public interface WorkJpaRepository extends JpaRepository<WorkEntity, String> {
    List<WorkEntity> findByCategoryIdAndVisibleTrueOrderByOrderAsc(String categoryId);
}
