package com.aieducenter.studio.application.service;

import com.aieducenter.studio.domain.tool.Tool;
import com.aieducenter.studio.infrastructure.config.ToolConfigLoader;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 工具服务
 *
 * 对应Python: backend/src/services/tool_service.py
 * 负责工具配置的加载和查询
 *
 * @author AI Teacher Platform
 */
@Service
public class ToolService {

    private static final Logger logger = LoggerFactory.getLogger(ToolService.class);

    private final ToolConfigLoader configLoader;

    public ToolService(ToolConfigLoader configLoader) {
        this.configLoader = configLoader;
    }

    /**
     * 获取所有工具列表
     *
     * 对应Python: def load_all_tools() -> List[Tool]
     *
     * @return 工具列表
     */
    public List<Tool> getAllTools() {
        return configLoader.loadAllTools();
    }

    /**
     * 根据tool_id获取工具
     *
     * 对应Python: def get_tool_by_id(...)
     *
     * @param toolId 工具ID
     * @return 工具实体，不存在返回null
     */
    public Tool getToolById(String toolId) {
        return configLoader.getToolById(toolId);
    }

    /**
     * 获取工具系统提示词
     *
     * @param toolId 工具ID
     * @return 系统提示词
     */
    public String getSystemPrompt(String toolId) {
        Tool tool = getToolById(toolId);
        if (tool == null) {
            logger.warn("工具不存在: {}", toolId);
            return "你是一个有用的AI助手。";
        }

        // 优先使用system_prompt
        if (tool.getSystemPrompt() != null && !tool.getSystemPrompt().trim().isEmpty()) {
            return tool.getSystemPrompt();
        }

        // 如果指定了system_prompt_file，从文件加载
        if (tool.getSystemPromptFile() != null && !tool.getSystemPromptFile().trim().isEmpty()) {
            String prompt = configLoader.loadSystemPrompt(
                tool.getToolsetId(),
                tool.getSystemPromptFile()
            );
            if (prompt != null) {
                return prompt;
            }
        }

        return "你是一个有用的AI助手。";
    }

    /**
     * 获取工具模型配置
     *
     * @param toolId 工具ID
     * @return 模型配置（格式：provider:model_name）
     */
    public String getModelConfig(String toolId) {
        Tool tool = getToolById(toolId);
        return tool != null ? tool.getModel() : null;
    }

    /**
     * 清除配置缓存
     */
    public void clearCache() {
        configLoader.clearCache();
    }
}
