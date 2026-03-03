package com.platform.application.service;

import com.platform.infrastructure.persistence.jpa.CommonToolEntity;
import com.platform.infrastructure.persistence.jpa.CommonToolJpaRepository;
import com.platform.infrastructure.persistence.jpa.ToolCategoryEntity;
import com.platform.infrastructure.persistence.jpa.ToolCategoryJpaRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * 通用工具服务
 *
 * 对应Python: backend/src/services/common_tool_service.py
 *
 * @author AI Teacher Platform
 */
@Service
public class CommonToolService {

    private static final Logger logger = LoggerFactory.getLogger(CommonToolService.class);

    private final ToolCategoryJpaRepository categoryRepository;
    private final CommonToolJpaRepository toolRepository;

    public CommonToolService(
            ToolCategoryJpaRepository categoryRepository,
            CommonToolJpaRepository toolRepository
    ) {
        this.categoryRepository = categoryRepository;
        this.toolRepository = toolRepository;
    }

    /**
     * 获取所有分类及其工具
     */
    public List<CategoryWithTools> getCategoriesWithTools() {
        return categoryRepository.findAllByOrderByOrderAsc().stream()
            .map(category -> {
                List<CommonToolEntity> tools = toolRepository
                    .findByCategoryIdAndVisibleTrueOrderByOrderAsc(category.getId());

                if (tools.isEmpty()) {
                    return null;
                }

                return new CategoryWithTools(
                    category.getId(),
                    category.getName(),
                    category.getIcon(),
                    category.getOrder(),
                    tools.stream()
                        .map(tool -> new ToolListItem(
                            tool.getId(),
                            tool.getName(),
                            tool.getDescription(),
                            tool.getType().name(),
                            tool.getIcon(),
                            tool.getOrder()
                        ))
                        .collect(Collectors.toList())
                );
            })
            .filter(java.util.Objects::nonNull)
            .collect(Collectors.toList());
    }

    /**
     * 根据ID获取工具详情
     */
    public CommonToolEntity getToolDetail(String toolId) {
        return toolRepository.findById(toolId)
            .filter(tool -> Boolean.TRUE.equals(tool.getVisible()))
            .orElse(null);
    }

    /**
     * 创建工具分类
     */
    @Transactional
    public ToolCategoryEntity createCategory(String name, String icon, Integer order) {
        ToolCategoryEntity entity = new ToolCategoryEntity();
        entity.setName(name);
        entity.setIcon(icon);
        entity.setOrder(order != null ? order : 0);

        return categoryRepository.save(entity);
    }

    /**
     * 创建通用工具
     */
    @Transactional
    public CommonToolEntity createTool(
            String name,
            String description,
            String categoryId,
            String type,
            String icon,
            String htmlPath,
            Integer order
    ) {
        CommonToolEntity entity = new CommonToolEntity();
        entity.setId(UUID.randomUUID().toString());
        entity.setName(name);
        entity.setDescription(description);
        entity.setCategoryId(categoryId);
        entity.setType(com.platform.domain.tool.CommonToolType.valueOf(type));
        entity.setIcon(icon);
        entity.setHtmlPath(htmlPath);
        entity.setOrder(order != null ? order : 0);
        entity.setVisible(true);

        return toolRepository.save(entity);
    }

    /**
     * 更新工具
     */
    @Transactional
    public CommonToolEntity updateTool(
            String toolId,
            String name,
            String description,
            String icon,
            String htmlPath,
            Integer order
    ) {
        return toolRepository.findById(toolId)
            .map(entity -> {
                if (name != null) entity.setName(name);
                if (description != null) entity.setDescription(description);
                if (icon != null) entity.setIcon(icon);
                if (htmlPath != null) entity.setHtmlPath(htmlPath);
                if (order != null) entity.setOrder(order);
                return toolRepository.save(entity);
            })
            .orElse(null);
    }

    /**
     * 删除工具
     */
    @Transactional
    public boolean deleteTool(String toolId) {
        if (toolRepository.existsById(toolId)) {
            toolRepository.deleteById(toolId);
            return true;
        }
        return false;
    }

    /**
     * 分类和工具组合
     */
    public static class CategoryWithTools {
        private final String id;
        private final String name;
        private final String icon;
        private final Integer order;
        private final List<ToolListItem> tools;

        public CategoryWithTools(String id, String name, String icon, Integer order, List<ToolListItem> tools) {
            this.id = id;
            this.name = name;
            this.icon = icon;
            this.order = order;
            this.tools = tools;
        }

        public String getId() { return id; }
        public String getName() { return name; }
        public String getIcon() { return icon; }
        public Integer getOrder() { return order; }
        public List<ToolListItem> getTools() { return tools; }
    }

    public static class ToolListItem {
        private final String id;
        private final String name;
        private final String description;
        private final String type;
        private final String icon;
        private final Integer order;

        public ToolListItem(String id, String name, String description, String type, String icon, Integer order) {
            this.id = id;
            this.name = name;
            this.description = description;
            this.type = type;
            this.icon = icon;
            this.order = order;
        }

        public String getId() { return id; }
        public String getName() { return name; }
        public String getDescription() { return description; }
        public String getType() { return type; }
        public String getIcon() { return icon; }
        public Integer getOrder() { return order; }
    }
}
