package com.platform.interfaces.rest;

import com.platform.application.service.CommonToolService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 通用工具控制器
 *
 * 对应Python: backend/src/interfaces/routers/admin/tools.py
 */
@RestController
@RequestMapping("/api/v1")
public class CommonToolController {

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
    @GetMapping("/common-tools/{toolId}")
    public Object getToolDetail(@PathVariable String toolId) {
        var tool = commonToolService.getToolDetail(toolId);
        if (tool == null) {
            throw new RuntimeException("工具不存在");
        }
        return tool;
    }
}
