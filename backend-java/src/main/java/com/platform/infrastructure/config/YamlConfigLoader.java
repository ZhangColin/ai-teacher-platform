package com.platform.infrastructure.config;

import com.platform.interfaces.dto.CategoryDTO;
import com.platform.interfaces.dto.NavigationModuleDTO;
import com.platform.interfaces.dto.ToolDTO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Component;
import org.yaml.snakeyaml.Yaml;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * YAML配置加载器
 *
 * 对应Python: backend/src/services/tool_service.py
 * 负责加载工具配置、导航配置、分类配置等
 */
@Slf4j
@Component
public class YamlConfigLoader {

    private final Yaml yaml = new Yaml();

    /**
     * 配置文件根目录（相对于项目根目录）
     * 对应Python: config_dir: str = "configs/tools"
     */
    @Value("${config.base-path:configs}")
    private String configBasePath;

    /**
     * 工具配置目录
     */
    @Value("${config.tools-path:configs/tools}")
    private String configToolsPath;

    /**
     * 缓存时间戳
     */
    private Instant cacheTimestamp;

    /**
     * 缓存的所有工具
     */
    private List<ToolDTO> cachedTools;

    /**
     * 加载导航配置
     * 对应Python: (在routers/tools.py中直接加载navigation.yaml)
     *
     * @return 导航模块列表
     */
    public List<NavigationModuleDTO> loadNavigationConfig() {
        Path navigationPath = Paths.get(configBasePath, "navigation.yaml");

        if (!Files.exists(navigationPath)) {
            log.warn("导航配置文件不存在: {}", navigationPath);
            return List.of();
        }

        try (FileInputStream fis = new FileInputStream(navigationPath.toFile())) {
            Map<String, Object> data = yaml.load(fis);
            List<Map<String, Object>> modulesList = (List<Map<String, Object>>) data.get("modules");

            if (modulesList == null) {
                return List.of();
            }

            return modulesList.stream()
                .map(this::mapToNavigationModule)
                .filter(NavigationModuleDTO::validate)
                .sorted(Comparator.comparing(NavigationModuleDTO::getOrder))
                .collect(Collectors.toList());

        } catch (IOException e) {
            log.error("加载导航配置失败: {}", navigationPath, e);
            return List.of();
        }
    }

    /**
     * 加载所有工具（带缓存机制）
     * 对应Python: load_all_tools() -> List[Tool]
     *
     * @return 工具列表（只包含成功加载且 visible=true 的工具）
     */
    public List<ToolDTO> loadAllTools() {
        // 检查缓存是否有效（5分钟过期）
        Instant now = Instant.now();
        if (cachedTools != null && cacheTimestamp != null &&
            Duration.between(cacheTimestamp, now).toSeconds() < 300) {
            return cachedTools;
        }

        Path toolsDir = Paths.get(configToolsPath);

        if (!Files.exists(toolsDir)) {
            log.warn("工具配置目录不存在: {}", toolsDir);
            cachedTools = List.of();
            cacheTimestamp = now;
            return cachedTools;
        }

        List<ToolDTO> tools = new ArrayList<>();

        try {
            // 检查是否是新的目录结构（有子目录）
            boolean hasSubdirs;
            try (Stream<Path> paths = Files.list(toolsDir)) {
                hasSubdirs = paths.anyMatch(Files::isDirectory);
            }

            if (hasSubdirs) {
                // 新的目录结构：扫描每个工具集子目录
                try (Stream<Path> toolsetDirs = Files.list(toolsDir)) {
                    toolsetDirs
                        .filter(Files::isDirectory)
                        .forEach(toolsetDir -> {
                            String toolsetId = toolsetDir.getFileName().toString();
                            tools.addAll(loadToolsFromDirectory(toolsetDir, toolsetId));
                        });
                }
            } else {
                // 旧的扁平结构（向后兼容）
                log.warn("使用旧的扁平配置目录结构，建议迁移到新的目录结构");
                try (Stream<Path> configFiles = Files.list(toolsDir)) {
                    configFiles
                        .filter(path -> !path.getFileName().toString().equals("categories.yaml"))
                        .filter(path -> path.toString().endsWith(".yaml") || path.toString().endsWith(".yml"))
                        .forEach(path -> {
                            ToolDTO tool = loadTool(path, "ai_tools");
                            if (tool != null && tool.getVisible()) {
                                tools.add(tool);
                            }
                        });
                }
            }
        } catch (IOException e) {
            log.error("扫描工具配置目录失败: {}", toolsDir, e);
        }

        // 更新缓存
        cachedTools = tools;
        cacheTimestamp = now;

        return tools;
    }

    /**
     * 从指定目录加载工具
     * 对应Python: load_tools_from_directory()
     *
     * @param directory 工具配置目录
     * @param toolsetId 工具集ID
     * @return 工具列表
     */
    public List<ToolDTO> loadToolsFromDirectory(Path directory, String toolsetId) {
        List<ToolDTO> tools = new ArrayList<>();

        if (!Files.exists(directory)) {
            return tools;
        }

        try (Stream<Path> configFiles = Files.list(directory)) {
            configFiles
                .filter(path -> {
                    String filename = path.getFileName().toString();
                    // 跳过特殊文件
                    return !filename.equals("categories.yaml") &&
                           !filename.equals("navigation.yaml") &&
                           (filename.endsWith(".yaml") || filename.endsWith(".yml"));
                })
                .forEach(path -> {
                    ToolDTO tool = loadTool(path, toolsetId);
                    if (tool != null && tool.getVisible()) {
                        tools.add(tool);
                    }
                });
        } catch (IOException e) {
            log.error("扫描工具目录失败: {}", directory, e);
        }

        return tools;
    }

    /**
     * 根据toolset_id加载工具
     * 对应Python: load_tools_by_toolset(toolset_id: str) -> List[Tool]
     *
     * @param toolsetId 工具集ID
     * @return 工具列表
     */
    public List<ToolDTO> loadToolsByToolset(String toolsetId) {
        // 尝试从工具集目录加载
        Path toolsetDir = Paths.get(configToolsPath, toolsetId);

        if (Files.exists(toolsetDir) && Files.isDirectory(toolsetDir)) {
            return loadToolsFromDirectory(toolsetDir, toolsetId);
        }

        // 如果目录不存在，从缓存中过滤
        return loadAllTools().stream()
            .filter(tool -> toolsetId.equals(tool.getToolsetId()))
            .collect(Collectors.toList());
    }

    /**
     * 从配置文件加载单个工具
     * 对应Python: load_tool()
     *
     * @param configPath 配置文件路径
     * @param toolsetId  工具集ID（用于从文件加载系统提示词）
     * @return Tool实例，如果加载失败返回null
     */
    public ToolDTO loadTool(Path configPath, String toolsetId) {
        try (FileInputStream fis = new FileInputStream(configPath.toFile())) {
            Map<String, Object> configData = yaml.load(fis);

            // 读取 system_prompt（可能为null）
            String systemPrompt = (String) configData.get("system_prompt");
            String systemPromptFile = (String) configData.get("system_prompt_file");

            // 如果指定了 system_prompt_file，从文件加载
            if (systemPromptFile != null && !systemPromptFile.isBlank()) {
                String loadedPrompt = loadSystemPromptFromFile(toolsetId, systemPromptFile);
                if (loadedPrompt != null) {
                    systemPrompt = loadedPrompt;
                } else {
                    log.warn("无法从文件加载系统提示词: {}, 工具: {}",
                        systemPromptFile, configData.get("tool_id"));
                }
            }

            // 确定 toolset_id
            String toolToolsetId = (String) configData.get("toolset_id");
            if (toolToolsetId == null || toolToolsetId.isBlank()) {
                toolToolsetId = toolsetId;
            }
            if (toolToolsetId == null || toolToolsetId.isBlank()) {
                toolToolsetId = "ai_tools";  // 默认值（向后兼容）
            }

            // 构建 ToolDTO
            ToolDTO tool = ToolDTO.builder()
                .toolId((String) configData.get("tool_id"))
                .name((String) configData.get("name"))
                .description((String) configData.get("description"))
                .systemPrompt(systemPrompt)
                .category((String) configData.get("category"))
                .icon((String) configData.get("icon"))
                .visible(configData.getOrDefault("visible", true) != null ?
                    Boolean.valueOf(configData.get("visible").toString()) : true)
                .type((String) configData.getOrDefault("type", "normal"))
                .welcomeMessage((String) configData.getOrDefault("welcome_message", ""))
                .order(((Number) configData.getOrDefault("order", 999)).intValue())
                .toolsetId(toolToolsetId)
                .systemPromptFile(systemPromptFile)
                .model((String) configData.get("model"))
                .contentType((String) configData.getOrDefault("content_type", "text"))
                .mediaType((String) configData.get("media_type"))
                .build();

            // 验证配置
            if (!tool.validate()) {
                log.warn("工具配置验证失败: {}", configPath);
                return null;
            }

            return tool;

        } catch (Exception e) {
            log.warn("加载工具配置失败: {}, 错误: {}", configPath, e.getMessage());
            return null;
        }
    }

    /**
     * 从文件加载系统提示词
     * 对应Python: config_loader.load_system_prompt_from_file()
     *
     * @param toolsetId    工具集ID
     * @param promptFile   提示词文件路径
     * @return 系统提示词内容
     */
    public String loadSystemPromptFromFile(String toolsetId, String promptFile) {
        Path promptPath = Paths.get(configToolsPath, toolsetId, "prompts", promptFile);

        if (!Files.exists(promptPath)) {
            log.warn("系统提示词文件不存在: {}", promptPath);
            return null;
        }

        try {
            return Files.readString(promptPath);
        } catch (IOException e) {
            log.error("读取系统提示词文件失败: {}", promptPath, e);
            return null;
        }
    }

    /**
     * 加载分类配置文件
     * 对应Python: load_category_config()
     *
     * @param toolsetId 工具集ID（如果指定，从对应工具集目录加载）
     * @return 分类配置字典，key为分类名称，value包含order和icon
     */
    public Map<String, CategoryConfig> loadCategoryConfig(String toolsetId) {
        Path categoryConfigPath;

        if (toolsetId != null && !toolsetId.isBlank()) {
            categoryConfigPath = Paths.get(configToolsPath, toolsetId, "categories.yaml");
        } else {
            categoryConfigPath = Paths.get(configToolsPath, "categories.yaml");
        }

        Map<String, CategoryConfig> categoryConfig = new HashMap<>();

        if (!Files.exists(categoryConfigPath)) {
            return categoryConfig;
        }

        try (FileInputStream fis = new FileInputStream(categoryConfigPath.toFile())) {
            Map<String, Object> data = yaml.load(fis);
            List<Map<String, Object>> categoriesList = (List<Map<String, Object>>) data.get("categories");

            if (categoriesList != null) {
                for (Map<String, Object> cat : categoriesList) {
                    String name = (String) cat.get("name");
                    if (name != null && !name.isBlank()) {
                        CategoryConfig config = new CategoryConfig();
                        config.order = ((Number) cat.getOrDefault("order", 999)).intValue();
                        config.icon = (String) cat.get("icon");
                        categoryConfig.put(name, config);
                    }
                }
            }
        } catch (Exception e) {
            log.warn("加载分类配置失败: {}, 错误: {}", categoryConfigPath, e.getMessage());
        }

        return categoryConfig;
    }

    /**
     * 按category聚合工具，生成分类结构
     * 对应Python: group_by_category()
     *
     * @param tools     工具列表
     * @param toolsetId 工具集ID（用于加载对应的分类配置）
     * @return 分类列表
     */
    public List<CategoryDTO> groupByCategory(List<ToolDTO> tools, String toolsetId) {
        // 加载分类配置
        Map<String, CategoryConfig> categoryConfig = loadCategoryConfig(toolsetId);

        // 使用字典按 category 分组
        Map<String, CategoryDTO> categoryDict = new HashMap<>();

        for (ToolDTO tool : tools) {
            String categoryName = tool.getCategory();
            if (categoryName == null || categoryName.isBlank()) {
                continue;
            }

            CategoryDTO category = categoryDict.computeIfAbsent(categoryName, k -> {
                CategoryConfig config = categoryConfig.getOrDefault(k, new CategoryConfig());
                return CategoryDTO.builder()
                    .name(k)
                    .icon(config.icon != null ? config.icon : tool.getIcon())
                    .order(config.order != null ? config.order : 999)
                    .tools(new ArrayList<>())
                    .build();
            });

            category.getTools().add(tool);
        }

        // 对每个分类内的工具按 order 排序
        categoryDict.values().forEach(category ->
            category.getTools().sort(Comparator.comparing(ToolDTO::getOrder))
        );

        // 转换为列表并按 order 排序
        return categoryDict.values().stream()
            .sorted(Comparator.comparing(CategoryDTO::getOrder))
            .collect(Collectors.toList());
    }

    /**
     * 映射为NavigationModuleDTO
     */
    private NavigationModuleDTO mapToNavigationModule(Map<String, Object> data) {
        return NavigationModuleDTO.builder()
            .name((String) data.get("name"))
            .type((String) data.get("type"))
            .configSource((String) data.get("config_source"))
            .pagePath((String) data.get("page_path"))
            .icon((String) data.get("icon"))
            .order(((Number) data.getOrDefault("order", 999)).intValue())
            .build();
    }

    /**
     * 分类配置内部类
     */
    private static class CategoryConfig {
        Integer order;
        String icon;
    }
}
