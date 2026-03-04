package com.aieducenter.studio.infrastructure.persistence.jpa;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * CourseCategory JPA Repository
 */
@Repository
public interface CourseCategoryJpaRepository extends JpaRepository<CourseCategoryEntity, String> {
    List<CourseCategoryEntity> findByParentIdOrderByOrderAsc(String parentId);
    List<CourseCategoryEntity> findByParentIdIsNullOrderByOrderAsc();
}

/**
 * CourseDocument JPA Repository
 */
@Repository
interface CourseDocumentJpaRepository extends JpaRepository<CourseDocumentEntity, String> {
    List<CourseDocumentEntity> findByCategoryIdOrderByOrderAsc(String categoryId);
}
