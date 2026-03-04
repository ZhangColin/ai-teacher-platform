package com.platform.application.service;

import com.platform.domain.session.Session;
import com.platform.infrastructure.persistence.jpa.MessageEntity;
import com.platform.infrastructure.persistence.jpa.MessageJpaRepository;
import com.platform.infrastructure.persistence.jpa.SessionEntity;
import com.platform.infrastructure.persistence.jpa.SessionJpaRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * SessionService单元测试
 *
 * 对应Python: backend/tests/unit/test_session_service.py
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("SessionService单元测试")
class SessionServiceTest {

    @Mock
    private SessionJpaRepository sessionJpaRepository;

    @Mock
    private MessageJpaRepository messageJpaRepository;

    @InjectMocks
    private SessionService sessionService;

    @BeforeEach
    void setUp() {
        // 测试数据
    }

    @Test
    @DisplayName("创建会话 - 成功")
    void createSession_Success() {
        // Given
        when(sessionJpaRepository.save(any(SessionEntity.class))).thenAnswer(invocation -> {
            SessionEntity entity = invocation.getArgument(0);
            return entity;
        });

        // When
        Session session = sessionService.createSession("user-123", "tool-456", "Test Session");

        // Then
        assertNotNull(session);
        assertEquals("user-123", session.getUserId());
        assertEquals("tool-456", session.getToolId());
        assertEquals("Test Session", session.getTitle());
        verify(sessionJpaRepository).save(any(SessionEntity.class));
    }

    @Test
    @DisplayName("获取会话 - 成功")
    void getSessionById_Success() {
        // Given
        SessionEntity entity = new SessionEntity();
        entity.setSessionId("session-123");
        entity.setUserId("user-123");
        entity.setToolId("tool-456");
        entity.setTitle("Test Session");
        entity.setCreatedAt(LocalDateTime.now());

        when(sessionJpaRepository.findById("session-123")).thenReturn(Optional.of(entity));

        // When
        Session session = sessionService.getSessionById("session-123", null);

        // Then
        assertNotNull(session);
        assertEquals("session-123", session.getSessionId());
    }

    @Test
    @DisplayName("获取会话 - 失败（不存在）")
    void getSessionById_NotFound() {
        // Given
        when(sessionJpaRepository.findById("invalid-id")).thenReturn(Optional.empty());

        // When
        Session session = sessionService.getSessionById("invalid-id", null);

        // Then
        assertNull(session);
    }

    @Test
    @DisplayName("删除会话 - 成功")
    void deleteSession_Success() {
        // Given
        SessionEntity entity = new SessionEntity();
        entity.setSessionId("session-123");
        entity.setUserId("user-123");

        when(sessionJpaRepository.findById("session-123")).thenReturn(Optional.of(entity));
        doNothing().when(sessionJpaRepository).delete(any());

        // When
        boolean result = sessionService.deleteSession("session-123", null);

        // Then
        assertTrue(result);
        verify(sessionJpaRepository).delete(any());
    }

    @Test
    @DisplayName("添加消息 - 成功")
    void addMessage_Success() {
        // Given
        SessionEntity entity = new SessionEntity();
        entity.setSessionId("session-123");
        entity.setUserId("user-123");

        when(sessionJpaRepository.findById("session-123")).thenReturn(Optional.of(entity));
        when(messageJpaRepository.save(any(MessageEntity.class))).thenAnswer(invocation -> {
            MessageEntity msg = invocation.getArgument(0);
            return msg;
        });

        // When
        var message = sessionService.addMessage("session-123", "user", "Hello", null);

        // Then
        assertNotNull(message);
        assertEquals("user", message.getRole().getValue());
        assertEquals("Hello", message.getContent());
    }
}
