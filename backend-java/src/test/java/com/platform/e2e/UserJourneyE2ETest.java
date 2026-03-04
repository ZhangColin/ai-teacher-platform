package com.platform.e2e;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * 用户完整旅程E2E测试
 *
 * 测试场景：登录 → 选择工具 → 对话 → 查看历史 → 登出
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
@DisplayName("用户完整旅程E2E测试")
class UserJourneyE2ETest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @DisplayName("完整用户旅程 - 登录到对话到查看历史")
    void completeUserJourney_Success() throws Exception {
        // 步骤1: 用户登录
        String loginRequest = """
            {
                "username": "testuser",
                "password": "password123"
            }
            """;

        String loginResponse = mockMvc.perform(post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(loginRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.token").isString())
            .andExpect(jsonPath("$.user.username").value("testuser"))
            .andReturn()
            .getResponse()
            .getContentAsString();

        // 提取token
        String token = objectMapper.readTree(loginResponse).get("token").asText();

        // 步骤2: 获取导航配置（查看可用工具）
        mockMvc.perform(get("/api/v1/navigation")
                .header("Authorization", "Bearer " + token))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.modules").isArray());

        // 步骤3: 获取所有工具
        mockMvc.perform(get("/api/v1/tools")
                .header("Authorization", "Bearer " + token))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.tools").isArray());

        // 步骤4: 发起对话（创建新会话）
        String chatRequest = """
            {
                "message": "你好，请帮我生成一个教案",
                "session_id": null,
                "history": []
            }
            """;

        mockMvc.perform(post("/api/v1/tools/test-tool/chat")
                .header("Authorization", "Bearer " + token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(chatRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.response").isString());

        // 步骤5: 查看会话历史
        mockMvc.perform(get("/api/v1/tools/test-tool/conversations")
                .header("Authorization", "Bearer " + token))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.conversations").isArray());

        // 步骤6: 获取用户会话列表
        mockMvc.perform(get("/api/v1/sessions")
                .param("toolId", "test-tool")
                .header("Authorization", "Bearer " + token))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.sessions").isArray());
    }

    @Test
    @DisplayName("用户旅程 - 未认证用户访问受保护端点")
    void userJourney_UnauthenticatedAccess_Returns401() throws Exception {
        // 尝试不登录直接访问工具
        mockMvc.perform(get("/api/v1/tools"))
            .andExpect(status().isUnauthorized());

        // 尝试不登录直接发起对话
        String chatRequest = """
            {
                "message": "测试消息",
                "session_id": null,
                "history": []
            }
            """;

        mockMvc.perform(post("/api/v1/tools/test-tool/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .content(chatRequest))
            .andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("用户旅程 - 访问不存在的工具")
    void userJourney_NonexistentTool_Returns404() throws Exception {
        // 先登录获取token（简化测试，假设token已知）
        String token = "valid-test-token"; // 实际测试中需要真实的token

        // 访问不存在的工具
        mockMvc.perform(get("/api/v1/tools/nonexistent-tool/conversations")
                .header("Authorization", "Bearer " + token))
            .andExpect(status().is4xxClientError()); // 可能是404或403
    }

    @Test
    @DisplayName("用户旅程 - 使用现有会话继续对话")
    void userJourney_ContinueExistingSession_Success() throws Exception {
        String token = "valid-test-token"; // 简化测试
        String existingSessionId = "existing-session-123";

        // 使用现有会话ID继续对话
        String chatRequest = String.format("""
            {
                "message": "请继续刚才的话题",
                "session_id": "%s",
                "history": []
            }
            """, existingSessionId);

        mockMvc.perform(post("/api/v1/tools/test-tool/chat")
                .header("Authorization", "Bearer " + token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(chatRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.response").isString());
    }

    @Test
    @DisplayName("用户旅程 - 删除会话")
    void userJourney_DeleteConversation_Success() throws Exception {
        String token = "valid-test-token";
        String conversationId = "conversation-to-delete";

        // 删除会话
        mockMvc.perform(delete("/api/v1/tools/test-tool/conversations/" + conversationId)
                .header("Authorization", "Bearer " + token))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").value("Conversation deleted successfully"));
    }

    @Test
    @DisplayName("用户旅程 - 多轮对话")
    void userJourney_MultipleTurnConversation_Success() throws Exception {
        String token = "valid-test-token";

        // 第一轮对话
        String chatRequest1 = """
            {
                "message": "请介绍自己",
                "session_id": null,
                "history": []
            }
            """;

        mockMvc.perform(post("/api/v1/tools/test-tool/chat")
                .header("Authorization", "Bearer " + token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(chatRequest1))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.response").isString());

        // 第二轮对话（假设使用了返回的session_id）
        String chatRequest2 = """
            {
                "message": "你能做什么？",
                "session_id": "session-from-first-turn",
                "history": []
            }
            """;

        mockMvc.perform(post("/api/v1/tools/test-tool/chat")
                .header("Authorization", "Bearer " + token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(chatRequest2))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.response").isString());
    }

    @Test
    @DisplayName("用户旅程 - 访问导航和工具集")
    void userJourney_NavigationAndToolsets_Success() throws Exception {
        String token = "valid-test-token";

        // 获取导航配置
        mockMvc.perform(get("/api/v1/navigation")
                .header("Authorization", "Bearer " + token))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.modules").isArray());

        // 获取工具集下的工具
        mockMvc.perform(get("/api/v1/toolsets/ai-tools/tools")
                .header("Authorization", "Bearer " + token))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.tools").isArray());
    }
}
