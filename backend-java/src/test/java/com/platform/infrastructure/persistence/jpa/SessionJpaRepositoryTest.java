package com.platform.infrastructure.persistence.jpa;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.test.context.ActiveProfiles;

import java.time.LocalDateTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * SessionJpaRepository集成测试
 */
@DataJpaTest
@ActiveProfiles("test")
@DisplayName("SessionJpaRepository集成测试")
class SessionJpaRepositoryTest {

    @Autowired
    private SessionJpaRepository repository;

    @Autowired
    private TestEntityManager entityManager;

    private SessionEntity session1;
    private SessionEntity session2;
    private String userId;
    private String toolId;

    @BeforeEach
    void setUp() {
        userId = "user-123";
        toolId = "tool-456";

        LocalDateTime baseTime = LocalDateTime.of(2024, 1, 1, 12, 0);

        // 创建测试数据
        session1 = new SessionEntity();
        session1.setSessionId("session-1");
        session1.setUserId(userId);
        session1.setToolId(toolId);
        session1.setTitle("会话1");
        session1.setCreatedAt(baseTime);
        session1.setUpdatedAt(baseTime.plusHours(1));

        session2 = new SessionEntity();
        session2.setSessionId("session-2");
        session2.setUserId(userId);
        session2.setToolId(toolId);
        session2.setTitle("会话2");
        session2.setCreatedAt(baseTime);
        session2.setUpdatedAt(baseTime.plusHours(2)); // 更新时间更晚

        // 保存到数据库
        entityManager.persist(session1);
        entityManager.persist(session2);
        entityManager.flush();
    }

    @Test
    @DisplayName("根据用户ID和工具ID查询会话 - 按更新时间倒序")
    void findByUserIdAndToolIdOrderByUpdatedAtDesc_ReturnsOrderedSessions() {
        // When
        List<SessionEntity> result = repository.findByUserIdAndToolIdOrderByUpdatedAtDesc(userId, toolId);

        // Then
        assertThat(result).hasSize(2);
        assertThat(result.get(0).getSessionId()).isEqualTo("session-2"); // 更新时间更晚的排第一
        assertThat(result.get(1).getSessionId()).isEqualTo("session-1");
    }

    @Test
    @DisplayName("根据用户ID查询所有会话 - 按更新时间倒序")
    void findByUserIdOrderByUpdatedAtDesc_ReturnsAllUserSessions() {
        // Given - 创建另一个工具的会话
        SessionEntity session3 = new SessionEntity();
        session3.setSessionId("session-3");
        session3.setUserId(userId);
        session3.setToolId("another-tool");
        session3.setTitle("会话3");
        session3.setCreatedAt(LocalDateTime.now());
        session3.setUpdatedAt(LocalDateTime.now().plusHours(3));

        entityManager.persist(session3);
        entityManager.flush();

        // When
        List<SessionEntity> result = repository.findByUserIdOrderByUpdatedAtDesc(userId);

        // Then
        assertThat(result).hasSize(3);
        assertThat(result.get(0).getSessionId()).isEqualTo("session-3"); // 更新时间最晚
    }

    @Test
    @DisplayName("查询不存在的用户会话 - 返回空列表")
    void findByUserIdAndToolIdOrderByUpdatedAtDesc_NoSessions_ReturnsEmpty() {
        // When
        List<SessionEntity> result = repository.findByUserIdAndToolIdOrderByUpdatedAtDesc("nonexistent-user", toolId);

        // Then
        assertThat(result).isEmpty();
    }

    @Test
    @DisplayName("根据ID查询会话 - 使用继承的findById")
    void findById_ExistingSession_ReturnsSession() {
        // When
        var result = repository.findById("session-1");

        // Then
        assertThat(result).isPresent();
        assertThat(result.get().getSessionId()).isEqualTo("session-1");
        assertThat(result.get().getTitle()).isEqualTo("会话1");
    }

    @Test
    @DisplayName("根据ID查询会话 - 不存在返回空")
    void findById_NonexistentSession_ReturnsEmpty() {
        // When
        var result = repository.findById("nonexistent");

        // Then
        assertThat(result).isEmpty();
    }

    @Test
    @DisplayName("保存新会话 - 使用继承的save")
    void save_NewSession_PersistsSession() {
        // Given
        SessionEntity newSession = new SessionEntity();
        newSession.setSessionId("new-session");
        newSession.setUserId(userId);
        newSession.setToolId(toolId);
        newSession.setTitle("新会话");
        newSession.setCreatedAt(LocalDateTime.now());
        newSession.setUpdatedAt(LocalDateTime.now());

        // When
        SessionEntity saved = repository.save(newSession);

        // Then
        assertThat(saved.getSessionId()).isEqualTo("new-session");
        assertThat(repository.findById("new-session")).isPresent();
    }

    @Test
    @DisplayName("删除会话 - 使用继承的deleteById")
    void deleteById_ExistingSession_RemovesSession() {
        // When
        repository.deleteById("session-1");

        // Then
        assertThat(repository.findById("session-1")).isEmpty();
    }

    @Test
    @DisplayName("查询所有会话 - 使用继承的findAll")
    void findAll_ReturnsAllSessions() {
        // When
        List<SessionEntity> result = repository.findAll();

        // Then
        assertThat(result).hasSizeGreaterThanOrEqualTo(2);
    }

    @Test
    @DisplayName("统计会话数量 - 使用继承的count")
    void count_ReturnsSessionCount() {
        // When
        long count = repository.count();

        // Then
        assertThat(count).isGreaterThanOrEqualTo(2);
    }

    @Test
    @DisplayName("检查会话是否存在 - 使用继承的existsById")
    void existsById_ExistingSession_ReturnsTrue() {
        // When
        boolean exists = repository.existsById("session-1");

        // Then
        assertThat(exists).isTrue();
    }

    @Test
    @DisplayName("检查会话是否存在 - 不存在返回false")
    void existsById_NonexistentSession_ReturnsFalse() {
        // When
        boolean exists = repository.existsById("nonexistent");

        // Then
        assertThat(exists).isFalse();
    }

    @Test
    @DisplayName("更新会话 - 修改标题")
    void update_ExistingSession_ModifiesSession() {
        // Given
        session1.setTitle("更新后的标题");

        // When
        repository.save(session1);
        entityManager.flush();
        entityManager.clear();

        // Then
        var updated = repository.findById("session-1");
        assertThat(updated).isPresent();
        assertThat(updated.get().getTitle()).isEqualTo("更新后的标题");
    }
}
