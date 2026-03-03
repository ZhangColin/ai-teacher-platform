package com.platform.interfaces.rest;

import com.platform.application.service.WorkService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 作品展示控制器
 *
 * 对应Python: backend/src/interfaces/routers/works/works.py
 */
@RestController
@RequestMapping("/api/v1")
public class WorkController {

    private final WorkService workService;

    public WorkController(WorkService workService) {
        this.workService = workService;
    }

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
     */
    @GetMapping("/works/{workId}")
    public Object getWorkDetail(@PathVariable String workId) {
        var work = workService.getWorkDetail(workId);
        if (work == null) {
            throw new RuntimeException("作品不存在");
        }
        return work;
    }
}
