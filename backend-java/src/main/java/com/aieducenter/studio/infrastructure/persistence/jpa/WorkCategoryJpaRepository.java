package com.aieducenter.studio.infrastructure.persistence.jpa;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * WorkCategory JPA Repository
 */
@Repository
public interface WorkCategoryJpaRepository extends JpaRepository<WorkCategoryEntity, String> {
    List<WorkCategoryEntity> findAllByOrderByOrderAsc();
}
