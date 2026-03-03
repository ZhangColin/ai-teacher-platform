package com.platform.infrastructure.security;

import io.jsonwebtoken.JwtException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * JWTProvider测试
 *
 * 对应Python: backend/tests/test_auth_service.py
 *
 * @author AI Teacher Platform
 */
@DisplayName("JWTProvider测试")
class JWTProviderTest {

    private JWTProvider jwtProvider;
    private static final String TEST_SECRET_KEY = "test-secret-key-must-be-at-least-32-characters-long-for-security";

    @BeforeEach
    void setUp() {
        jwtProvider = new JWTProvider(
            TEST_SECRET_KEY,
            Duration.ofHours(24).toMillis(),
            Duration.ofDays(7).toMillis()
        );
    }

    @Test
    @DisplayName("生成短期Token - 成功")
    void generateShortLivedToken_Success() {
        // When
        String token = jwtProvider.generateShortLivedToken("user-123");

        // Then
        assertThat(token).isNotEmpty();
        assertThat(token).isNotBlank();
        assertThat(token.split("\\.")).hasSize(3); // JWT格式: header.payload.signature
    }

    @Test
    @DisplayName("生成长期Token - 成功")
    void generateLongLivedToken_Success() {
        // When
        String token = jwtProvider.generateLongLivedToken("user-456");

        // Then
        assertThat(token).isNotEmpty();
        assertThat(token).isNotBlank();
    }

    @Test
    @DisplayName("验证Token - 有效token返回用户ID")
    void validateToken_ValidToken_ReturnsUserId() {
        // Given
        String userId = "user-789";
        String token = jwtProvider.generateShortLivedToken(userId);

        // When
        String extractedUserId = jwtProvider.validateToken(token);

        // Then
        assertThat(extractedUserId).isEqualTo(userId);
    }

    @Test
    @DisplayName("验证Token - 无效token返回null")
    void validateToken_InvalidToken_ReturnsNull() {
        // Given
        String invalidToken = "invalid.token.here";

        // When
        String extractedUserId = jwtProvider.validateToken(invalidToken);

        // Then
        assertThat(extractedUserId).isNull();
    }

    @Test
    @DisplayName("验证Token并获取用户ID - 有效token返回用户ID")
    void validateTokenAndGetUserId_ValidToken_ReturnsUserId() {
        // Given
        String userId = "user-101";
        String token = jwtProvider.generateShortLivedToken(userId);

        // When
        String extractedUserId = jwtProvider.validateTokenAndGetUserId(token);

        // Then
        assertThat(extractedUserId).isEqualTo(userId);
    }

    @Test
    @DisplayName("验证Token并获取用户ID - 无效token抛出异常")
    void validateTokenAndGetUserId_InvalidToken_ThrowsException() {
        // Given
        String invalidToken = "invalid.token.here";

        // When & Then
        assertThatThrownBy(() -> jwtProvider.validateTokenAndGetUserId(invalidToken))
            .isInstanceOf(JwtException.class);
    }

    @Test
    @DisplayName("从Token中提取用户ID - 有效token返回用户ID")
    void getUserIdFromToken_ValidToken_ReturnsUserId() {
        // Given
        String userId = "user-202";
        String token = jwtProvider.generateShortLivedToken(userId);

        // When
        String extractedUserId = jwtProvider.getUserIdFromToken(token);

        // Then
        assertThat(extractedUserId).isEqualTo(userId);
    }

    @Test
    @DisplayName("从Token中提取用户ID - 无效token返回null")
    void getUserIdFromToken_InvalidToken_ReturnsNull() {
        // Given
        String invalidToken = "not-a-valid-jwt";

        // When
        String extractedUserId = jwtProvider.getUserIdFromToken(invalidToken);

        // Then
        assertThat(extractedUserId).isNull();
    }

    @Test
    @DisplayName("构造函数 - 密钥太短抛出异常")
    void constructor_ShortKey_ThrowsException() {
        // When & Then
        assertThatThrownBy(() -> new JWTProvider(
            "short",
            Duration.ofHours(24).toMillis(),
            Duration.ofDays(7).toMillis()
        ))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("至少32字符");
    }

    @Test
    @DisplayName("构造函数 - null密钥抛出异常")
    void constructor_NullKey_ThrowsException() {
        // When & Then
        assertThatThrownBy(() -> new JWTProvider(
            null,
            Duration.ofHours(24).toMillis(),
            Duration.ofDays(7).toMillis()
        ))
            .isInstanceOf(IllegalArgumentException.class);
    }
}
