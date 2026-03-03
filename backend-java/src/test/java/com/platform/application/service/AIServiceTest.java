package com.platform.application.service;

import com.platform.domain.ai.Message;
import com.platform.domain.ai.MessageRole;
import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.output.Response;
import dev.langchain4j.data.message.AiMessage;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

/**
 * AIService单元测试
 *
 * 对应Python: backend/tests/unit/test_ai_service.py
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("AIService单元测试")
class AIServiceTest {

    @Mock
    private ChatLanguageModel chatLanguageModel;

    @InjectMocks
    private AIService aiService;

    private List<Message> history;
    private String systemPrompt;

    @BeforeEach
    void setUp() {
        systemPrompt = "You are a helpful assistant.";
        history = List.of(
            Message.createUserMessage("session-1", "Hello"),
            Message.createAssistantMessage("session-1", "Hi there!", null)
        );
    }

    @Test
    @DisplayName("非流式对话 - 成功")
    void chat_Success() {
        // Given
        Response<AiMessage> mockResponse = Response.from(
            AiMessage.from("This is a test response.")
        );
        when(chatLanguageModel.generate(any())).thenReturn(mockResponse);

        // When
        StepVerifier.create(aiService.chat(systemPrompt, history, "Test message"))
            .expectNextCount(11) // "This is a test response." 长度
            .verifyComplete();
    }

    @Test
    @DisplayName("非流式对话 - 失败（异常处理）")
    void chat_Error() {
        // Given
        when(chatLanguageModel.generate(any())).thenThrow(new RuntimeException("AI service error"));

        // When
        StepVerifier.create(aiService.chat(systemPrompt, history, "Test message"))
            .expectError(RuntimeException.class)
            .verify();
    }

    @Test
    @DisplayName("生成欢迎消息 - 成功")
    void generateWelcomeMessage_Success() {
        // Given
        Response<AiMessage> mockResponse = Response.from(
            AiMessage.from("Hello! How can I help you today?")
        );
        when(chatLanguageModel.generate(any())).thenReturn(mockResponse);

        // When
        StepVerifier.create(aiService.generateWelcomeMessage(systemPrompt))
            .expectNext("Hello! How can I help you today?")
            .verifyComplete();
    }

    @Test
    @DisplayName("生成欢迎消息 - 失败（降级处理）")
    void generateWelcomeMessage_Error() {
        // Given
        when(chatLanguageModel.generate(any())).thenThrow(new RuntimeException("AI error"));

        // When
        StepVerifier.create(aiService.generateWelcomeMessage(systemPrompt))
            .expectNextMatches(msg -> msg.contains("AI助手") || msg.contains("助手"))
            .verifyComplete();
    }
}
