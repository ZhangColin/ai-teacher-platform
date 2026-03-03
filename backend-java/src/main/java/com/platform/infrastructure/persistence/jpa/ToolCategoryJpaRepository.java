package com.platform.infrastructure.persistence.jpa;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * ToolCategory JPA Repository
 */
@Repository
public interface ToolCategoryJpaRepository extends JpaRepository<ToolCategoryEntity, String> {

    /**
     * 按order排序获取所有分类
     */
    List<ToolCategoryEntity> findAllByOrderByOrderAsc();
}
