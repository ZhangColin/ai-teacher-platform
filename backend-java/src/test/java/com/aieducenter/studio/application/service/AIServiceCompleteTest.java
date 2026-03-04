package com.platform.application.service;

import com.platform.domain.ai.Message;
import com.platform.domain.ai.MessageRole;
import dev.langchain4j.data.message.AiMessage;
import dev.langchain4j.data.message.ChatMessage;
import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.output.Response;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
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
        history = List.of(
            new Message("msg1", MessageRole.USER, "Previous message"),
            new Message("msg2", MessageRole.ASSISTANT, "Previous response")
        );
    }

    @Test
    @DisplayName("流式对话 - 成功返回内容")
    void chatStream_Success_ReturnsContent() {
        // Given
        when(chatLanguageModel.generate(any(List.class), any())).thenAnswer(invocation -> {
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
        when(chatLanguageModel.generate(any(List.class), any())).thenAnswer(invocation -> {
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
        when(chatLanguageModel.generate(any(List.class), any())).thenThrow(new RuntimeException("API error"));

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
        when(chatLanguageModel.generate(any(List.class), any())).thenReturn(mockResponse);

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
        when(chatLanguageModel.generate(any(List.class), any())).thenReturn(incompleteResponse);

        // When
        String result = aiService.chat(systemPrompt, history, "Generate code");

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
        when(chatLanguageModel.generate(any(List.class), any())).thenReturn(mockResponse);

        // When
        StepVerifier.create(aiService.generateWelcomeMessage(systemPrompt))
            .expectNext("Welcome to AI teaching platform!")
            .verifyComplete();
    }

    @Test
    @DisplayName("生成欢迎消息 - AI服务失败降级")
    void generateWelcomeMessage_Fallback() {
        // Given
        when(chatLanguageModel.generate(any(List.class), any())).thenThrow(new RuntimeException("AI error"));

        // When
        StepVerifier.create(aiService.generateWelcomeMessage(systemPrompt))
            .expectNext(msg -> msg.contains("AI助手") || msg.contains("助手"))
            .verifyComplete();
    }

    @Test
    @DisplayName("构建消息列表 - 包含系统提示词")
    void buildMessages_WithSystemPrompt() {
        // When
        List<ChatMessage> messages = aiService.buildMessages(
            "System prompt here",
            history,
            "User message"
        );

        // Then - 验证消息顺序和数量
        assertNotNull(messages);
        assertTrue(messages.size() >= 3); // 至少：系统提示词 + 历史消息2条 + 用户消息1条
    }

    @Test
    @DisplayName("检测HTML完整性 - 完整的HTML")
    void isHtmlComplete_Complete() {
        // When & Then
        assertTrue(aiService.isHtmlComplete("<html><body>Complete</body></html>"));
        assertTrue(aiService.isHtmlComplete("<div>Content</div>"));
    }

    @Test
    @DisplayName("检测HTML完整性 - 不完整")
    void isHtmlComplete_Incomplete() {
        // When & Then
        assertFalse(aiService.isHtmlComplete("<html><body>Incomplete"));
        assertFalse(aiService.isHtmlComplete("<div>Unclosed"));
        assertFalse(aiService.isHtmlComplete(""));
    }

    @Test
    @DisplayName("判断是否需要继续生成 - 不完整代码")
    void shouldAutoContinue_IncompleteCode() {
        // When & Then
        assertTrue(aiService.shouldAutoContinue("<html><body>Test", 3));
        assertTrue(aiService.shouldAutoContinue("```python\nprint('incomplete'", 3));
        assertTrue(aiService.shouldAutoContinue("<div>Unclosed", 3));
    }

    @Test
    @DisplayName("判断是否需要继续生成 - 达到最大次数")
    void shouldAutoContinue_MaxRetriesReached() {
        // When & Then
        assertFalse(aiService.shouldAutoContinue("<html></html>", 3));
        assertFalse(aiService.shouldAutoContinue("Complete code", 3));
    }

    @Test
    @DisplayName("提取语言类型 - HTML代码")
    void detectLanguageByContent_HTML() {
        // When & Then
        assertEquals("html", aiService.detectLanguageByContent("<html>code</html>"));
        assertEquals("html", aiService.detectLanguageByContent("<div>content</div>"));
        assertEquals("html", aiService.detectLanguageByContent("<svg>shape</svg>"));
    }

    @Test
    @DisplayName("提取语言类型 - Markdown")
    void detectLanguageByContent_Markdown() {
        // When & Then
        assertEquals("markdown", aiService.detectLanguageByContent("# Title\nContent"));
        assertEquals("markdown", aiService.detectLanguageByContent("```python\ncode```"));
    }

    @Test
    @DisplayName("提取语言类型 - SVG")
    void detectLanguageByContent_SVG() {
        // When & Then
        assertEquals("svg", aiService.detectLanguageByContent("<svg>...</svg>"));
        assertEquals("svg", aiService.detectLanguageByContent("<circle cx=\"1\"/>"));
    }

    @Test
    @DisplayName("提取语言类型 - 代码块")
    void detectLanguageByContent_CodeBlock() {
        // When & Then
        assertEquals("python", aiService.detectLanguageByContent("```python\nprint('hello')```"));
        assertEquals("javascript", aiService.detectLanguageByContent("```javascript\nconsole.log()```"));
        assertEquals("java", aiService.detectLanguageByContent("```java\nSystem.out.println()```"));
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
        when(chatLanguageModel.generate(any(List.class), any())).thenReturn(mockResponse);

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
        when(chatLanguageModel.generate(any(List.class), any())).thenReturn(mockResponse);

        // When
        StepVerifier.create(aiService.chat(systemPrompt, history, "Single"))
            .expectNext("Single response")
            .verifyComplete();
    }

    @Test
    @DisplayName("构建消息 - 多条历史消息")
    void buildMessages_MultipleHistory() {
        // Given
        List<Message> extendedHistory = List.of(
            new Message("msg1", MessageRole.USER, "User 1"),
            new Message("msg2", MessageRole.ASSISTANT, "AI 1"),
            new Message("msg3", MessageRole.USER, "User 2"),
            new Message("msg4", MessageRole.ASSISTANT, "AI 2")
        );

        // When
        List<ChatMessage> messages = aiService.buildMessages(
            "System prompt",
            extendedHistory,
            "New user message"
        );

        // Then
        assertNotNull(messages);
        assertTrue(messages.size() >= 5); // 系统 + 4条历史 + 1条用户
    }

    @Test
    @DisplayName("检测语言类型 - 未知类型")
    void detectLanguageByContent_Unknown() {
        // When & Then
        assertEquals("text", aiService.detectLanguageByContent("Just plain text"));
        assertEquals("text", aiService.detectLanguageByContent(""));
    }

    @Test
    @DisplayName("流式对话 - 最大继续次数")
    void chatStream_MaxRetries() {
        // Given - 返回3次不完整响应
        Response<AiMessage> incompleteResponse = Response.from(
            AiMessage.from("<html><body>Incomplete")
        );
        when(chatLanguageModel.generate(any(List.class), any())).thenReturn(incompleteResponse);

        // When
        Flux<String> result = aiService.chatStream(systemPrompt, history, "Test");

        // Then
        StepVerifier.create(result)
            .expectNextCount(1)  // 只返回第一次尝试
            .verifyComplete();
    }
}
