package com.aieducenter.studio.infrastructure.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;

import static org.junit.jupiter.api.Assertions.*;

/**
 * JWTProvider单元测试
 *
 * 对应Python: backend/tests/unit/test_auth_service.py中的JWT相关测试
 */
@DisplayName("JWTProvider单元测试")
class JWTProviderTest {

    private JWTProvider jwtProvider;
    // 64字符 = 512位，满足HS512要求
    private static final String TEST_SECRET = "test-secret-key-for-jwt-hs512-must-be-at-least-64-characters-long-12345";
    private static final String TEST_USER_ID = "test-user-123";

    @BeforeEach
    void setUp() {
        jwtProvider = new JWTProvider(
            TEST_SECRET,
            Duration.ofHours(24).toMillis(),
            Duration.ofDays(7).toMillis()
        );
    }

    @Test
    @DisplayName("生成Token - 成功")
    void generateToken_Success() {
        String token = jwtProvider.generateToken(TEST_USER_ID, false);
        assertNotNull(token);
        assertTrue(token.startsWith("eyJ"));
    }

    @Test
    @DisplayName("验证Token - 成功")
    void validateToken_Success() {
        String token = jwtProvider.generateToken(TEST_USER_ID, false);
        String userId = jwtProvider.validateTokenAndGetUserId(token);
        assertEquals(TEST_USER_ID, userId);
    }

    @Test
    @DisplayName("验证Token - 失败（无效Token）")
    void validateToken_InvalidToken() {
        String invalidToken = "invalid.token.here";
        assertThrows(Exception.class, () -> {
            jwtProvider.validateTokenAndGetUserId(invalidToken);
        });
    }
}
