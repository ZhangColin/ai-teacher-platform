package com.platform.interfaces.rest;

import com.platform.application.service.CommonToolService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 通用工具控制器
 *
 * 对应Python: backend/src/interfaces/routers/common/common.py
 */
@RestController
@RequestMapping("/api/v1")
public class CommonToolController {

    private static final Logger logger = LoggerFactory.getLogger(CommonToolController.class);

    private final CommonToolService commonToolService;

    public CommonToolController(CommonToolService commonToolService) {
        this.commonToolService = commonToolService;
    }

    /**
     * 获取工具分类和工具列表
     *
     * 对应Python: @router.get("/common-tools/categories")
     */
    @GetMapping("/common-tools/categories")
    public List<CommonToolService.CategoryWithTools> getCategories() {
        return commonToolService.getCategoriesWithTools();
    }

    /**
     * 获取工具详情
     *
     * 对应Python: @router.get("/common-tools/{tool_id}")
     */
    @GetMapping("/common-tools/{tool_id}")
    public Object getToolDetail(@PathVariable("tool_id") String toolId) {
        var tool = commonToolService.getToolDetail(toolId);
        if (tool == null) {
            throw new RuntimeException("工具不存在");
        }
        return tool;
    }

    /**
     * Markdown转Word
     *
     * 对应Python: @router.post("/convert/markdown-to-word")
     */
    @PostMapping("/convert/markdown-to-word")
    public Map<String, String> convertMarkdownToWord(@RequestBody Map<String, String> request) {
        try {
            // TODO: 实现Markdown转Word功能
            logger.info("Markdown转Word请求 - 内容长度: {}", request.getOrDefault("markdown", "").length());
            return Map.of("task_id", "mock-task-id");
        } catch (Exception e) {
            logger.error("Markdown转Word失败: {}", e.getMessage(), e);
            throw new RuntimeException("Markdown转Word失败: " + e.getMessage());
        }
    }

    /**
     * 查询异步任务状态
     *
     * 对应Python: @router.get("/tasks/{task_id}")
     */
    @GetMapping("/tasks/{task_id}")
    public Map<String, Object> getTaskStatus(@PathVariable("task_id") String taskId) {
        try {
            // TODO: 实现查询任务状态
            logger.info("查询任务状态 - 任务ID: {}", taskId);
            return Map.of(
                "task_id", taskId,
                "status", "completed",
                "result", "mock-result"
            );
        } catch (Exception e) {
            logger.error("查询任务状态失败: {}", e.getMessage(), e);
            throw new RuntimeException("查询任务状态失败: " + e.getMessage());
        }
    }
}
