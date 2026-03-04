package com.platform.application.service;

import com.platform.infrastructure.ai.provider.ProviderFactory;
import dev.langchain4j.model.chat.ChatLanguageModel;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Mono;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * TitleGenerator单元测试
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("TitleGenerator单元测试")
class TitleGeneratorTest {

    @Mock
    private ProviderFactory providerFactory;

    @Mock
    private ChatLanguageModel chatModel;

    @InjectMocks
    private TitleGenerator titleGenerator;

    @Test
    @DisplayName("生成标题 - 空消息返回默认标题")
    void generateTitle_EmptyMessage_ReturnsDefaultTitle() {
        // When
        Mono<String> result = titleGenerator.generateTitle("", null);

        // Then
        assertThat(result.block()).isEqualTo("新对话");
    }

    @Test
    @DisplayName("生成标题 - 使用降级方案截取标题")
    void generateTitle_UsesFallback() {
        // Given
        String longMessage = "这是一个非常非常长的用户消息，超过了三十个字符的限制，应该被截断处理。";

        // When
        Mono<String> result = titleGenerator.generateTitle(longMessage, null);

        // Then
        String title = result.block();
        assertThat(title).isNotNull();
        assertThat(title.length()).isLessThanOrEqualTo(30);
    }

    @Test
    @DisplayName("降级标题生成 - 短消息原样返回")
    void fallbackTitle_ShortMessage_ReturnsAsIs() {
        // Given
        String shortMessage = "短消息";

        // When
        String result = titleGenerator.fallbackTitle(shortMessage);

        // Then
        assertThat(result).isEqualTo("短消息");
    }

    @Test
    @DisplayName("降级标题生成 - 长消息截取到30字符")
    void fallbackTitle_LongMessage_TruncatesTo30() {
        // Given
        String longMessage = "这是一个超过三十个字符限制的非常非常长的消息";
        assertThat(longMessage.length()).isGreaterThan(30);

        // When
        String result = titleGenerator.fallbackTitle(longMessage);

        // Then
        assertThat(result.length()).isEqualTo(30);
        assertThat(result).isEqualTo("这是一个超过三十个字符限制的非常");
    }

    @Test
    @DisplayName("降级标题生成 - 去除换行符")
    void fallbackTitle_RemovesNewlines() {
        // Given
        String message = "第一行\n第二行\r\n第三行";

        // When
        String result = titleGenerator.fallbackTitle(message);

        // Then
        assertThat(result).doesNotContain("\n").doesNotContain("\r");
        assertThat(result).isEqualTo("第一行 第二行 第三行");
    }

    @Test
    @DisplayName("降级标题生成 - 空消息返回默认标题")
    void fallbackTitle_EmptyMessage_ReturnsDefault() {
        // When
        String result = titleGenerator.fallbackTitle("");

        // Then
        assertThat(result).isEqualTo("新对话");
    }

    @Test
    @DisplayName("降级标题生成 - 去除前后空格")
    void fallbackTitle_TrimsWhitespace() {
        // Given
        String message = "   前后有空格的消息   ";

        // When
        String result = titleGenerator.fallbackTitle(message);

        // Then
        assertThat(result).isEqualTo("前后有空格的消息");
        assertThat(result).doesNotStartWith(" ").doesNotEndWith(" ");
    }

    @Test
    @DisplayName("生成标题 - 带助手回复")
    void generateTitle_WithAssistantMessage() {
        // Given
        String userMessage = "用户的问题";
        String assistantMessage = "AI的回复";

        // When
        Mono<String> result = titleGenerator.generateTitle(userMessage, assistantMessage);

        // Then
        String title = result.block();
        assertThat(title).isNotNull();
        // 当前实现使用降级方案，所以应该基于用户消息
        assertThat(title).contains("用户的问题");
    }

    @Test
    @DisplayName("生成标题 - 纯空格消息返回默认标题")
    void generateTitle_WhitespaceOnly_ReturnsDefault() {
        // When
        Mono<String> result = titleGenerator.generateTitle("   \n\t  ", null);

        // Then
        assertThat(result.block()).isEqualTo("新对话");
    }

    @Test
    @DisplayName("降级标题生成 - 多个换行符替换为空格")
    void fallbackTitle_MultipleNewlines_ReplacedWithSpaces() {
        // Given
        String message = "第一行\n\n\n第二行\r\r\r第三行";

        // When
        String result = titleGenerator.fallbackTitle(message);

        // Then
        assertThat(result).isEqualTo("第一行 第二行 第三行");
        assertThat(result).doesNotContain("\n").doesNotContain("\r");
    }

    @Test
    @DisplayName("降级标题生成 - 混合换行符")
    void fallbackTitle_MixedNewlines_ReplacedWithSpaces() {
        // Given
        String message = "第一行\n\r第二行\r\n第三行";

        // When
        String result = titleGenerator.fallbackTitle(message);

        // Then
        assertThat(result).isEqualTo("第一行 第二行 第三行");
    }

    @Test
    @DisplayName("降级标题生成 - 恰好30字符")
    void fallbackTitle_Exactly30Chars_ReturnsAsIs() {
        // Given
        String message = "123456789012345678901234567890"; // 30字符

        // When
        String result = titleGenerator.fallbackTitle(message);

        // Then
        assertThat(result).isEqualTo(message);
        assertThat(result.length()).isEqualTo(30);
    }

    @Test
    @DisplayName("降级标题生成 - 31字符被截断")
    void fallbackTitle_31Chars_TruncatesTo30() {
        // Given
        String message = "1234567890123456789012345678901"; // 31字符

        // When
        String result = titleGenerator.fallbackTitle(message);

        // Then
        assertThat(result.length()).isEqualTo(30);
        assertThat(result).isEqualTo("123456789012345678901234567890");
    }
}
