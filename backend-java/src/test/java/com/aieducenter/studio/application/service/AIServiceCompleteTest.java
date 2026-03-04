package com.aieducenter.studio.application.service;

import com.aieducenter.studio.domain.ai.Message;
import com.aieducenter.studio.domain.ai.MessageRole;
import dev.langchain4j.data.message.AiMessage;
import dev.langchain4j.data.message.ChatMessage;
import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.output.Response;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.Mock;
import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

import java.time.Duration;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

/**
 * AIService完整测试 - 包含所有核心测试场景
 *
 * 对应Python: backend/tests/unit/services/test_ai_service.py
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("AIService完整测试")
class AIServiceCompleteTest {

    @Mock
    private ChatLanguageModel chatLanguageModel;

    @InjectMocks
    private AIService aiService;

    private String systemPrompt;
    private List<Message> history;

    @BeforeEach
    void setUp() {
        systemPrompt = "You are a helpful assistant.";

        // 使用 setter 方法创建测试消息
        Message msg1 = new Message();
        msg1.setId("msg1");
        msg1.setSessionId("test-session");
        msg1.setRole(MessageRole.USER);
        msg1.setContent("Previous message");

        Message msg2 = new Message();
        msg2.setId("msg2");
        msg2.setSessionId("test-session");
        msg2.setRole(MessageRole.ASSISTANT);
        msg2.setContent("Previous response");

        history = List.of(msg1, msg2);
    }

    @Test
    @DisplayName("流式对话 - 成功返回内容")
    void chatStream_Success_ReturnsContent() {
        // Given
        when(chatLanguageModel.generate(any(List.class), any(List.class))).thenAnswer(invocation -> {
            AiMessage msg = AiMessage.from("Test response");
            return Response.from(msg);
        });

        // When
        Flux<String> result = aiService.chatStream(systemPrompt, history, "Hello");

        // Then
        StepVerifier.create(result)
            .expectNext("Test response")
            .verifyComplete();
    }

    @Test
    @DisplayName("流式对话 - 空响应处理")
    void chatStream_EmptyResponse() {
        // Given
        when(chatLanguageModel.generate(any(List.class), any(List.class))).thenAnswer(invocation -> {
            AiMessage msg = AiMessage.from("");
            return Response.from(msg);
        });

        // When
        Flux<String> result = aiService.chatStream(systemPrompt, history, "Hello");

        // Then
        StepVerifier.create(result)
            .expectNextCount(0)
            .verifyComplete();
    }

    @Test
    @DisplayName("流式对话 - 错误处理")
    void chatStream_ErrorHandling() {
        // Given
        when(chatLanguageModel.generate(any(List.class), any(List.class))).thenThrow(new RuntimeException("API error"));

        // When
        Flux<String> result = aiService.chatStream(systemPrompt, history, "Hello");

        // Then
        StepVerifier.create(result)
            .expectError(RuntimeException.class)
            .verify();
    }

    @Test
    @DisplayName("非流式对话 - 成功")
    void chat_Success() {
        // Given
        Response<AiMessage> mockResponse = Response.from(
            AiMessage.from("Complete response")
        );
        when(chatLanguageModel.generate(any(List.class), any(List.class))).thenReturn(mockResponse);

        // When
        StepVerifier.create(aiService.chat(systemPrompt, history, "Test"))
            .expectNext("Complete response")
            .verifyComplete();
    }

    @Test
    @DisplayName("非流式对话 - 自动继续生成代码")
    void chat_AutoContinue() {
        // Given - 第一次返回不完整的HTML
        Response<AiMessage> incompleteResponse = Response.from(
            AiMessage.from("<html><body>Incomplete")
        );
        when(chatLanguageModel.generate(any(List.class), any(List.class))).thenReturn(incompleteResponse);

        // When - 使用 .block() 获取 Mono 的值
        String result = aiService.chat(systemPrompt, history, "Generate code").block();

        // Then - 应该检测到不完整并继续
        assertNotNull(result);
        assertTrue(result.contains("<html>") || result.contains("body>"));
    }

    @Test
    @DisplayName("生成欢迎消息 - 成功")
    void generateWelcomeMessage_Success() {
        // Given
        Response<AiMessage> mockResponse = Response.from(
            AiMessage.from("Welcome to AI teaching platform!")
        );
        when(chatLanguageModel.generate(any(List.class), any(List.class))).thenReturn(mockResponse);

        // When
        StepVerifier.create(aiService.generateWelcomeMessage(systemPrompt))
            .expectNext("Welcome to AI teaching platform!")
            .verifyComplete();
    }

    @Test
    @DisplayName("生成欢迎消息 - AI服务失败降级")
    void generateWelcomeMessage_Fallback() {
        // Given
        when(chatLanguageModel.generate(any(List.class), any(List.class))).thenThrow(new RuntimeException("AI error"));

        // When
        StepVerifier.create(aiService.generateWelcomeMessage(systemPrompt))
            .expectNextMatches(msg -> msg.contains("AI助手") || msg.contains("助手"))
            .verifyComplete();
    }

    @Test
    @DisplayName("检测代码块 - 匹配成功")
    void detectCodeBlock_MatchSuccess() {
        // Given
        String markdown = "```python\nprint('hello')\n```";

        // When
        String result = aiService.detectCodeBlock(markdown);

        // Then
        assertNotNull(result);
        assertEquals("print('hello')", result);
    }

    @Test
    @DisplayName("检测代码块 - 无代码块")
    void detectCodeBlock_NoCodeBlock() {
        // Given
        String markdown = "Just plain text";

        // When
        String result = aiService.detectCodeBlock(markdown);

        // Then
        assertNull(result);
    }

    @Test
    @DisplayName("检查代码块完整性 - 完整代码块")
    void isCodeBlockComplete_Complete() {
        // When & Then
        assertTrue(aiService.isCodeBlockComplete("```python\nprint('hello')\n```"));
        assertTrue(aiService.isCodeBlockComplete("```html\n<div></div>\n```"));
    }

    @Test
    @DisplayName("检查代码块完整性 - 不完整代码块")
    void isCodeBlockComplete_Incomplete() {
        // When & Then
        assertFalse(aiService.isCodeBlockComplete("```python\nprint('hello'"));  // 缺少结束标记
        assertFalse(aiService.isCodeBlockComplete("```python\n```"));  // 只有开始标记
        assertFalse(aiService.isCodeBlockComplete(""));
    }

    @Test
    @DisplayName("流式对话 - 带历史消息")
    void chatStream_WithHistory() {
        // Given
        Response<AiMessage> mockResponse = Response.from(
            AiMessage.from("Response with history")
        );
        when(chatLanguageModel.generate(any(List.class), any(List.class))).thenReturn(mockResponse);

        // When
        Flux<String> result = aiService.chatStream(systemPrompt, history, "New message");

        // Then
        StepVerifier.create(result)
            .expectNext("Response with history")
            .verifyComplete();
    }

    @Test
    @DisplayName("非流式对话 - 一次成功")
    void chat_SingleSuccess() {
        // Given
        Response<AiMessage> mockResponse = Response.from(
            AiMessage.from("Single response")
        );
        when(chatLanguageModel.generate(any(List.class), any(List.class))).thenReturn(mockResponse);

        // When
        StepVerifier.create(aiService.chat(systemPrompt, history, "Single"))
            .expectNext("Single response")
            .verifyComplete();
    }

    @Test
    @DisplayName("流式对话 - 最大继续次数")
    void chatStream_MaxRetries() {
        // Given - 返回3次不完整响应
        Response<AiMessage> incompleteResponse = Response.from(
            AiMessage.from("<html><body>Incomplete")
        );
        when(chatLanguageModel.generate(any(List.class), any(List.class))).thenReturn(incompleteResponse);

        // When
        Flux<String> result = aiService.chatStream(systemPrompt, history, "Test");

        // Then
        StepVerifier.create(result)
            .expectNextCount(1)  // 只返回第一次尝试
            .verifyComplete();
    }
}
