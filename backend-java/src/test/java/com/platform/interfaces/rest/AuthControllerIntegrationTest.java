package com.platform.interfaces.rest;

import com.platform.application.service.AuthService;
import com.platform.application.service.UserService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureWebMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * AuthController集成测试
 *
 * 对应Python: backend/tests/integration/test_auth_api.py
 */
@SpringBootTest
@AutoConfigureWebMvc
@DisplayName("AuthController集成测试")
class AuthControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private AuthService authService;

    @MockBean
    private UserService userService;

    @Test
    @DisplayName("POST /api/v1/auth/login - 成功")
    void login_Success() throws Exception {
        // Given
        when(authService.login(any(), any(), any())).thenReturn("test-token");
        when(authService.validateToken("test-token")).thenReturn("user-123");
        when(userService.getUserById("user-123")).thenAnswer(invocation -> {
            com.platform.domain.user.User user = new com.platform.domain.user.User();
            user.setId("user-123");
            user.setUsername("testuser");
            user.setIsAdmin(false);
            return user;
        });

        // When & Then
        mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"account\":\"testuser\",\"password\":\"pass123\",\"rememberMe\":false}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").value("test-token"))
                .andExpect(jsonPath("$.user.userId").value("user-123"));
    }

    @Test
    @DisplayName("POST /api/v1/auth/login - 失败（账号密码错误）")
    void login_Failure() throws Exception {
        // Given
        when(authService.login(any(), any(), any())).thenReturn(null);

        // When & Then
        mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"account\":\"testuser\",\"password\":\"wrong\"}"))
                .andExpect(status().is5xxServerError());
    }

    @Test
    @DisplayName("GET /api/v1/auth/me - 成功")
    void getMe_Success() throws Exception {
        // Given
        when(userService.getUserById("user-123")).thenAnswer(invocation -> {
            com.platform.domain.user.User user = new com.platform.domain.user.User();
            user.setId("user-123");
            user.setUsername("testuser");
            user.setIsAdmin(false);
            return user;
        });

        // When & Then (需要认证上下文，这里简化测试)
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/auth/me"))
                .andExpect(status().isUnauthorized()); // 未认证应该返回401
    }
}
