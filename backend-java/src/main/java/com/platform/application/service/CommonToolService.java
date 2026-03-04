package com.platform.application.service;

import com.platform.infrastructure.persistence.jpa.CommonToolEntity;
import com.platform.infrastructure.persistence.jpa.CommonToolJpaRepository;
import com.platform.infrastructure.persistence.jpa.ToolCategoryEntity;
import com.platform.infrastructure.persistence.jpa.ToolCategoryJpaRepository;
import com.platform.interfaces.rest.dto.admin.AdminToolDTO;
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

    // ==================== 管理员方法 ====================

    /**
     * 获取所有工具（管理后台）
     * 对应Python: get_all_tools_admin()
     */
    public AdminToolListResult getAllToolsAdmin(int page, int pageSize, String categoryId, String toolType, Boolean visible) {
        List<CommonToolEntity> tools;

        // 构建查询条件
        if (categoryId != null && toolType != null && visible != null) {
            tools = toolRepository.findByCategoryIdAndTypeAndVisibleTrueOrderByOrderAsc(
                categoryId, com.platform.domain.tool.CommonToolType.valueOf(toolType));
        } else if (categoryId != null && visible != null) {
            tools = toolRepository.findByCategoryIdAndVisibleTrueOrderByOrderAsc(categoryId);
        } else if (categoryId != null) {
            tools = toolRepository.findByCategoryIdOrderByOrderAsc(categoryId);
        } else {
            tools = toolRepository.findAll();
        }

        // 分页
        int start = (page - 1) * pageSize;
        int end = Math.min(start + pageSize, tools.size());
        List<CommonToolEntity> pagedTools = tools.subList(start, end);

        return new AdminToolListResult(
            pagedTools.stream()
                .map(this::convertToAdminToolDTO)
                .collect(Collectors.toList()),
            tools.size(),
            page,
            pageSize
        );
    }

    /**
     * 创建内置工具
     * 对应Python: create_built_in_tool()
     */
    @Transactional
    public CommonToolEntity createBuiltInTool(
            String name,
            String description,
            String categoryId,
            String icon,
            Integer order,
            Boolean visible,
            String systemPrompt,
            String modelConfig
    ) {
        // 验证分类存在
        if (!categoryRepository.existsById(categoryId)) {
            throw new IllegalArgumentException("分类不存在");
        }

        CommonToolEntity entity = new CommonToolEntity();
        entity.setId(UUID.randomUUID().toString());
        entity.setName(name);
        entity.setDescription(description);
        entity.setCategoryId(categoryId);
        entity.setType(com.platform.domain.tool.CommonToolType.BUILT_IN);
        entity.setIcon(icon);
        entity.setOrder(order != null ? order : 0);
        entity.setVisible(visible != null ? visible : true);
        // 注意：systemPrompt 和 modelConfig 字段不在 CommonToolEntity 中
        // 它们应该从工具配置文件中加载，而不是存储在数据库中

        return toolRepository.save(entity);
    }

    /**
     * 创建HTML工具
     * 对应Python: create_html_tool()
     */
    @Transactional
    public CommonToolEntity createHtmlTool(
            String name,
            String description,
            String categoryId,
            String htmlPath,
            String icon,
            Integer order,
            Boolean visible
    ) {
        // 验证分类存在
        if (!categoryRepository.existsById(categoryId)) {
            throw new IllegalArgumentException("分类不存在");
        }

        CommonToolEntity entity = new CommonToolEntity();
        entity.setId(UUID.randomUUID().toString());
        entity.setName(name);
        entity.setDescription(description);
        entity.setCategoryId(categoryId);
        entity.setType(com.platform.domain.tool.CommonToolType.HTML);
        entity.setIcon(icon);
        entity.setHtmlPath(htmlPath);
        entity.setOrder(order != null ? order : 0);
        entity.setVisible(visible != null ? visible : true);

        return toolRepository.save(entity);
    }

    /**
     * 更新工具（管理后台）
     * 对应Python: update_tool()
     */
    @Transactional
    public CommonToolEntity updateTool(String toolId, String name, String description, String categoryId,
                                       String icon, Integer order, Boolean visible, String systemPrompt, String modelConfig) {
        return toolRepository.findById(toolId)
            .map(entity -> {
                if (name != null) entity.setName(name);
                if (description != null) entity.setDescription(description);
                if (categoryId != null) {
                    if (!categoryRepository.existsById(categoryId)) {
                        throw new IllegalArgumentException("分类不存在");
                    }
                    entity.setCategoryId(categoryId);
                }
                if (icon != null) entity.setIcon(icon);
                if (order != null) entity.setOrder(order);
                if (visible != null) entity.setVisible(visible);
                // systemPrompt 和 modelConfig 字段不在实体中，从配置文件加载
                // if (systemPrompt != null) entity.setSystemPrompt(systemPrompt);
                // if (modelConfig != null) entity.setModelConfig(modelConfig);
                return toolRepository.save(entity);
            })
            .orElseThrow(() -> new IllegalArgumentException("工具不存在"));
    }

    /**
     * 删除工具（管理后台）
     * 对应Python: delete_tool()
     */
    @Transactional
    public String deleteTool(String toolId) {
        return toolRepository.findById(toolId)
            .map(entity -> {
                String htmlPath = entity.getHtmlPath();
                toolRepository.deleteById(toolId);
                return htmlPath;
            })
            .orElseThrow(() -> new IllegalArgumentException("工具不存在"));
    }

    /**
     * 上移工具
     * 对应Python: move_tool_up()
     */
    @Transactional
    public CommonToolEntity moveToolUp(String toolId) {
        CommonToolEntity tool = toolRepository.findById(toolId)
            .orElseThrow(() -> new IllegalArgumentException("工具不存在"));

        List<CommonToolEntity> siblings = toolRepository
            .findByCategoryIdOrderByOrderAsc(tool.getCategoryId());

        int currentIndex = siblings.indexOf(tool);
        if (currentIndex <= 0) {
            throw new IllegalArgumentException("工具已经是第一个");
        }

        // 交换位置
        CommonToolEntity prevTool = siblings.get(currentIndex - 1);
        int tempOrder = tool.getOrder();
        tool.setOrder(prevTool.getOrder());
        prevTool.setOrder(tempOrder);

        toolRepository.save(prevTool);
        return toolRepository.save(tool);
    }

    /**
     * 下移工具
     * 对应Python: move_tool_down()
     */
    @Transactional
    public CommonToolEntity moveToolDown(String toolId) {
        CommonToolEntity tool = toolRepository.findById(toolId)
            .orElseThrow(() -> new IllegalArgumentException("工具不存在"));

        List<CommonToolEntity> siblings = toolRepository
            .findByCategoryIdOrderByOrderAsc(tool.getCategoryId());

        int currentIndex = siblings.indexOf(tool);
        if (currentIndex >= siblings.size() - 1) {
            throw new IllegalArgumentException("工具已经是最后一个");
        }

        // 交换位置
        CommonToolEntity nextTool = siblings.get(currentIndex + 1);
        int tempOrder = tool.getOrder();
        tool.setOrder(nextTool.getOrder());
        nextTool.setOrder(tempOrder);

        toolRepository.save(nextTool);
        return toolRepository.save(tool);
    }

    /**
     * 切换工具可见性
     * 对应Python: toggle_tool_visibility()
     */
    @Transactional
    public VisibilityToggleResult toggleToolVisibility(String toolId) {
        CommonToolEntity tool = toolRepository.findById(toolId)
            .orElseThrow(() -> new IllegalArgumentException("工具不存在"));

        tool.setVisible(!tool.getVisible());
        CommonToolEntity saved = toolRepository.save(tool);

        String message = saved.getVisible() ? "工具已显示" : "工具已隐藏";
        return new VisibilityToggleResult(message, saved);
    }

    /**
     * 获取所有分类（管理后台）
     * 对应Python: get_all_categories_admin()
     */
    public AdminCategoryListResult getAllCategoriesAdmin() {
        List<ToolCategoryEntity> categories = categoryRepository.findAllByOrderByOrderAsc();

        return new AdminCategoryListResult(
            categories.stream()
                .map(cat -> {
                    int toolCount = toolRepository.findByCategoryIdOrderByOrderAsc(cat.getId()).size();
                    return new AdminCategoryItem(
                        cat.getId(),
                        cat.getName(),
                        cat.getOrder(),
                        toolCount
                    );
                })
                .collect(Collectors.toList()),
            categories.size()
        );
    }

    /**
     * 创建分类（管理后台）
     * 对应Python: create_category()
     */
    @Transactional
    public ToolCategoryEntity createCategory(String name, Integer order) {
        // 检查名称是否已存在 - TODO: 实现名称唯一性检查
        // if (categoryRepository.existsByName(name)) {
        //     throw new IllegalArgumentException("分类名称已存在");
        // }

        ToolCategoryEntity entity = new ToolCategoryEntity();
        entity.setId(UUID.randomUUID().toString());
        entity.setName(name);
        entity.setOrder(order != null ? order : 0);

        return categoryRepository.save(entity);
    }

    /**
     * 更新分类（管理后台）
     * 对应Python: update_category()
     */
    @Transactional
    public ToolCategoryEntity updateCategory(String categoryId, String name, Integer order) {
        return categoryRepository.findById(categoryId)
            .map(entity -> {
                if (name != null && !name.equals(entity.getName())) {
                    // TODO: 检查名称唯一性
                    // if (categoryRepository.existsByName(name)) {
                    //     throw new IllegalArgumentException("分类名称已被使用");
                    // }
                    entity.setName(name);
                }
                if (order != null) entity.setOrder(order);
                return categoryRepository.save(entity);
            })
            .orElseThrow(() -> new IllegalArgumentException("分类不存在"));
    }

    /**
     * 删除分类（管理后台）
     * 对应Python: delete_category()
     */
    @Transactional
    public void deleteCategory(String categoryId) {
        // 检查分类是否存在
        if (!categoryRepository.existsById(categoryId)) {
            throw new IllegalArgumentException("分类不存在");
        }

        // 检查是否还有工具
        List<CommonToolEntity> tools = toolRepository.findByCategoryIdOrderByOrderAsc(categoryId);
        if (!tools.isEmpty()) {
            throw new IllegalArgumentException("分类下还有" + tools.size() + "个工具，无法删除");
        }

        categoryRepository.deleteById(categoryId);
    }

    /**
     * 上移分类
     * 对应Python: move_category_up()
     */
    @Transactional
    public ToolCategoryEntity moveCategoryUp(String categoryId) {
        ToolCategoryEntity category = categoryRepository.findById(categoryId)
            .orElseThrow(() -> new IllegalArgumentException("分类不存在"));

        List<ToolCategoryEntity> categories = categoryRepository.findAllByOrderByOrderAsc();

        int currentIndex = categories.indexOf(category);
        if (currentIndex <= 0) {
            throw new IllegalArgumentException("分类已经是第一个");
        }

        // 交换位置
        ToolCategoryEntity prevCategory = categories.get(currentIndex - 1);
        int tempOrder = category.getOrder();
        category.setOrder(prevCategory.getOrder());
        prevCategory.setOrder(tempOrder);

        categoryRepository.save(prevCategory);
        return categoryRepository.save(category);
    }

    /**
     * 下移分类
     * 对应Python: move_category_down()
     */
    @Transactional
    public ToolCategoryEntity moveCategoryDown(String categoryId) {
        ToolCategoryEntity category = categoryRepository.findById(categoryId)
            .orElseThrow(() -> new IllegalArgumentException("分类不存在"));

        List<ToolCategoryEntity> categories = categoryRepository.findAllByOrderByOrderAsc();

        int currentIndex = categories.indexOf(category);
        if (currentIndex >= categories.size() - 1) {
            throw new IllegalArgumentException("分类已经是最后一个");
        }

        // 交换位置
        ToolCategoryEntity nextCategory = categories.get(currentIndex + 1);
        int tempOrder = category.getOrder();
        category.setOrder(nextCategory.getOrder());
        nextCategory.setOrder(tempOrder);

        categoryRepository.save(nextCategory);
        return categoryRepository.save(category);
    }

    // ==================== 辅助方法 ====================

    private com.platform.interfaces.rest.dto.admin.AdminToolDTO convertToAdminToolDTO(CommonToolEntity entity) {
        ToolCategoryEntity category = categoryRepository.findById(entity.getCategoryId()).orElse(null);

        return com.platform.interfaces.rest.dto.admin.AdminToolDTO.builder()
            .toolId(entity.getId())
            .name(entity.getName())
            .description(entity.getDescription())
            .categoryId(entity.getCategoryId())
            .categoryName(category != null ? category.getName() : null)
            .icon(entity.getIcon())
            .type(entity.getType().name().toLowerCase())
            .order(entity.getOrder())
            .visible(entity.getVisible())
            .htmlPath(entity.getHtmlPath())
            // systemPrompt 和 modelConfig 从配置文件加载，不从数据库获取
            .systemPrompt("")
            .modelConfig("")
            .build();
    }

    // ==================== 管理员结果类 ====================

    public static class AdminToolListResult {
        private final List<com.platform.interfaces.rest.dto.admin.AdminToolDTO> tools;
        private final int total;
        private final int page;
        private final int pageSize;

        public AdminToolListResult(List<com.platform.interfaces.rest.dto.admin.AdminToolDTO> tools, int total, int page, int pageSize) {
            this.tools = tools;
            this.total = total;
            this.page = page;
            this.pageSize = pageSize;
        }

        public List<com.platform.interfaces.rest.dto.admin.AdminToolDTO> getTools() { return tools; }
        public int getTotal() { return total; }
        public int getPage() { return page; }
        public int getPageSize() { return pageSize; }
    }

    public static class VisibilityToggleResult {
        private final String message;
        private final CommonToolEntity tool;

        public VisibilityToggleResult(String message, CommonToolEntity tool) {
            this.message = message;
            this.tool = tool;
        }

        public String getMessage() { return message; }
        public CommonToolEntity getTool() { return tool; }
    }

    public static class AdminCategoryListResult {
        private final List<AdminCategoryItem> categories;
        private final int total;

        public AdminCategoryListResult(List<AdminCategoryItem> categories, int total) {
            this.categories = categories;
            this.total = total;
        }

        public List<AdminCategoryItem> getCategories() { return categories; }
        public int getTotal() { return total; }
    }

    public static class AdminCategoryItem {
        private final String categoryId;
        private final String name;
        private final Integer order;
        private final int toolCount;

        public AdminCategoryItem(String categoryId, String name, Integer order, int toolCount) {
            this.categoryId = categoryId;
            this.name = name;
            this.order = order;
            this.toolCount = toolCount;
        }

        public String getCategoryId() { return categoryId; }
        public String getName() { return name; }
        public Integer getOrder() { return order; }
        public int getToolCount() { return toolCount; }
    }
}
