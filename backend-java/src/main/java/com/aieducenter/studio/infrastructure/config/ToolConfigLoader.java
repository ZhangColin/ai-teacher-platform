package com.platform.infrastructure.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;

/**
 * 工具配置加载器
 *
 * 对应Python: backend/src/services/tool_service.py
 * 负责从YAML文件加载工具配置
 *
 * @author AI Teacher Platform
 */
@Component
public class ToolConfigLoader {

    private static final Logger logger = LoggerFactory.getLogger(ToolConfigLoader.class);

    @Value("${tools.config-dir:configs/tools}")
    private String configDir;

    @Value("${tools.cache-duration:300}")
    private long cacheDurationSeconds;

    /**
     * 缓存：toolId -> Tool
     */
    private Map<String, com.platform.domain.tool.Tool> toolsCache = new HashMap<>();

    /**
     * 缓存时间戳
     */
    private long cacheTimestamp = 0;

    /**
     * 系统提示词缓存：toolsetId/promptFile -> prompt
     */
    private Map<String, String> promptCache = new HashMap<>();

    /**
     * 加载所有工具（带缓存）
     *
     * 对应Python: def load_all_tools() -> List[Tool]
     *
     * @return 工具列表
     */
    public List<com.platform.domain.tool.Tool> loadAllTools() {
        // 检查缓存是否有效
        long currentTime = System.currentTimeMillis() / 1000;
        if (!toolsCache.isEmpty() && (currentTime - cacheTimestamp) < cacheDurationSeconds) {
            logger.debug("返回缓存的工具列表，工具数量: {}", toolsCache.size());
            return List.copyOf(toolsCache.values());
        }

        toolsCache.clear();
        Path configPath = Paths.get(configDir);

        if (!Files.exists(configPath)) {
            logger.warn("工具配置目录不存在: {}", configDir);
            return List.of();
        }

        try {
            // 检查是否有子目录（新的目录结构）
            boolean hasSubdirs = Files.list(configPath)
                .anyMatch(Files::isDirectory);

            if (hasSubdirs) {
                // 新的目录结构：扫描每个工具集子目录
                try (Stream<Path> toolsetDirs = Files.list(configPath)) {
                    toolsetDirs
                        .filter(Files::isDirectory)
                        .forEach(toolsetDir -> {
                            String toolsetId = toolsetDir.getFileName().toString();
                            loadToolsFromDirectory(toolsetDir, toolsetId);
                        });
                }
            } else {
                // 旧的扁平结构（向后兼容）
                loadLegacyStructure(configPath);
            }

            cacheTimestamp = currentTime;
            logger.info("加载工具完成，总数量: {}", toolsCache.size());

        } catch (IOException e) {
            logger.error("加载工具配置失败: {}", e.getMessage(), e);
        }

        return List.copyOf(toolsCache.values());
    }

    /**
     * 从指定目录加载工具
     *
     * 对应Python: def load_tools_from_directory(...)
     *
     * @param directory 目录路径
     * @param toolsetId 工具集ID
     */
    private void loadToolsFromDirectory(Path directory, String toolsetId) {
        try (Stream<Path> yamlFiles = Files.list(directory)) {
            yamlFiles
                .filter(this::isYamlFile)
                .filter(file -> !isSpecialFile(file.getFileName().toString()))
                .forEach(file -> loadTool(file, toolsetId));
        } catch (IOException e) {
            logger.error("加载目录失败: {}, 错误: {}", directory, e.getMessage());
        }
    }

    /**
     * 加载旧的扁平结构
     */
    private void loadLegacyStructure(Path configPath) {
        try (Stream<Path> yamlFiles = Files.list(configPath)) {
            yamlFiles
                .filter(this::isYamlFile)
                .filter(file -> !isSpecialFile(file.getFileName().toString()))
                .forEach(file -> loadTool(file, "ai_tools")); // 默认工具集ID
        } catch (IOException e) {
            logger.error("加载旧结构配置失败: {}", e.getMessage());
        }
    }

    /**
     * 加载单个工具
     *
     * 对应Python: def load_tool(...)
     *
     * @param configPath 配置文件路径
     * @param toolsetId 工具集ID
     */
    private void loadTool(Path configPath, String toolsetId) {
        try {
            // TODO: 解析YAML文件（需要添加SnakeYAML依赖或使用Spring Boot的配置绑定）
            logger.warn("YAML解析功能待实现，跳过文件: {}", configPath);

            // 临时实现：使用占位符数据
            com.platform.domain.tool.Tool tool = com.platform.domain.tool.Tool.builder()
                .toolId(configPath.getFileName().toString().replace(".yaml", ""))
                .name("占位符工具")
                .description("待实现")
                .systemPrompt("你是一个有用的AI助手。")
                .category("默认")
                .visible(true)
                .type("normal")
                .welcomeMessage("欢迎使用！")
                .order(999)
                .toolsetId(toolsetId)
                .build();

            if (tool.validate()) {
                toolsCache.put(tool.getToolId(), tool);
            }

        } catch (Exception e) {
            logger.warn("加载工具配置失败: {}, 错误: {}", configPath, e.getMessage());
        }
    }

    /**
     * 从文件加载系统提示词
     *
     * @param toolsetId 工具集ID
     * @param promptFile 提示词文件名
     * @return 提示词内容，失败返回null
     */
    public String loadSystemPrompt(String toolsetId, String promptFile) {
        String cacheKey = toolsetId + "/" + promptFile;

        // 检查缓存
        if (promptCache.containsKey(cacheKey)) {
            return promptCache.get(cacheKey);
        }

        try {
            Path promptPath = Paths.get(configDir, toolsetId, "prompts", promptFile);
            if (!Files.exists(promptPath)) {
                logger.warn("系统提示词文件不存在: {}", promptPath);
                return null;
            }

            String content = Files.readString(promptPath);
            promptCache.put(cacheKey, content);
            return content;

        } catch (IOException e) {
            logger.error("读取系统提示词文件失败: {}", e.getMessage());
            return null;
        }
    }

    /**
     * 根据tool_id获取工具
     *
     * 对应Python: def get_tool_by_id(...)
     *
     * @param toolId 工具ID
     * @return 工具实体，不存在返回null
     */
    public com.platform.domain.tool.Tool getToolById(String toolId) {
        if (toolsCache.isEmpty()) {
            loadAllTools();
        }
        return toolsCache.get(toolId);
    }

    /**
     * 清除缓存
     */
    public void clearCache() {
        toolsCache.clear();
        promptCache.clear();
        cacheTimestamp = 0;
        logger.info("工具配置缓存已清除");
    }

    /**
     * 检查是否是YAML文件
     */
    private boolean isYamlFile(Path file) {
        String fileName = file.getFileName().toString();
        return fileName.endsWith(".yaml") || fileName.endsWith(".yml");
    }

    /**
     * 检查是否是特殊文件（categories.yaml, navigation.yaml等）
     */
    private boolean isSpecialFile(String fileName) {
        return fileName.equals("categories.yaml") ||
               fileName.equals("categories.yml") ||
               fileName.equals("navigation.yaml") ||
               fileName.equals("navigation.yml");
    }
}
