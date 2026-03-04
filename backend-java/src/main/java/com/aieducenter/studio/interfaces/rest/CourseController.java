package com.platform.interfaces.rest;

import com.platform.application.service.CourseService;
import com.platform.interfaces.rest.dto.UserInfo;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 课程文档控制器
 *
 * 对应Python: backend/src/interfaces/routers/courses/courses.py
 *
 * 端点列表：
 * - GET    /api/v1/documents/categories - 获取分类树（已实现）
 * - GET    /api/v1/documents/category/{category_id}/documents - 获取分类下的文档
 * - GET    /api/v1/documents/{doc_id} - 获取文档详情
 * - GET    /api/v1/admin/course-categories - 获取课程分类列表
 * - POST   /api/v1/admin/course-categories - 创建课程分类
 * - PATCH  /api/v1/admin/course-categories/{category_id} - 更新课程分类
 * - DELETE /api/v1/admin/course-categories/{category_id} - 删除课程分类
 * - POST   /api/v1/admin/course-categories/{category_id}/move-up - 上移分类
 * - POST   /api/v1/admin/course-categories/{category_id}/move-down - 下移分类
 * - GET    /api/v1/admin/course-documents - 获取课程文档列表
 * - POST   /api/v1/admin/course-documents - 创建课程文档
 * - PATCH  /api/v1/admin/course-documents/{doc_id} - 更新课程文档
 * - DELETE /api/v1/admin/course-documents/{doc_id} - 删除课程文档
 * - POST   /api/v1/admin/course-documents/{doc_id}/move-up - 上移文档
 * - POST   /api/v1/admin/course-documents/{doc_id}/move-down - 下移文档
 */
@RestController
@RequestMapping("/api/v1")
public class CourseController {

    private static final Logger logger = LoggerFactory.getLogger(CourseController.class);

    private final CourseService courseService;

    public CourseController(CourseService courseService) {
        this.courseService = courseService;
    }

    // ==================== 前端查询接口 ====================

    /**
     * 获取课程文档分类树
     *
     * 对应Python: @router.get("/documents/categories")
     */
    @GetMapping("/documents/categories")
    public List<CourseService.CategoryNode> getCategoryTree() {
        return courseService.getCategoryTree();
    }

    /**
     * 获取分类下的文档
     *
     * 对应Python: @router.get("/documents/category/{category_id}/documents")
     */
    @GetMapping("/documents/category/{category_id}/documents")
    public ResponseEntity<?> getDocumentsByCategory(
            @PathVariable("category_id") String categoryId
    ) {
        try {
            // TODO: 实现获取分类下的文档
            return ResponseEntity.ok(Map.of("documents", List.of()));
        } catch (Exception e) {
            logger.error("获取分类下的文档失败: {}", e.getMessage(), e);
            throw new RuntimeException("获取分类下的文档失败: " + e.getMessage());
        }
    }

    /**
     * 获取文档详情
     *
     * 对应Python: @router.get("/documents/{doc_id}")
     */
    @GetMapping("/documents/{doc_id}")
    public ResponseEntity<?> getDocumentDetail(
            @PathVariable("doc_id") String docId
    ) {
        try {
            // TODO: 实现获取文档详情
            return ResponseEntity.ok(Map.of());
        } catch (Exception e) {
            logger.error("获取文档详情失败: {}", e.getMessage(), e);
            throw new RuntimeException("获取文档详情失败: " + e.getMessage());
        }
    }

    // ==================== 管理员接口 - 分类管理 ====================

    /**
     * 获取课程分类列表（管理后台）
     *
     * 对应Python: @router.get("/admin/course-categories")
     */
    @GetMapping("/admin/course-categories")
    public ResponseEntity<?> getAdminCategories(
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现获取管理员分类列表
            return ResponseEntity.ok(Map.of("categories", List.of()));
        } catch (Exception e) {
            logger.error("获取课程分类列表失败: {}", e.getMessage(), e);
            throw new RuntimeException("获取课程分类列表失败: " + e.getMessage());
        }
    }

    /**
     * 创建课程分类（管理后台）
     *
     * 对应Python: @router.post("/admin/course-categories")
     */
    @PostMapping("/admin/course-categories")
    public ResponseEntity<?> createCategory(
            @RequestBody Map<String, Object> request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现创建分类
            return ResponseEntity.status(HttpStatus.CREATED).build();
        } catch (Exception e) {
            logger.error("创建课程分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("创建课程分类失败: " + e.getMessage());
        }
    }

    /**
     * 更新课程分类（管理后台）
     *
     * 对应Python: @router.patch("/admin/course-categories/{category_id}")
     */
    @PatchMapping("/admin/course-categories/{category_id}")
    public ResponseEntity<?> updateCategory(
            @PathVariable("category_id") String categoryId,
            @RequestBody Map<String, Object> request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现更新分类
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            logger.error("更新课程分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("更新课程分类失败: " + e.getMessage());
        }
    }

    /**
     * 删除课程分类（管理后台）
     *
     * 对应Python: @router.delete("/admin/course-categories/{category_id}")
     */
    @DeleteMapping("/admin/course-categories/{category_id}")
    public ResponseEntity<?> deleteCategory(
            @PathVariable("category_id") String categoryId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现删除分类
            return ResponseEntity.noContent().build();
        } catch (Exception e) {
            logger.error("删除课程分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("删除课程分类失败: " + e.getMessage());
        }
    }

    /**
     * 上移课程分类（管理后台）
     *
     * 对应Python: @router.post("/admin/course-categories/{category_id}/move-up")
     */
    @PostMapping("/admin/course-categories/{category_id}/move-up")
    public ResponseEntity<?> moveCategoryUp(
            @PathVariable("category_id") String categoryId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现上移分类
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            logger.error("上移课程分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("上移课程分类失败: " + e.getMessage());
        }
    }

    /**
     * 下移课程分类（管理后台）
     *
     * 对应Python: @router.post("/admin/course-categories/{category_id}/move-down")
     */
    @PostMapping("/admin/course-categories/{category_id}/move-down")
    public ResponseEntity<?> moveCategoryDown(
            @PathVariable("category_id") String categoryId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现下移分类
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            logger.error("下移课程分类失败: {}", e.getMessage(), e);
            throw new RuntimeException("下移课程分类失败: " + e.getMessage());
        }
    }

    // ==================== 管理员接口 - 文档管理 ====================

    /**
     * 获取课程文档列表（管理后台）
     *
     * 对应Python: @router.get("/admin/course-documents")
     */
    @GetMapping("/admin/course-documents")
    public ResponseEntity<?> getAdminDocuments(
            @RequestParam(required = false) String categoryId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现获取文档列表
            return ResponseEntity.ok(Map.of("documents", List.of()));
        } catch (Exception e) {
            logger.error("获取课程文档列表失败: {}", e.getMessage(), e);
            throw new RuntimeException("获取课程文档列表失败: " + e.getMessage());
        }
    }

    /**
     * 创建课程文档（管理后台）
     *
     * 对应Python: @router.post("/admin/course-documents")
     */
    @PostMapping("/admin/course-documents")
    public ResponseEntity<?> createDocument(
            @RequestBody Map<String, Object> request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现创建文档
            return ResponseEntity.status(HttpStatus.CREATED).build();
        } catch (Exception e) {
            logger.error("创建课程文档失败: {}", e.getMessage(), e);
            throw new RuntimeException("创建课程文档失败: " + e.getMessage());
        }
    }

    /**
     * 更新课程文档（管理后台）
     *
     * 对应Python: @router.patch("/admin/course-documents/{doc_id}")
     */
    @PatchMapping("/admin/course-documents/{doc_id}")
    public ResponseEntity<?> updateDocument(
            @PathVariable("doc_id") String docId,
            @RequestBody Map<String, Object> request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现更新文档
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            logger.error("更新课程文档失败: {}", e.getMessage(), e);
            throw new RuntimeException("更新课程文档失败: " + e.getMessage());
        }
    }

    /**
     * 删除课程文档（管理后台）
     *
     * 对应Python: @router.delete("/admin/course-documents/{doc_id}")
     */
    @DeleteMapping("/admin/course-documents/{doc_id}")
    public ResponseEntity<?> deleteDocument(
            @PathVariable("doc_id") String docId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现删除文档
            return ResponseEntity.noContent().build();
        } catch (Exception e) {
            logger.error("删除课程文档失败: {}", e.getMessage(), e);
            throw new RuntimeException("删除课程文档失败: " + e.getMessage());
        }
    }

    /**
     * 上移课程文档（管理后台）
     *
     * 对应Python: @router.post("/admin/course-documents/{doc_id}/move-up")
     */
    @PostMapping("/admin/course-documents/{doc_id}/move-up")
    public ResponseEntity<?> moveDocumentUp(
            @PathVariable("doc_id") String docId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现上移文档
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            logger.error("上移课程文档失败: {}", e.getMessage(), e);
            throw new RuntimeException("上移课程文档失败: " + e.getMessage());
        }
    }

    /**
     * 下移课程文档（管理后台）
     *
     * 对应Python: @router.post("/admin/course-documents/{doc_id}/move-down")
     */
    @PostMapping("/admin/course-documents/{doc_id}/move-down")
    public ResponseEntity<?> moveDocumentDown(
            @PathVariable("doc_id") String docId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);
            // TODO: 实现下移文档
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            logger.error("下移课程文档失败: {}", e.getMessage(), e);
            throw new RuntimeException("下移课程文档失败: " + e.getMessage());
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
