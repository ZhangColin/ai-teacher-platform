package com.aieducenter.studio.interfaces.rest;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * SessionController集成测试
 *
 * 对应Python: backend/tests/integration/test_sessions.py
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
@DisplayName("SessionController集成测试")
class SessionControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("获取会话详情 - 成功")
    @WithMockUser(username = "testuser")
    void getSessionDetail_Success() throws Exception {
        mockMvc.perform(get("/api/v1/sessions/test-session-id"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.sessionId").value("test-session-id"))
            .andExpect(jsonPath("$.messages").isArray());
    }

    @Test
    @DisplayName("更新会话标题 - 成功")
    @WithMockUser(username = "testuser")
    void updateSessionTitle_Success() throws Exception {
        String updateJson = """
            {
                "title": "更新后的标题"
            }
            """;

        mockMvc.perform(patch("/api/v1/sessions/test-session-id")
                .contentType("application/json")
                .content(updateJson))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.title").value("更新后的标题"));
    }

    @Test
    @DisplayName("删除会话 - 成功")
    @WithMockUser(username = "testuser")
    void deleteSession_Success() throws Exception {
        mockMvc.perform(delete("/api/v1/sessions/test-session-id"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").value("Session deleted successfully"));
    }

    @Test
    @DisplayName("获取代理的会话列表（已废弃）- 返回空列表")
    @WithMockUser(username = "testuser")
    void getAgentSessions_Deprecated_ReturnsEmpty() throws Exception {
        mockMvc.perform(get("/api/v1/agents/test-agent-id/sessions"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.sessions").isArray());
    }
}
