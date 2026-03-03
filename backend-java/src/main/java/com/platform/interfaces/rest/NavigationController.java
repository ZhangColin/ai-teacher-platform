package com.platform.interfaces.rest;

import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 导航配置控制器
 *
 * 对应Python: backend/src/interfaces/routers/tools/list.py
 */
@RestController
@RequestMapping("/api/v1")
public class NavigationController {

    /**
     * 获取导航配置
     *
     * 对应Python: @router.get("/navigation")
     */
    @GetMapping("/navigation")
    public Map<String, Object> getNavigation() {
        // TODO: 从configs/navigation.yaml加载配置
        return Map.of("modules", List.of());
    }

    /**
     * 获取所有工具
     *
     * 对应Python: @router.get("/tools")
     */
    @GetMapping("/tools")
    public Map<String, Object> getAllTools() {
        // TODO: 返回所有工具列表
        return Map.of("tools", List.of());
    }
}
