package com.platform.interfaces.rest;

import com.platform.application.service.WorkService;
import com.platform.interfaces.rest.dto.UserInfo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 作品展示控制器
 *
 * 对应Python: backend/src/interfaces/routers/works/works.py
 *
 * 端点列表：
 * - GET    /api/v1/works/categories - 获取作品分类（已实现）
 * - GET    /api/v1/works/{work_id} - 获取作品详情（已实现）
 * - GET    /api/v1/admin/works - 获取教案列表
 * - POST   /api/v1/admin/works - 创建教案
 * - PATCH  /api/v1/admin/works/{work_id} - 更新教案
 * - DELETE /api/v1/admin/works/{work_id} - 删除教案
 * - POST   /api/v1/admin/works/{work_id}/move-up - 上移教案
 * - POST   /api/v1/admin/works/{work_id}/move-down - 下移教案
 * - POST   /api/v1/admin/works/{work_id}/toggle-visibility - 切换可见性
 * - GET    /api/v1/admin/work-categories - 获取教案分类列表
 * - POST   /api/v1/admin/work-categories - 创建教案分类
 * - PATCH  /api/v1/admin/work-categories/{category_id} - 更新教案分类
 * - DELETE /api/v1/admin/work-categories/{category_id} - 删除教案分类
 * - POST   /api/v1/admin/work-categories/{category_id}/move-up - 上移分类
 * - POST   /api/v1/admin/work-categories/{category_id}/move-down - 下移分类
 */
@RestController
@RequestMapping("/api/v1")
public class WorkController {

    private static final Logger logger = LoggerFactory.getLogger(WorkController.class);

    private final WorkService workService;

    public WorkController(WorkService workService) {
        this.workService = workService;
    }

    // ==================== 前端查询接口 ====================

    /**
     * 获取作品分类和作品列表
     *
     * 对应Python: @router.get("/works/categories")
     */
    @GetMapping("/works/categories")
    public List<WorkService.CategoryWithWorks> getCategories() {
        return workService.getCategoriesWithWorks();
    }

    /**
     * 获取作品详情
     *
     * 对应Python: @router.get("/works/{work_id}")
     */
    @GetMapping("/works/{work_id}")
    public Object getWorkDetail(@PathVariable("work_id") String workId) {
        var work = workService.getWorkDetail(workId);
        if (work == null) {
            throw new RuntimeException("作品不存在");
        }
        return work;
    }

    // ==================== 管理员接口 - 教案管理 ====================

    /**
     * 获取教案列表（管理后台）
     *
     * 对应Python: @router.get("/admin/works")
     */
    @GetMapping("/admin/works")
    public ResponseEntity<?> getAdminWorks(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize,
            @RequestParam(required = false) String categoryId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现获取教案列表
            return ResponseEntity.ok(Map.of("works", List.of(), "total", 0));
        } catch (Exception e) {
            logger.error("获取教案列表失败: {}", e.getMessage(), e);
            throw new RuntimeException("获取教案列表失败: " + e.getMessage());
        }
    }

    /**
     * 创建教案（管理后台）
     *
     * 对应Python: @router.post("/admin/works")
     */
    @PostMapping("/admin/works")
    public ResponseEntity<?> createWork(
            @RequestBody Map<String, Object> request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现创建教案
            return ResponseEntity.status(HttpStatus.CREATED).build();
        } catch (Exception e) {
            logger.error("创建教案失败: {}", e.getMessage(), e);
            throw new RuntimeException("创建教案失败: " + e.getMessage());
        }
    }

    /**
     * 更新教案（管理后台）
     *
     * 对应Python: @router.patch("/admin/works/{work_id}")
     */
    @PatchMapping("/admin/works/{work_id}")
    public ResponseEntity<?> updateWork(
            @PathVariable("work_id") String workId,
            @RequestBody Map<String, Object> request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现更新教案
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            logger.error("更新教案失败: {}", e.getMessage(), e);
            throw new RuntimeException("更新教案失败: " + e.getMessage());
        }
    }

    /**
     * 删除教案（管理后台）
     *
     * 对应Python: @router.delete("/admin/works/{work_id}")
     */
    @DeleteMapping("/admin/works/{work_id}")
    public ResponseEntity<?> deleteWork(
            @PathVariable("work_id") String workId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现删除教案
            return ResponseEntity.noContent().build();
        } catch (Exception e) {
            logger.error("删除教案失败: {}", e.getMessage(), e);
            throw new RuntimeException("删除教案失败: " + e.getMessage());
        }
    }

    /**
     * 上移教案（管理后台）
     *
     * 对应Python: @router.post("/admin/works/{work_id}/move-up")
     */
    @PostMapping("/admin/works/{work_id}/move-up")
    public ResponseEntity<?> moveWorkUp(
            @PathVariable("work_id") String workId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现上移教案
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            logger.error("上移教案失败: {}", e.getMessage(), e);
            throw new RuntimeException("上移教案失败: " + e.getMessage());
        }
    }

    /**
     * 下移教案（管理后台）
     *
     * 对应Python: @router.post("/admin/works/{work_id}/move-down")
     */
    @PostMapping("/admin/works/{work_id}/move-down")
    public ResponseEntity<?> moveWorkDown(
            @PathVariable("work_id") String workId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现下移教案
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            logger.error("下移教案失败: {}", e.getMessage(), e);
            throw new RuntimeException("下移教案失败: " + e.getMessage());
        }
    }

    /**
     * 切换教案可见性（管理后台）
     *
     * 对应Python: @router.post("/admin/works/{work_id}/toggle-visibility")
     */
    @PostMapping("/admin/works/{work_id}/toggle-visibility")
    public ResponseEntity<?> toggleWorkVisibility(
            @PathVariable("work_id") String workId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现切换可见性
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            logger.error("切换教案可见性失败: {}", e.getMessage(), e);
            throw new RuntimeException("切换教案可见性失败: " + e.getMessage());
        }
    }

    // ==================== 管理员接口 - 教案分类管理 ====================

    /**
     * 获取教案分类列表（管理后台）
     *
     * 对应Python: @router.get("/admin/work-categories")
     */
    @GetMapping("/admin/work-categories")
    public ResponseEntity<?> getAdminWorkCategories(
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现获取教案分类列表
            return ResponseEntity.ok(Map.of("categories", List.of()));
        } catch (Exception e) {
            logger.error("获取教案分类列表失败: {}", e.getMessage(), e);
            throw new RuntimeException("获取教案分类列表失败: " + e.getMessage());
        }
    }

    /**
     * 创建教案分类（管理后台）
     *
     * 对应Python: @router.post("/admin/work-categories")
     */
    @PostMapping("/admin/work-categories")
    public ResponseEntity<?> createWorkCategory(
            @RequestBody Map<String, Object> request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现创建教案分类
            return ResponseEntity.status(HttpStatus.CREATED).build();
        } catch (Exception e) {
            logger.error("创建教案分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("创建教案分类失败: " + e.getMessage());
        }
    }

    /**
     * 更新教案分类（管理后台）
     *
     * 对应Python: @router.patch("/admin/work-categories/{category_id}")
     */
    @PatchMapping("/admin/work-categories/{category_id}")
    public ResponseEntity<?> updateWorkCategory(
            @PathVariable("category_id") String categoryId,
            @RequestBody Map<String, Object> request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现更新教案分类
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            logger.error("更新教案分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("更新教案分类失败: " + e.getMessage());
        }
    }

    /**
     * 删除教案分类（管理后台）
     *
     * 对应Python: @router.delete("/admin/work-categories/{category_id}")
     */
    @DeleteMapping("/admin/work-categories/{category_id}")
    public ResponseEntity<?> deleteWorkCategory(
            @PathVariable("category_id") String categoryId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现删除教案分类
            return ResponseEntity.noContent().build();
        } catch (Exception e) {
            logger.error("删除教案分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("删除教案分类失败: " + e.getMessage());
        }
    }

    /**
     * 上移教案分类（管理后台）
     *
     * 对应Python: @router.post("/admin/work-categories/{category_id}/move-up")
     */
    @PostMapping("/admin/work-categories/{category_id}/move-up")
    public ResponseEntity<?> moveWorkCategoryUp(
            @PathVariable("category_id") String categoryId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现上移教案分类
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            logger.error("上移教案分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("上移教案分类失败: " + e.getMessage());
        }
    }

    /**
     * 下移教案分类（管理后台）
     *
     * 对应Python: @router.post("/admin/work-categories/{category_id}/move-down")
     */
    @PostMapping("/admin/work-categories/{category_id}/move-down")
    public ResponseEntity<?> moveWorkCategoryDown(
            @PathVariable("category_id") String categoryId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现下移教案分类
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            logger.error("下移教案分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("下移教案分类失败: " + e.getMessage());
        }
    }

    /**
     * 管理员权限验证
     */
    private void requireAdmin(UserInfo currentUser) {
        if (currentUser == null || !Boolean.TRUE.equals(currentUser.getIsAdmin())) {
            throw new IllegalArgumentException("需要管理员权限");
        }
    }
}
