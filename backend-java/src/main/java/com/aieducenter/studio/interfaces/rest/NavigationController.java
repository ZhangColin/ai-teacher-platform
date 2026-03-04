package com.aieducenter.studio.interfaces.rest;

import com.aieducenter.studio.infrastructure.config.YamlConfigLoader;
import com.aieducenter.studio.interfaces.dto.CategoryDTO;
import com.aieducenter.studio.interfaces.dto.NavigationModuleDTO;
import com.aieducenter.studio.interfaces.dto.ToolDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 导航配置控制器
 *
 * 对应Python: backend/src/routers/tools.py
 */
@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
public class NavigationController {

    private final YamlConfigLoader configLoader;

    /**
     * 获取导航配置
     *
     * 对应Python: @router.get("/navigation")
     */
    @GetMapping("/navigation")
    public ResponseEntity<Map<String, List<NavigationModuleDTO>>> getNavigation() {
        List<NavigationModuleDTO> modules = configLoader.loadNavigationConfig();
        return ResponseEntity.ok(Map.of("modules", modules));
    }

    /**
     * 获取所有工具
     *
     * 对应Python: @router.get("/tools")
     */
    @GetMapping("/tools")
    public ResponseEntity<Map<String, List<ToolDTO>>> getAllTools() {
        List<ToolDTO> tools = configLoader.loadAllTools();
        return ResponseEntity.ok(Map.of("tools", tools));
    }

    /**
     * 按工具集获取工具
     *
     * 对应Python: @router.get("/toolsets/{toolset_id}/tools")
     */
    @GetMapping("/toolsets/{toolset_id}/tools")
    public ResponseEntity<Map<String, Object>> getToolsByToolset(
            @PathVariable("toolset_id") String toolsetId
    ) {
        List<ToolDTO> tools = configLoader.loadToolsByToolset(toolsetId);

        // 按分类聚合
        List<CategoryDTO> categories = configLoader.groupByCategory(tools, toolsetId);

        Map<String, Object> response = new HashMap<>();
        response.put("tools", tools);
        response.put("categories", categories);

        return ResponseEntity.ok(response);
    }
}
