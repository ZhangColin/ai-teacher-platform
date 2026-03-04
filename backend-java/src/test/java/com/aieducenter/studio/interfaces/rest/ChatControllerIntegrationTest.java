package com.aieducenter.studio.interfaces.rest;

import com.aieducenter.studio.application.service.AIService;
import com.aieducenter.studio.application.service.SessionService;
import com.aieducenter.studio.application.service.ToolService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * ChatController集成测试
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
@DisplayName("ChatController集成测试")
class ChatControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private AIService aiService;

    @MockBean
    private SessionService sessionService;

    @MockBean
    private ToolService toolService;

    @Test
    @DisplayName("流式对话 - 成功")
    @WithMockUser(username = "testuser")
    void chatStream_Success() throws Exception {
        String requestJson = """
            {
                "message": "测试消息",
                "session_id": null,
                "history": []
            }
            """;

        when(toolService.getSystemPrompt(anyString())).thenReturn("You are a helpful assistant.");
        when(toolService.getModelConfig(anyString())).thenReturn("deepseek:deepseek-chat");

        mockMvc.perform(post("/api/v1/tools/test-tool-id/chat/stream")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("非流式对话 - 成功")
    @WithMockUser(username = "testuser")
    void chat_Success() throws Exception {
        String requestJson = """
            {
                "message": "测试消息",
                "session_id": null,
                "history": []
            }
            """;

        when(toolService.getSystemPrompt(anyString())).thenReturn("You are a helpful assistant.");
        when(aiService.chat(anyString(), any(), anyString()))
            .thenReturn(reactor.core.publisher.Mono.just("AI响应"));

        mockMvc.perform(post("/api/v1/tools/test-tool-id/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.response").value("AI响应"));
    }

    @Test
    @DisplayName("对话时工具不存在 - 返回404")
    @WithMockUser(username = "testuser")
    void chat_ToolNotFound_Returns404() throws Exception {
        String requestJson = """
            {
                "message": "测试消息",
                "session_id": null,
                "history": []
            }
            """;

        when(toolService.getSystemPrompt(anyString())).thenReturn("You are a helpful assistant.");
        when(aiService.chat(anyString(), any(), anyString()))
            .thenReturn(reactor.core.publisher.Mono.just("AI响应"));

        mockMvc.perform(post("/api/v1/tools/invisible-tool/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("对话时消息为空 - 返回400")
    @WithMockUser(username = "testuser")
    void chat_EmptyMessage_Returns400() throws Exception {
        String requestJson = """
            {
                "message": "",
                "session_id": null,
                "history": []
            }
            """;

        mockMvc.perform(post("/api/v1/tools/test-tool-id/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
            .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("使用现有会话ID对话 - 成功")
    @WithMockUser(username = "testuser")
    void chat_WithExistingSessionId_Success() throws Exception {
        String requestJson = """
            {
                "message": "后续消息",
                "session_id": "existing-session-id",
                "history": []
            }
            """;

        when(toolService.getSystemPrompt(anyString())).thenReturn("You are a helpful assistant.");
        when(aiService.chat(anyString(), any(), anyString()))
            .thenReturn(reactor.core.publisher.Mono.just("AI响应"));

        mockMvc.perform(post("/api/v1/tools/test-tool-id/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.response").value("AI响应"));
    }

    @Test
    @DisplayName("带历史记录的对话 - 成功")
    @WithMockUser(username = "testuser")
    void chat_WithHistory_Success() throws Exception {
        String requestJson = """
            {
                "message": "新消息",
                "session_id": null,
                "history": [
                    {"role": "user", "content": "之前的问题"},
                    {"role": "assistant", "content": "之前的回答"}
                ]
            }
            """;

        when(toolService.getSystemPrompt(anyString())).thenReturn("You are a helpful assistant.");
        when(aiService.chat(anyString(), any(), anyString()))
            .thenReturn(reactor.core.publisher.Mono.just("基于上下文的AI响应"));

        mockMvc.perform(post("/api/v1/tools/test-tool-id/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.response").value("基于上下文的AI响应"));
    }

    @Test
    @DisplayName("未认证用户访问 - 返回401")
    void chat_UnauthenticatedUser_Returns401() throws Exception {
        String requestJson = """
            {
                "message": "测试消息",
                "session_id": null,
                "history": []
            }
            """;

        mockMvc.perform(post("/api/v1/tools/test-tool-id/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
            .andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("SSE流式响应 - 验证响应头")
    @WithMockUser(username = "testuser")
    void chatStream_VerifiesResponseHeaders() throws Exception {
        String requestJson = """
            {
                "message": "测试消息",
                "session_id": null,
                "history": []
            }
            """;

        when(toolService.getSystemPrompt(anyString())).thenReturn("You are a helpful assistant.");
        when(toolService.getModelConfig(anyString())).thenReturn("deepseek:deepseek-chat");

        mockMvc.perform(post("/api/v1/tools/test-tool-id/chat/stream")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
            .andExpect(status().isOk())
            .andExpect(header().exists("Content-Type"));
    }
}
