package com.aieducenter.studio.application.service;

import com.aieducenter.studio.domain.tool.Tool;
import com.aieducenter.studio.infrastructure.config.ToolConfigLoader;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

/**
 * ToolService单元测试
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("ToolService单元测试")
class ToolServiceTest {

    @Mock
    private ToolConfigLoader configLoader;

    @InjectMocks
    private ToolService toolService;

    private Tool testTool;

    @BeforeEach
    void setUp() {
        // 准备测试工具数据
        testTool = new Tool();
        testTool.setToolId("test-tool");
        testTool.setName("测试工具");
        testTool.setDescription("这是一个测试工具");
        testTool.setToolsetId("ai_tools");
        testTool.setModel("deepseek:deepseek-chat");
        testTool.setSystemPrompt("你是一个测试助手。");
        testTool.setSystemPromptFile(null);
    }

    @Test
    @DisplayName("获取所有工具 - 成功")
    void getAllTools_Success() {
        // Given
        List<Tool> expectedTools = List.of(testTool);
        when(configLoader.loadAllTools()).thenReturn(expectedTools);

        // When
        List<Tool> result = toolService.getAllTools();

        // Then
        assertThat(result).isNotNull();
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getToolId()).isEqualTo("test-tool");

        verify(configLoader).loadAllTools();
    }

    @Test
    @DisplayName("根据ID获取工具 - 成功")
    void getToolById_Success() {
        // Given
        when(configLoader.getToolById("test-tool")).thenReturn(testTool);

        // When
        Tool result = toolService.getToolById("test-tool");

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getToolId()).isEqualTo("test-tool");
        assertThat(result.getName()).isEqualTo("测试工具");

        verify(configLoader).getToolById("test-tool");
    }

    @Test
    @DisplayName("获取不存在的工具 - 返回null")
    void getToolById_NotFound_ReturnsNull() {
        // Given
        when(configLoader.getToolById("nonexistent")).thenReturn(null);

        // When
        Tool result = toolService.getToolById("nonexistent");

        // Then
        assertThat(result).isNull();

        verify(configLoader).getToolById("nonexistent");
    }

    @Test
    @DisplayName("获取工具系统提示词 - 使用直接配置的提示词")
    void getSystemPrompt_UsesDirectPrompt() {
        // Given
        testTool.setSystemPrompt("这是直接配置的提示词");
        when(configLoader.getToolById("test-tool")).thenReturn(testTool);

        // When
        String result = toolService.getSystemPrompt("test-tool");

        // Then
        assertThat(result).isEqualTo("这是直接配置的提示词");
    }

    @Test
    @DisplayName("获取工具系统提示词 - 使用文件中的提示词")
    void getSystemPrompt_UsesFilePrompt() {
        // Given
        testTool.setSystemPrompt(null);
        testTool.setSystemPromptFile("prompts/test.md");
        when(configLoader.getToolById("test-tool")).thenReturn(testTool);
        when(configLoader.loadSystemPrompt("ai_tools", "prompts/test.md"))
            .thenReturn("这是文件中的提示词");

        // When
        String result = toolService.getSystemPrompt("test-tool");

        // Then
        assertThat(result).isEqualTo("这是文件中的提示词");
        verify(configLoader).loadSystemPrompt("ai_tools", "prompts/test.md");
    }

    @Test
    @DisplayName("工具不存在时的系统提示词 - 返回默认提示词")
    void getSystemPrompt_ToolNotFound_ReturnsDefault() {
        // Given
        when(configLoader.getToolById("nonexistent")).thenReturn(null);

        // When
        String result = toolService.getSystemPrompt("nonexistent");

        // Then
        assertThat(result).isEqualTo("你是一个有用的AI助手。");
    }

    @Test
    @DisplayName("工具没有配置提示词 - 返回默认提示词")
    void getSystemPrompt_NoPromptConfigured_ReturnsDefault() {
        // Given
        testTool.setSystemPrompt(null);
        testTool.setSystemPromptFile(null);
        when(configLoader.getToolById("test-tool")).thenReturn(testTool);

        // When
        String result = toolService.getSystemPrompt("test-tool");

        // Then
        assertThat(result).isEqualTo("你是一个有用的AI助手。");
    }

    @Test
    @DisplayName("获取模型配置 - 成功")
    void getModelConfig_Success() {
        // Given
        when(configLoader.getToolById("test-tool")).thenReturn(testTool);

        // When
        String result = toolService.getModelConfig("test-tool");

        // Then
        assertThat(result).isEqualTo("deepseek:deepseek-chat");
    }

    @Test
    @DisplayName("获取不存在工具的模型配置 - 返回null")
    void getModelConfig_ToolNotFound_ReturnsNull() {
        // Given
        when(configLoader.getToolById("nonexistent")).thenReturn(null);

        // When
        String result = toolService.getModelConfig("nonexistent");

        // Then
        assertThat(result).isNull();
    }

    @Test
    @DisplayName("清除配置缓存 - 成功")
    void clearCache_Success() {
        // When
        toolService.clearCache();

        // Then
        verify(configLoader).clearCache();
    }

    @Test
    @DisplayName("优先使用直接配置的提示词而非文件")
    void getSystemPrompt_DirectPromptTakesPrecedence() {
        // Given
        testTool.setSystemPrompt("直接配置的提示词");
        testTool.setSystemPromptFile("prompts/test.md");
        when(configLoader.getToolById("test-tool")).thenReturn(testTool);

        // When
        String result = toolService.getSystemPrompt("test-tool");

        // Then
        assertThat(result).isEqualTo("直接配置的提示词");
        verify(configLoader, never()).loadSystemPrompt(anyString(), anyString());
    }

    @Test
    @DisplayName("空系统提示词字符串 - 使用文件或默认")
    void getSystemPrompt_EmptyPromptString_UsesFileOrDefault() {
        // Given
        testTool.setSystemPrompt("   ");
        testTool.setSystemPromptFile(null);
        when(configLoader.getToolById("test-tool")).thenReturn(testTool);

        // When
        String result = toolService.getSystemPrompt("test-tool");

        // Then
        assertThat(result).isEqualTo("你是一个有用的AI助手。");
    }

    @Test
    @DisplayName("空系统提示文件路径 - 使用直接配置或默认")
    void getSystemPrompt_EmptyPromptFile_UsesDirectOrDefault() {
        // Given
        testTool.setSystemPrompt(null);
        testTool.setSystemPromptFile("   ");
        when(configLoader.getToolById("test-tool")).thenReturn(testTool);
        when(configLoader.loadSystemPrompt(anyString(), anyString())).thenReturn(null);

        // When
        String result = toolService.getSystemPrompt("test-tool");

        // Then
        assertThat(result).isEqualTo("你是一个有用的AI助手。");
    }

    @Test
    @DisplayName("文件提示词加载失败 - 使用默认提示词")
    void getSystemPrompt_FileLoadFails_UsesDefault() {
        // Given
        testTool.setSystemPrompt(null);
        testTool.setSystemPromptFile("prompts/nonexistent.md");
        when(configLoader.getToolById("test-tool")).thenReturn(testTool);
        when(configLoader.loadSystemPrompt("ai_tools", "prompts/nonexistent.md"))
            .thenReturn(null);

        // When
        String result = toolService.getSystemPrompt("test-tool");

        // Then
        assertThat(result).isEqualTo("你是一个有用的AI助手。");
    }
}
