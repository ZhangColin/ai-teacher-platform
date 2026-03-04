package com.platform.interfaces.rest;

import com.platform.application.service.CommonToolService;
import com.platform.interfaces.rest.dto.admin.*;
import com.platform.interfaces.rest.dto.UserInfo;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.UUID;

/**
 * 管理后台控制器
 *
 * 对应Python: backend/src/interfaces/routers/admin/tools.py
 *
 * 端点列表：
 * - GET    /api/v1/admin/common-tools - 获取工具列表
 * - POST   /api/v1/admin/common-tools/built-in - 创建内置工具
 * - POST   /api/v1/admin/common-tools/html - 创建HTML工具
 * - PATCH  /api/v1/admin/common-tools/{tool_id} - 更新工具
 * - DELETE /api/v1/admin/common-tools/{tool_id} - 删除工具
 * - POST   /api/v1/admin/common-tools/{tool_id}/move-up - 上移工具
 * - POST   /api/v1/admin/common-tools/{tool_id}/move-down - 下移工具
 * - POST   /api/v1/admin/common-tools/{tool_id}/toggle-visibility - 切换可见性
 * - GET    /api/v1/admin/tool-categories - 获取工具分类列表
 * - POST   /api/v1/admin/tool-categories - 创建工具分类
 * - PATCH  /api/v1/admin/tool-categories/{category_id} - 更新工具分类
 * - DELETE /api/v1/admin/tool-categories/{category_id} - 删除工具分类
 * - POST   /api/v1/admin/tool-categories/{category_id}/move-up - 上移分类
 * - POST   /api/v1/admin/tool-categories/{category_id}/move-down - 下移分类
 *
 * @author AI Teacher Platform
 */
@RestController
@RequestMapping("/api/v1/admin")
public class AdminController {

    private static final Logger logger = LoggerFactory.getLogger(AdminController.class);

    private final CommonToolService commonToolService;

    public AdminController(CommonToolService commonToolService) {
        this.commonToolService = commonToolService;
    }

    /**
     * 管理员权限验证
     */
    private void requireAdmin(UserInfo currentUser) {
        if (currentUser == null || !Boolean.TRUE.equals(currentUser.getIsAdmin())) {
            throw new IllegalArgumentException("需要管理员权限");
        }
    }

    // ==================== 常用工具管理接口 ====================

    /**
     * 获取工具列表（管理后台）
     * GET /api/v1/admin/common-tools
     */
    @GetMapping("/common-tools")
    public ResponseEntity<AdminToolListResponse> getAdminTools(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize,
            @RequestParam(required = false) String category_id,
            @RequestParam(required = false) String type,
            @RequestParam(required = false) Boolean visible,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            CommonToolService.AdminToolListResult result = commonToolService.getAllToolsAdmin(
                page, pageSize, category_id, type, visible
            );

            return ResponseEntity.ok(AdminToolListResponse.builder()
                .tools(result.getTools())
                .total(result.getTotal())
                .page(result.getPage())
                .pageSize(result.getPageSize())
                .build());
        } catch (IllegalArgumentException e) {
            throw e; // 交给全局异常处理
        } catch (Exception e) {
            logger.error("获取工具列表失败: {}", e.getMessage(), e);
            throw new RuntimeException("获取工具列表失败: " + e.getMessage());
        }
    }

    /**
     * 创建内置工具（管理后台）
     * POST /api/v1/admin/common-tools/built-in
     */
    @PostMapping("/common-tools/built-in")
    public ResponseEntity<CreateToolResponse> createBuiltInTool(
            @Valid @RequestBody CreateBuiltInToolRequest request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            var tool = commonToolService.createBuiltInTool(
                request.getName(),
                request.getDescription(),
                request.getCategoryId(),
                request.getIcon(),
                request.getOrder(),
                request.getVisible(),
                request.getSystemPrompt(),
                request.getModelConfig()
            );

            return ResponseEntity.status(HttpStatus.CREATED).body(CreateToolResponse.builder()
                .tool(convertToAdminToolDTO(tool))
                .build());
        } catch (IllegalArgumentException e) {
            if ("分类不存在".equals(e.getMessage())) {
                throw new IllegalArgumentException("分类不存在");
            }
            throw e;
        } catch (Exception e) {
            logger.error("创建内置工具失败: {}", e.getMessage(), e);
            throw new RuntimeException("创建内置工具失败: " + e.getMessage());
        }
    }

    /**
     * 上传HTML工具（管理后台）
     * POST /api/v1/admin/common-tools/html
     */
    @PostMapping(value = "/common-tools/html", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<CreateToolResponse> createHtmlTool(
            @RequestParam("name") String name,
            @RequestParam("description") String description,
            @RequestParam("category_id") String categoryId,
            @RequestParam(value = "icon", required = false) String icon,
            @RequestParam(value = "order", defaultValue = "0") int order,
            @RequestParam(value = "visible", defaultValue = "true") boolean visible,
            @RequestParam("html_file") MultipartFile htmlFile,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            // 验证文件类型
            String filename = htmlFile.getOriginalFilename();
            if (filename == null || !filename.endsWith(".html")) {
                throw new IllegalArgumentException("只支持.html文件");
            }

            // 验证文件大小（5MB）
            if (htmlFile.getSize() > 5 * 1024 * 1024) {
                throw new IllegalArgumentException("文件大小超过5MB限制");
            }

            // 生成工具ID
            String toolId = UUID.randomUUID().toString().substring(0, 8);

            // 创建存储目录
            String uploadDir = System.getProperty("upload.dir", "static/common_tools/html");
            Path toolDir = Paths.get(uploadDir, toolId);
            Files.createDirectories(toolDir);

            // 保存文件
            Path filePath = toolDir.resolve("index.html");
            Files.write(filePath, htmlFile.getBytes());

            // 数据库存储相对路径
            String htmlPath = "common_tools/html/" + toolId + "/index.html";

            // 创建工具记录
            var tool = commonToolService.createHtmlTool(
                name, description, categoryId, htmlPath, icon, order, visible
            );

            return ResponseEntity.status(HttpStatus.CREATED).body(CreateToolResponse.builder()
                .tool(convertToAdminToolDTO(tool))
                .build());
        } catch (IllegalArgumentException e) {
            if ("分类不存在".equals(e.getMessage())) {
                throw new IllegalArgumentException("分类不存在");
            }
            throw e;
        } catch (IOException e) {
            logger.error("保存HTML文件失败: {}", e.getMessage(), e);
            throw new RuntimeException("保存HTML文件失败: " + e.getMessage());
        } catch (Exception e) {
            logger.error("创建HTML工具失败: {}", e.getMessage(), e);
            throw new RuntimeException("创建HTML工具失败: " + e.getMessage());
        }
    }

    /**
     * 更新工具信息（管理后台）
     * PATCH /api/v1/admin/common-tools/{tool_id}
     */
    @PatchMapping("/common-tools/{tool_id}")
    public ResponseEntity<UpdateToolResponse> updateTool(
            @PathVariable("tool_id") String toolId,
            @RequestBody UpdateToolRequest request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            var tool = commonToolService.updateTool(
                toolId,
                request.getName(),
                request.getDescription(),
                request.getCategoryId(),
                request.getIcon(),
                request.getOrder(),
                request.getVisible(),
                request.getSystemPrompt(),
                request.getModelConfig()
            );

            return ResponseEntity.ok(UpdateToolResponse.builder()
                .tool(convertToAdminToolDTO(tool))
                .build());
        } catch (IllegalArgumentException e) {
            if ("工具不存在".equals(e.getMessage()) || "分类不存在".equals(e.getMessage())) {
                throw new IllegalArgumentException(e.getMessage());
            }
            throw e;
        } catch (Exception e) {
            logger.error("更新工具失败: {}", e.getMessage(), e);
            throw new RuntimeException("更新工具失败: " + e.getMessage());
        }
    }

    /**
     * 删除工具（管理后台）
     * DELETE /api/v1/admin/common-tools/{tool_id}
     */
    @DeleteMapping("/common-tools/{tool_id}")
    public ResponseEntity<Void> deleteTool(
            @PathVariable("tool_id") String toolId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            String htmlPath = commonToolService.deleteTool(toolId);

            // 如果是HTML工具，删除文件
            if (htmlPath != null) {
                try {
                    String uploadDir = System.getProperty("upload.dir", "static");
                    Path filePath = Paths.get(uploadDir, htmlPath);
                    if (Files.exists(filePath)) {
                        // 删除整个工具目录
                        Files.deleteIfExists(filePath);
                        Path toolDir = filePath.getParent();
                        if (Files.exists(toolDir)) {
                            Files.delete(toolDir);
                        }
                    }
                } catch (IOException e) {
                    logger.warn("删除HTML文件失败: {}", e.getMessage());
                }
            }

            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            if ("工具不存在".equals(e.getMessage())) {
                throw new IllegalArgumentException(e.getMessage());
            }
            throw e;
        } catch (Exception e) {
            logger.error("删除工具失败: {}", e.getMessage(), e);
            throw new RuntimeException("删除工具失败: " + e.getMessage());
        }
    }

    /**
     * 上移工具（管理后台）
     * POST /api/v1/admin/common-tools/{tool_id}/move-up
     */
    @PostMapping("/common-tools/{tool_id}/move-up")
    public ResponseEntity<MoveToolResponse> moveToolUp(
            @PathVariable("tool_id") String toolId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            var tool = commonToolService.moveToolUp(toolId);

            return ResponseEntity.ok(MoveToolResponse.builder()
                .message("工具已上移")
                .tool(convertToAdminToolDTO(tool))
                .build());
        } catch (IllegalArgumentException e) {
            if ("工具不存在".equals(e.getMessage())) {
                throw new IllegalArgumentException(e.getMessage());
            }
            throw e;
        } catch (Exception e) {
            logger.error("上移工具失败: {}", e.getMessage(), e);
            throw new RuntimeException("上移工具失败: " + e.getMessage());
        }
    }

    /**
     * 下移工具（管理后台）
     * POST /api/v1/admin/common-tools/{tool_id}/move-down
     */
    @PostMapping("/common-tools/{tool_id}/move-down")
    public ResponseEntity<MoveToolResponse> moveToolDown(
            @PathVariable("tool_id") String toolId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            var tool = commonToolService.moveToolDown(toolId);

            return ResponseEntity.ok(MoveToolResponse.builder()
                .message("工具已下移")
                .tool(convertToAdminToolDTO(tool))
                .build());
        } catch (IllegalArgumentException e) {
            if ("工具不存在".equals(e.getMessage())) {
                throw new IllegalArgumentException(e.getMessage());
            }
            throw e;
        } catch (Exception e) {
            logger.error("下移工具失败: {}", e.getMessage(), e);
            throw new RuntimeException("下移工具失败: " + e.getMessage());
        }
    }

    /**
     * 切换工具可见性（管理后台）
     * POST /api/v1/admin/common-tools/{tool_id}/toggle-visibility
     */
    @PostMapping("/common-tools/{tool_id}/toggle-visibility")
    public ResponseEntity<ToggleVisibilityResponse> toggleToolVisibility(
            @PathVariable("tool_id") String toolId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            var result = commonToolService.toggleToolVisibility(toolId);

            return ResponseEntity.ok(ToggleVisibilityResponse.builder()
                .message(result.getMessage())
                .tool(convertToAdminToolDTO(result.getTool()))
                .build());
        } catch (IllegalArgumentException e) {
            if ("工具不存在".equals(e.getMessage())) {
                throw new IllegalArgumentException(e.getMessage());
            }
            throw e;
        } catch (Exception e) {
            logger.error("切换工具可见性失败: {}", e.getMessage(), e);
            throw new RuntimeException("切换工具可见性失败: " + e.getMessage());
        }
    }

    // ==================== 工具分类管理接口 ====================

    /**
     * 获取工具分类列表（管理后台）
     * GET /api/v1/admin/tool-categories
     */
    @GetMapping("/tool-categories")
    public ResponseEntity<AdminToolCategoryListResponse> getAdminToolCategories(
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            var result = commonToolService.getAllCategoriesAdmin();

            return ResponseEntity.ok(AdminToolCategoryListResponse.builder()
                .categories(result.getCategories().stream()
                    .map(cat -> AdminToolCategoryDTO.builder()
                        .categoryId(cat.getCategoryId())
                        .name(cat.getName())
                        .order(cat.getOrder())
                        .toolCount(cat.getToolCount())
                        .build())
                    .toList())
                .total(result.getTotal())
                .build());
        } catch (Exception e) {
            logger.error("获取工具分类列表失败: {}", e.getMessage(), e);
            throw new RuntimeException("获取工具分类列表失败: " + e.getMessage());
        }
    }

    /**
     * 创建工具分类（管理后台）
     * POST /api/v1/admin/tool-categories
     */
    @PostMapping("/tool-categories")
    public ResponseEntity<CreateToolCategoryResponse> createToolCategory(
            @Valid @RequestBody CreateToolCategoryRequest request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            var category = commonToolService.createCategory(request.getName(), request.getOrder());

            return ResponseEntity.status(HttpStatus.CREATED).body(CreateToolCategoryResponse.builder()
                .category(AdminToolCategoryDTO.builder()
                    .categoryId(category.getId())
                    .name(category.getName())
                    .order(category.getOrder())
                    .toolCount(0)
                    .build())
                .build());
        } catch (IllegalArgumentException e) {
            if ("分类名称已存在".equals(e.getMessage())) {
                throw new IllegalArgumentException("分类名称已存在");
            }
            throw e;
        } catch (Exception e) {
            logger.error("创建工具分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("创建工具分类失败: " + e.getMessage());
        }
    }

    /**
     * 更新工具分类（管理后台）
     * PATCH /api/v1/admin/tool-categories/{category_id}
     */
    @PatchMapping("/tool-categories/{category_id}")
    public ResponseEntity<UpdateToolCategoryResponse> updateToolCategory(
            @PathVariable("category_id") String categoryId,
            @RequestBody UpdateToolCategoryRequest request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            var category = commonToolService.updateCategory(categoryId, request.getName(), request.getOrder());

            return ResponseEntity.ok(UpdateToolCategoryResponse.builder()
                .category(AdminToolCategoryDTO.builder()
                    .categoryId(category.getId())
                    .name(category.getName())
                    .order(category.getOrder())
                    .toolCount(0)
                    .build())
                .build());
        } catch (IllegalArgumentException e) {
            if ("分类不存在".equals(e.getMessage()) || "分类名称已被使用".equals(e.getMessage())) {
                throw new IllegalArgumentException(e.getMessage());
            }
            throw e;
        } catch (Exception e) {
            logger.error("更新工具分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("更新工具分类失败: " + e.getMessage());
        }
    }

    /**
     * 删除工具分类（管理后台）
     * DELETE /api/v1/admin/tool-categories/{category_id}
     */
    @DeleteMapping("/tool-categories/{category_id}")
    public ResponseEntity<Void> deleteToolCategory(
            @PathVariable("category_id") String categoryId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            commonToolService.deleteCategory(categoryId);

            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            if ("分类不存在".equals(e.getMessage())) {
                throw new IllegalArgumentException(e.getMessage());
            }
            if (e.getMessage() != null && e.getMessage().contains("还有") && e.getMessage().contains("工具")) {
                throw new IllegalArgumentException(e.getMessage());
            }
            throw e;
        } catch (Exception e) {
            logger.error("删除工具分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("删除工具分类失败: " + e.getMessage());
        }
    }

    /**
     * 上移分类（管理后台）
     * POST /api/v1/admin/tool-categories/{category_id}/move-up
     */
    @PostMapping("/tool-categories/{category_id}/move-up")
    public ResponseEntity<MoveCategoryResponse> moveCategoryUp(
            @PathVariable("category_id") String categoryId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            var category = commonToolService.moveCategoryUp(categoryId);

            return ResponseEntity.ok(MoveCategoryResponse.builder()
                .message("分类已上移")
                .category(AdminToolCategoryDTO.builder()
                    .categoryId(category.getId())
                    .name(category.getName())
                    .order(category.getOrder())
                    .toolCount(0)
                    .build())
                .build());
        } catch (IllegalArgumentException e) {
            if ("分类不存在".equals(e.getMessage())) {
                throw new IllegalArgumentException(e.getMessage());
            }
            throw e;
        } catch (Exception e) {
            logger.error("上移分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("上移分类失败: " + e.getMessage());
        }
    }

    /**
     * 下移分类（管理后台）
     * POST /api/v1/admin/tool-categories/{category_id}/move-down
     */
    @PostMapping("/tool-categories/{category_id}/move-down")
    public ResponseEntity<MoveCategoryResponse> moveCategoryDown(
            @PathVariable("category_id") String categoryId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            var category = commonToolService.moveCategoryDown(categoryId);

            return ResponseEntity.ok(MoveCategoryResponse.builder()
                .message("分类已下移")
                .category(AdminToolCategoryDTO.builder()
                    .categoryId(category.getId())
                    .name(category.getName())
                    .order(category.getOrder())
                    .toolCount(0)
                    .build())
                .build());
        } catch (IllegalArgumentException e) {
            if ("分类不存在".equals(e.getMessage())) {
                throw new IllegalArgumentException(e.getMessage());
            }
            throw e;
        } catch (Exception e) {
            logger.error("下移分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("下移分类失败: " + e.getMessage());
        }
    }

    // ==================== 辅助方法 ====================

    private AdminToolDTO convertToAdminToolDTO(com.platform.infrastructure.persistence.jpa.CommonToolEntity entity) {
        return AdminToolDTO.builder()
            .toolId(entity.getId())
            .name(entity.getName())
            .description(entity.getDescription())
            .categoryId(entity.getCategoryId())
            .categoryName(null) // TODO: 从categoryRepository获取
            .icon(entity.getIcon())
            .type(entity.getType().name().toLowerCase())
            .order(entity.getOrder())
            .visible(entity.getVisible())
            .htmlPath(entity.getHtmlPath())
            // systemPrompt和modelConfig从Tool配置文件(YAML)加载，不存储在数据库中
            // 管理后台如需查看这些字段，应从ToolService获取
            // .systemPrompt(entity.getSystemPrompt())
            // .modelConfig(entity.getModelConfig())
            .systemPrompt(null)
            .modelConfig(null)
            .build();
    }
}
