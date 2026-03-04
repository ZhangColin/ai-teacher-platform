package com.aieducenter.studio.domain.session;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Session领域实体单元测试
 */
@DisplayName("Session领域实体单元测试")
class SessionTest {

    @Test
    @DisplayName("Lombok @Data注解 - Getter和Setter工作正常")
    void lombokData_GettersAndSetters_Work() {
        // Given
        Session session = new Session();
        LocalDateTime now = LocalDateTime.now();

        // When
        session.setSessionId("session-123");
        session.setUserId("user-456");
        session.setToolId("tool-789");
        session.setTitle("测试会话");
        session.setCreatedAt(now);
        session.setUpdatedAt(now);

        // Then
        assertThat(session.getSessionId()).isEqualTo("session-123");
        assertThat(session.getUserId()).isEqualTo("user-456");
        assertThat(session.getToolId()).isEqualTo("tool-789");
        assertThat(session.getTitle()).isEqualTo("测试会话");
        assertThat(session.getCreatedAt()).isEqualTo(now);
        assertThat(session.getUpdatedAt()).isEqualTo(now);
    }

    @Test
    @DisplayName("创建Session - 所有字段可设置")
    void session_AllFieldsCanBeSet() {
        // Given
        Session session = new Session();
        LocalDateTime createdAt = LocalDateTime.of(2024, 1, 1, 10, 0);
        LocalDateTime updatedAt = LocalDateTime.of(2024, 1, 1, 11, 0);

        // When
        session.setSessionId("test-session-id");
        session.setUserId("test-user-id");
        session.setToolId("test-tool-id");
        session.setTitle("会话标题");
        session.setCreatedAt(createdAt);
        session.setUpdatedAt(updatedAt);

        // Then
        assertThat(session.getSessionId()).isEqualTo("test-session-id");
        assertThat(session.getUserId()).isEqualTo("test-user-id");
        assertThat(session.getToolId()).isEqualTo("test-tool-id");
        assertThat(session.getTitle()).isEqualTo("会话标题");
        assertThat(session.getCreatedAt()).isEqualTo(createdAt);
        assertThat(session.getUpdatedAt()).isEqualTo(updatedAt);
    }

    @Test
    @DisplayName("创建Session - 字段可为null")
    void session_FieldsCanBeNull() {
        // Given
        Session session = new Session();

        // When - 不设置任何字段

        // Then
        assertThat(session.getSessionId()).isNull();
        assertThat(session.getUserId()).isNull();
        assertThat(session.getToolId()).isNull();
        assertThat(session.getTitle()).isNull();
        assertThat(session.getCreatedAt()).isNull();
        assertThat(session.getUpdatedAt()).isNull();
    }

    @Test
    @DisplayName("创建Session - 标题可为空字符串")
    void session_TitleCanBeEmpty() {
        // Given
        Session session = new Session();

        // When
        session.setTitle("");

        // Then
        assertThat(session.getTitle()).isEqualTo("");
    }

    @Test
    @DisplayName("创建Session - 创建时间和更新时间可不同")
    void session_CreatedAndUpdatedTimes_CanBeDifferent() {
        // Given
        Session session = new Session();
        LocalDateTime createdAt = LocalDateTime.of(2024, 1, 1, 10, 0);
        LocalDateTime updatedAt = LocalDateTime.of(2024, 1, 1, 12, 0); // 2小时后

        // When
        session.setCreatedAt(createdAt);
        session.setUpdatedAt(updatedAt);

        // Then
        assertThat(session.getCreatedAt()).isNotEqualTo(session.getUpdatedAt());
        assertThat(session.getUpdatedAt()).isAfter(session.getCreatedAt());
    }

    @Test
    @DisplayName("Lombok toString - 包含所有字段")
    void lombokToString_ContainsAllFields() {
        // Given
        Session session = new Session();
        session.setSessionId("session-123");
        session.setUserId("user-456");
        session.setToolId("tool-789");
        session.setTitle("测试会话");

        // When
        String str = session.toString();

        // Then
        assertThat(str).contains("session-123");
        assertThat(str).contains("user-456");
        assertThat(str).contains("tool-789");
        assertThat(str).contains("测试会话");
    }

    @Test
    @DisplayName("Lombok equals - 相同字段的对象相等")
    void lombokEquals_SameFields_AreEqual() {
        // Given
        LocalDateTime now = LocalDateTime.now();

        Session session1 = new Session();
        session1.setSessionId("session-123");
        session1.setUserId("user-456");
        session1.setToolId("tool-789");
        session1.setTitle("测试会话");
        session1.setCreatedAt(now);
        session1.setUpdatedAt(now);

        Session session2 = new Session();
        session2.setSessionId("session-123");
        session2.setUserId("user-456");
        session2.setToolId("tool-789");
        session2.setTitle("测试会话");
        session2.setCreatedAt(now);
        session2.setUpdatedAt(now);

        // Then
        assertThat(session1).isEqualTo(session2);
        assertThat(session2).isEqualTo(session1);
    }

    @Test
    @DisplayName("Lombok hashCode - 相同字段的对象hashCode相同")
    void lombokHashCode_SameFields_SameHashCode() {
        // Given
        LocalDateTime now = LocalDateTime.now();

        Session session1 = new Session();
        session1.setSessionId("session-123");
        session1.setUserId("user-456");
        session1.setToolId("tool-789");
        session1.setTitle("测试会话");
        session1.setCreatedAt(now);
        session1.setUpdatedAt(now);

        Session session2 = new Session();
        session2.setSessionId("session-123");
        session2.setUserId("user-456");
        session2.setToolId("tool-789");
        session2.setTitle("测试会话");
        session2.setCreatedAt(now);
        session2.setUpdatedAt(now);

        // Then
        assertThat(session1.hashCode()).isEqualTo(session2.hashCode());
    }

    @Test
    @DisplayName("Session - 可设置长标题")
    void session_LongTitle_CanBeSet() {
        // Given
        Session session = new Session();
        String longTitle = "这是一个非常非常长的会话标题，包含很多文字，用来测试系统是否能够正确处理和存储长标题内容。";

        // When
        session.setTitle(longTitle);

        // Then
        assertThat(session.getTitle()).isEqualTo(longTitle);
    }

    @Test
    @DisplayName("Session - ID可为UUID格式")
    void session_IdCanBeUUIDFormat() {
        // Given
        Session session = new Session();
        String uuid = "550e8400-e29b-41d4-a716-446655440000";

        // When
        session.setSessionId(uuid);

        // Then
        assertThat(session.getSessionId()).isEqualTo(uuid);
    }
}
