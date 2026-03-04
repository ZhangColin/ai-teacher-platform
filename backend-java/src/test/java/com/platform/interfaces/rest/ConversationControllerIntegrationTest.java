package com.platform.interfaces.rest;

import com.platform.application.service.SessionService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * ConversationController集成测试
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
@DisplayName("ConversationController集成测试")
class ConversationControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("获取会话列表 - 成功")
    @WithMockUser(username = "testuser")
    void getConversations_Success() throws Exception {
        mockMvc.perform(get("/api/v1/tools/test-tool-id/conversations"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.conversations").isArray());
    }

    @Test
    @DisplayName("删除会话 - 成功")
    @WithMockUser(username = "testuser")
    void deleteConversation_Success() throws Exception {
        mockMvc.perform(delete("/api/v1/tools/test-tool-id/conversations/test-conv-id"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").value("Conversation deleted successfully"));
    }

    @Test
    @DisplayName("获取会话详情 - 成功")
    @WithMockUser(username = "testuser")
    void getConversation_Success() throws Exception {
        mockMvc.perform(get("/api/v1/tools/test-tool-id/conversations/test-conv-id"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.conversation").exists())
            .andExpect(jsonPath("$.messages").isArray());
    }

    @Test
    @DisplayName("访问其他用户的会话 - 返回403")
    @WithMockUser(username = "otheruser")
    void getConversation_AccessDenied_Returns403() throws Exception {
        mockMvc.perform(get("/api/v1/tools/test-tool-id/conversations/test-conv-id"))
            .andExpect(status().is4xxClientError());
    }
}
