package com.platform.domain.tool;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Tool领域实体单元测试
 */
@DisplayName("Tool领域实体单元测试")
class ToolTest {

    @Test
    @DisplayName("验证工具配置 - 完整配置返回true")
    void validate_CompleteConfiguration_ReturnsTrue() {
        // Given
        Tool tool = Tool.builder()
            .toolId("test-tool")
            .name("测试工具")
            .category("测试分类")
            .welcomeMessage("欢迎使用测试工具")
            .systemPrompt("你是一个测试助手")
            .build();

        // When
        boolean result = tool.validate();

        // Then
        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("验证工具配置 - 使用systemPromptFile")
    void validate_WithSystemPromptFile_ReturnsTrue() {
        // Given
        Tool tool = Tool.builder()
            .toolId("test-tool")
            .name("测试工具")
            .category("测试分类")
            .welcomeMessage("欢迎使用")
            .systemPromptFile("prompts/test.md")
            .build();

        // When
        boolean result = tool.validate();

        // Then
        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("验证工具配置 - toolId为空返回false")
    void validate_EmptyToolId_ReturnsFalse() {
        // Given
        Tool tool = Tool.builder()
            .toolId("")
            .name("测试工具")
            .category("测试分类")
            .welcomeMessage("欢迎使用")
            .systemPrompt("提示词")
            .build();

        // When
        boolean result = tool.validate();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("验证工具配置 - name为空返回false")
    void validate_EmptyName_ReturnsFalse() {
        // Given
        Tool tool = Tool.builder()
            .toolId("test-tool")
            .name("")
            .category("测试分类")
            .welcomeMessage("欢迎使用")
            .systemPrompt("提示词")
            .build();

        // When
        boolean result = tool.validate();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("验证工具配置 - category为空返回false")
    void validate_EmptyCategory_ReturnsFalse() {
        // Given
        Tool tool = Tool.builder()
            .toolId("test-tool")
            .name("测试工具")
            .category("")
            .welcomeMessage("欢迎使用")
            .systemPrompt("提示词")
            .build();

        // When
        boolean result = tool.validate();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("验证工具配置 - welcomeMessage为空返回false")
    void validate_EmptyWelcomeMessage_ReturnsFalse() {
        // Given
        Tool tool = Tool.builder()
            .toolId("test-tool")
            .name("测试工具")
            .category("测试分类")
            .welcomeMessage("")
            .systemPrompt("提示词")
            .build();

        // When
        boolean result = tool.validate();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("验证工具配置 - 缺少systemPrompt和systemPromptFile返回false")
    void validate_NoSystemPrompt_ReturnsFalse() {
        // Given
        Tool tool = Tool.builder()
            .toolId("test-tool")
            .name("测试工具")
            .category("测试分类")
            .welcomeMessage("欢迎使用")
            .build();

        // When
        boolean result = tool.validate();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("验证工具配置 - 多模态工具缺少mediaType返回false")
    void validate_MultimodalWithoutMediaType_ReturnsFalse() {
        // Given
        Tool tool = Tool.builder()
            .toolId("test-tool")
            .name("测试工具")
            .category("测试分类")
            .welcomeMessage("欢迎使用")
            .systemPrompt("提示词")
            .contentType("multimodal")
            .mediaType(null)
            .build();

        // When
        boolean result = tool.validate();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("验证工具配置 - 多模态工具有mediaType返回true")
    void validate_MultimodalWithMediaType_ReturnsTrue() {
        // Given
        Tool tool = Tool.builder()
            .toolId("test-tool")
            .name("测试工具")
            .category("测试分类")
            .welcomeMessage("欢迎使用")
            .systemPrompt("提示词")
            .contentType("multimodal")
            .mediaType("image")
            .build();

        // When
        boolean result = tool.validate();

        // Then
        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("验证工具配置 - 文本工具不需要mediaType")
    void validate_TextTool_NoMediaTypeRequired() {
        // Given
        Tool tool = Tool.builder()
            .toolId("test-tool")
            .name("测试工具")
            .category("测试分类")
            .welcomeMessage("欢迎使用")
            .systemPrompt("提示词")
            .contentType("text")
            .mediaType(null)
            .build();

        // When
        boolean result = tool.validate();

        // Then
        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("Lombok @Builder - Builder模式工作正常")
    void lombokBuilder_Works() {
        // When
        Tool tool = Tool.builder()
            .toolId("test-tool")
            .name("测试工具")
            .description("这是一个测试工具")
            .category("测试分类")
            .icon("🔧")
            .visible(true)
            .type("normal")
            .welcomeMessage("欢迎使用")
            .order(1)
            .toolsetId("ai_tools")
            .systemPrompt("提示词")
            .model("deepseek:deepseek-chat")
            .contentType("text")
            .build();

        // Then
        assertThat(tool.getToolId()).isEqualTo("test-tool");
        assertThat(tool.getName()).isEqualTo("测试工具");
        assertThat(tool.getDescription()).isEqualTo("这是一个测试工具");
        assertThat(tool.getCategory()).isEqualTo("测试分类");
        assertThat(tool.getIcon()).isEqualTo("🔧");
        assertThat(tool.getVisible()).isTrue();
        assertThat(tool.getType()).isEqualTo("normal");
        assertThat(tool.getWelcomeMessage()).isEqualTo("欢迎使用");
        assertThat(tool.getOrder()).isEqualTo(1);
        assertThat(tool.getToolsetId()).isEqualTo("ai_tools");
        assertThat(tool.getSystemPrompt()).isEqualTo("提示词");
        assertThat(tool.getModel()).isEqualTo("deepseek:deepseek-chat");
        assertThat(tool.getContentType()).isEqualTo("text");
    }

    @Test
    @DisplayName("Lombok全参构造 - 工作正常")
    void lombokAllArgsConstructor_Works() {
        // When
        Tool tool = new Tool(
            "test-tool", "测试工具", "描述", "提示词", "分类", "🔧",
            true, "normal", "欢迎使用", 1, "ai_tools", "prompts/test.md",
            "deepseek:deepseek-chat", "text", "image"
        );

        // Then
        assertThat(tool.getToolId()).isEqualTo("test-tool");
        assertThat(tool.getName()).isEqualTo("测试工具");
    }

    @Test
    @DisplayName("Lombok无参构造 - 工作正常")
    void lombokNoArgsConstructor_Works() {
        // When
        Tool tool = new Tool();

        // Then
        assertThat(tool).isNotNull();
    }

    @Test
    @DisplayName("验证 - toolId为null返回false")
    void validate_NullToolId_ReturnsFalse() {
        // Given
        Tool tool = Tool.builder()
            .toolId(null)
            .name("测试工具")
            .category("测试分类")
            .welcomeMessage("欢迎使用")
            .systemPrompt("提示词")
            .build();

        // When
        boolean result = tool.validate();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("验证 - toolId只有空格返回false")
    void validate_WhitespaceOnlyToolId_ReturnsFalse() {
        // Given
        Tool tool = Tool.builder()
            .toolId("   ")
            .name("测试工具")
            .category("测试分类")
            .welcomeMessage("欢迎使用")
            .systemPrompt("提示词")
            .build();

        // When
        boolean result = tool.validate();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("验证 - 两个提示词都为空字符串返回false")
    void validate_BothPromptsEmptyStrings_ReturnsFalse() {
        // Given
        Tool tool = Tool.builder()
            .toolId("test-tool")
            .name("测试工具")
            .category("测试分类")
            .welcomeMessage("欢迎使用")
            .systemPrompt("   ")
            .systemPromptFile("   ")
            .build();

        // When
        boolean result = tool.validate();

        // Then
        assertThat(result).isFalse();
    }
}
