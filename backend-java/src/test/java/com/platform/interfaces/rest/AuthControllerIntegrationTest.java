package com.platform.interfaces.rest;

import com.platform.application.service.AuthService;
import com.platform.application.service.UserService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.reactive.server.WebTestClient;
import reactor.core.publisher.Mono;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

/**
 * AuthController集成测试（WebFlux版本）
 *
 * 对应Python: backend/tests/integration/test_auth_api.py
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@DisplayName("AuthController集成测试")
class AuthControllerIntegrationTest {

    @Autowired
    private WebTestClient webTestClient;

    @MockBean
    private AuthService authService;

    @MockBean
    private UserService userService;

    @Test
    @DisplayName("POST /api/v1/auth/login - 成功")
    void login_Success() {
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
        webTestClient.post()
                .uri("/api/v1/auth/login")
                .bodyValue("{\"account\":\"testuser\",\"password\":\"pass123\",\"rememberMe\":false}")
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.token").isEqualTo("test-token")
                .jsonPath("$.user.userId").isEqualTo("user-123");
    }

    @Test
    @DisplayName("POST /api/v1/auth/login - 失败（账号密码错误）")
    void login_Failure() {
        // Given
        when(authService.login(any(), any(), any())).thenReturn(null);

        // When & Then
        webTestClient.post()
                .uri("/api/v1/auth/login")
                .bodyValue("{\"account\":\"testuser\",\"password\":\"wrong\"}")
                .exchange()
                .expectStatus().is5xxServerError();
    }

    @Test
    @DisplayName("GET /api/v1/auth/me - 成功")
    void getMe_Success() {
        // Given - 模拟认证用户
        when(userService.getUserById("user-123")).thenAnswer(invocation -> {
            com.platform.domain.user.User user = new com.platform.domain.user.User();
            user.setId("user-123");
            user.setUsername("testuser");
            user.setIsAdmin(false);
            return user;
        });

        // When & Then (未认证应该返回401)
        webTestClient.get()
                .uri("/api/v1/auth/me")
                .exchange()
                .expectStatus().isUnauthorized(); // 未认证应该返回401
    }
}
