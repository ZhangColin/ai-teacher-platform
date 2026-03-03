package com.platform.infrastructure.persistence.jpa;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * CommonTool JPA Repository
 */
@Repository
public interface CommonToolJpaRepository extends JpaRepository<CommonToolEntity, String> {

    /**
     * 获取分类下的可见工具（按order排序）
     */
    List<CommonToolEntity> findByCategoryIdAndVisibleTrueOrderByOrderAsc(String categoryId);

    /**
     * 根据ID获取可见工具
     */
    List<CommonToolEntity> findByIdAndVisibleTrue(String id);
}
