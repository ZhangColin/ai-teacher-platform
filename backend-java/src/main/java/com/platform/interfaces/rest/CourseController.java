package com.platform.interfaces.rest;

import com.platform.application.service.CourseService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 课程文档控制器
 *
 * 对应Python: backend/src/interfaces/routers/courses/courses.py
 */
@RestController
@RequestMapping("/api/v1")
public class CourseController {

    private final CourseService courseService;

    public CourseController(CourseService courseService) {
        this.courseService = courseService;
    }

    /**
     * 获取课程文档分类树
     *
     * 对应Python: @router.get("/documents/categories")
     */
    @GetMapping("/documents/categories")
    public List<CourseService.CategoryNode> getCategoryTree() {
        return courseService.getCategoryTree();
    }
}
