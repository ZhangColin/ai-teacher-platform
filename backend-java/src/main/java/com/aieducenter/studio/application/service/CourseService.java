package com.aieducenter.studio.application.service;

import com.aieducenter.studio.infrastructure.persistence.jpa.CourseCategoryEntity;
import com.aieducenter.studio.infrastructure.persistence.jpa.CourseDocumentEntity;
import com.aieducenter.studio.infrastructure.persistence.jpa.CourseCategoryJpaRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * 课程文档服务
 *
 * 对应Python: backend/src/services/course_service.py
 */
@Service
public class CourseService {

    private static final Logger logger = LoggerFactory.getLogger(CourseService.class);

    private final CourseCategoryJpaRepository categoryRepository;

    public CourseService(CourseCategoryJpaRepository categoryRepository) {
        this.categoryRepository = categoryRepository;
    }

    /**
     * 获取树形结构的课程分类
     */
    public List<CategoryNode> getCategoryTree() {
        List<CourseCategoryEntity> rootCategories = categoryRepository.findByParentIdIsNullOrderByOrderAsc();

        return rootCategories.stream()
            .map(this::buildCategoryNode)
            .collect(Collectors.toList());
    }

    /**
     * 递归构建分类节点
     */
    private CategoryNode buildCategoryNode(CourseCategoryEntity category) {
        List<CategoryNode> children = category.getChildren().stream()
            .map(this::buildCategoryNode)
            .collect(Collectors.toList());

        return new CategoryNode(
            category.getId(),
            category.getName(),
            category.getParentId(),
            category.getOrder(),
            children
        );
    }

    /**
     * 创建分类
     */
    @Transactional
    public CourseCategoryEntity createCategory(String name, String parentId, Integer order) {
        CourseCategoryEntity entity = new CourseCategoryEntity();
        entity.setName(name);
        entity.setParentId(parentId);
        entity.setOrder(order != null ? order : 0);

        return categoryRepository.save(entity);
    }

    /**
     * 创建文档
     */
    @Transactional
    public CourseDocumentEntity createDocument(
            String title,
            String categoryId,
            String content,
            Integer order
    ) {
        CourseDocumentEntity entity = new CourseDocumentEntity();
        entity.setId(UUID.randomUUID().toString());
        entity.setTitle(title);
        entity.setCategoryId(categoryId);
        entity.setContent(content);
        entity.setOrder(order != null ? order : 0);

        // 需要CourseDocumentJpaRepository来保存，这里暂时返回null
        return entity;
    }

    /**
     * 分类节点（树形结构）
     */
    public static class CategoryNode {
        private final String id;
        private final String name;
        private final String parentId;
        private final Integer order;
        private final List<CategoryNode> children;

        public CategoryNode(String id, String name, String parentId, Integer order, List<CategoryNode> children) {
            this.id = id;
            this.name = name;
            this.parentId = parentId;
            this.order = order;
            this.children = children != null ? children : new ArrayList<>();
        }

        public String getId() { return id; }
        public String getName() { return name; }
        public String getParentId() { return parentId; }
        public Integer getOrder() { return order; }
        public List<CategoryNode> getChildren() { return children; }
    }
}
