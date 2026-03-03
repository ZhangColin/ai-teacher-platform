package com.platform.application.service;

import org.springframework.stereotype.Service;

/**
 * 工具服务（占位符）
 *
 * 对应Python: backend/src/services/tool_service.py
 * TODO: Task 11 实现
 *
 * @author AI Teacher Platform
 */
@Service
public class ToolService {

    /**
     * 获取工具系统提示词
     *
     * @param toolId 工具ID
     * @return 系统提示词
     */
    public String getSystemPrompt(String toolId) {
        // TODO: 实现工具配置加载
        return "你是一个有用的AI助手。";
    }

    /**
     * 获取工具模型配置
     *
     * @param toolId 工具ID
     * @return 模型配置
     */
    public String getModelConfig(String toolId) {
        // TODO: 实现工具配置加载
        return null;
    }
}
