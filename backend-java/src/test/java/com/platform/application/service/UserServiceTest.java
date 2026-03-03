package com.platform.application.service;

import com.platform.infrastructure.persistence.jpa.UserEntity;
import com.platform.infrastructure.persistence.jpa.UserJpaRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

/**
 * UserService单元测试
 *
 * 对应Python: backend/tests/unit/test_user_service.py
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("UserService单元测试")
class UserServiceTest {

    @Mock
    private UserJpaRepository userJpaRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @InjectMocks
    private UserService userService;

    private UserEntity testUser;

    @BeforeEach
    void setUp() {
        testUser = new UserEntity();
        testUser.setUserId("test-user-123");
        testUser.setUsername("testuser");
        testUser.setPasswordHash("hashed_password");
        testUser.setIsAdmin(false);
    }

    @Test
    @DisplayName("创建用户 - 成功")
    void createUser_Success() {
        // Given
        when(userJpaRepository.existsByUsername(anyString())).thenReturn(false);
        when(userJpaRepository.existsByEmail(anyString())).thenReturn(false);
        when(userJpaRepository.existsByPhone(anyString())).thenReturn(false);
        when(passwordEncoder.encode(anyString())).thenReturn("encoded_password");
        when(userJpaRepository.save(any(UserEntity.class))).thenAnswer(invocation -> {
            UserEntity entity = invocation.getArgument(0);
            return entity;
        });

        // When
        var user = userService.createUser(
            "testuser",
            "password123",
            "Test User",
            "test@example.com",
            "13800138000",
            null,
            false
        );

        // Then
        assertNotNull(user);
        assertEquals("testuser", user.getUsername());
        verify(userJpaRepository).save(any(UserEntity.class));
    }

    @Test
    @DisplayName("创建用户 - 失败（用户名已存在）")
    void createUser_UsernameExists() {
        // Given
        when(userJpaRepository.existsByUsername("testuser")).thenReturn(true);

        // When & Then
        assertThrows(IllegalArgumentException.class, () -> {
            userService.createUser(
                "testuser",
                "password123",
                null,
                null,
                null,
                null,
                false
            );
        });
    }

    @Test
    @DisplayName("根据用户名获取用户 - 成功")
    void getUserByUsername_Success() {
        // Given
        when(userJpaRepository.findByUsername("testuser")).thenReturn(Optional.of(testUser));

        // When
        var user = userService.getUserByUsername("testuser");

        // Then
        assertNotNull(user);
        assertEquals("testuser", user.getUsername());
    }

    @Test
    @DisplayName("验证密码 - 正确")
    void verifyPassword_Correct() {
        // Given
        when(userJpaRepository.findById("test-user-123")).thenReturn(Optional.of(testUser));
        when(passwordEncoder.matches("password123", "hashed_password")).thenReturn(true);

        // When
        boolean result = userService.verifyPassword("test-user-123", "password123");

        // Then
        assertTrue(result);
    }

    @Test
    @DisplayName("验证密码 - 错误")
    void verifyPassword_Incorrect() {
        // Given
        when(userJpaRepository.findById("test-user-123")).thenReturn(Optional.of(testUser));
        when(passwordEncoder.matches("wrongpass", "hashed_password")).thenReturn(false);

        // When
        boolean result = userService.verifyPassword("test-user-123", "wrongpass");

        // Then
        assertFalse(result);
    }
}
