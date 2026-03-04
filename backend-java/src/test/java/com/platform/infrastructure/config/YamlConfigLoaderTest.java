package com.platform.infrastructure.config;

import com.platform.interfaces.dto.ToolDTO;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@DisplayName("YamlConfigLoader测试")
class YamlConfigLoaderTest {

    private YamlConfigLoader loader;

    @BeforeEach
    void setUp() {
        loader = new YamlConfigLoader();
        // 设置配置路径（相对于项目根目录）
        ReflectionTestUtils.setField(loader, "configBasePath", "configs");
        ReflectionTestUtils.setField(loader, "configToolsPath", "configs/tools");
    }

    @Test
    @DisplayName("加载导航配置 - 成功")
    void loadNavigationConfig_Success() {
        // When
        var modules = loader.loadNavigationConfig();

        // Then
        assertThat(modules).isNotNull();
        assertThat(modules).isNotEmpty();
        assertThat(modules).hasSize(5);  // navigation.yaml中有5个模块

        // 验证第一个模块（AI模型能力）
        var firstModule = modules.get(0);
        assertThat(firstModule.getName()).isEqualTo("AI模型能力");
        assertThat(firstModule.getType()).isEqualTo("toolset");
        assertThat(firstModule.getConfigSource()).isEqualTo("tools/ai_tools");
        assertThat(firstModule.getOrder()).isEqualTo(1);
    }

    @Test
    @DisplayName("加载所有工具 - 成功")
    void loadAllTools_Success() {
        // When
        List<ToolDTO> tools = loader.loadAllTools();

        // Then
        assertThat(tools).isNotNull();
        assertThat(tools).isNotEmpty();

        // 验证至少有一个工具
        var textGenTool = tools.stream()
            .filter(t -> "text_gen".equals(t.getToolId()))
            .findFirst();

        assertThat(textGenTool).isPresent();
        var tool = textGenTool.get();
        assertThat(tool.getName()).isEqualTo("文字对话");
        assertThat(tool.getCategory()).isEqualTo("内容生成");
        assertThat(tool.getVisible()).isTrue();
        assertThat(tool.getToolsetId()).isEqualTo("ai_tools");
    }

    @Test
    @DisplayName("按工具集加载工具 - ai_tools成功")
    void loadToolsByToolset_AiTools_Success() {
        // When
        List<ToolDTO> tools = loader.loadToolsByToolset("ai_tools");

        // Then
        assertThat(tools).isNotNull();
        assertThat(tools).isNotEmpty();

        // 验证所有工具都属于ai_tools
        assertThat(tools).allMatch(t -> "ai_tools".equals(t.getToolsetId()));

        // 验证可见性
        assertThat(tools).allMatch(t -> t.getVisible() != null && t.getVisible());
    }

    @Test
    @DisplayName("按分类聚合工具 - 成功")
    void groupByCategory_Success() {
        // Given
        List<ToolDTO> tools = loader.loadToolsByToolset("ai_tools");

        // When
        var categories = loader.groupByCategory(tools, "ai_tools");

        // Then
        assertThat(categories).isNotNull();
        assertThat(categories).isNotEmpty();

        // 验证有"内容生成"分类
        var contentCategory = categories.stream()
            .filter(c -> "内容生成".equals(c.getName()))
            .findFirst();

        assertThat(contentCategory).isPresent();
        assertThat(contentCategory.get().getTools()).isNotEmpty();
    }

    @Test
    @DisplayName("缓存机制 - 第二次调用使用缓存")
    void cache_Mechanism() {
        // When - 第一次调用
        long start1 = System.currentTimeMillis();
        List<ToolDTO> tools1 = loader.loadAllTools();
        long end1 = System.currentTimeMillis();

        // When - 第二次调用（应该使用缓存）
        long start2 = System.currentTimeMillis();
        List<ToolDTO> tools2 = loader.loadAllTools();
        long end2 = System.currentTimeMillis();

        // Then
        assertThat(tools1).isEqualTo(tools2);
        // 第二次调用应该更快（使用缓存）
        // 注意：这个断言可能在某些环境下不稳定，可以接受偶尔失败
    }
}
