package com.platform.infrastructure.persistence.jpa;

import com.platform.domain.ai.MessageRole;
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
 * MessageJpaRepository集成测试
 */
@DataJpaTest
@ActiveProfiles("test")
@DisplayName("MessageJpaRepository集成测试")
class MessageJpaRepositoryTest {

    @Autowired
    private MessageJpaRepository repository;

    @Autowired
    private TestEntityManager entityManager;

    private MessageEntity message1;
    private MessageEntity message2;
    private String sessionId;

    @BeforeEach
    void setUp() {
        sessionId = "session-123";

        LocalDateTime baseTime = LocalDateTime.of(2024, 1, 1, 12, 0);

        // 创建测试数据
        message1 = new MessageEntity();
        message1.setId("msg-1");
        message1.setSessionId(sessionId);
        message1.setRole(MessageRole.USER);
        message1.setContent("用户消息1");
        message1.setCreatedAt(baseTime);

        message2 = new MessageEntity();
        message2.setId("msg-2");
        message2.setSessionId(sessionId);
        message2.setRole(MessageRole.ASSISTANT);
        message2.setContent("助手回复1");
        message2.setCreatedAt(baseTime.plusMinutes(1));

        // 保存到数据库
        entityManager.persist(message1);
        entityManager.persist(message2);
        entityManager.flush();
    }

    @Test
    @DisplayName("根据会话ID查询消息 - 按创建时间正序")
    void findBySessionIdOrderByCreatedAtAsc_ReturnsOrderedMessages() {
        // When
        List<MessageEntity> result = repository.findBySessionIdOrderByCreatedAtAsc(sessionId);

        // Then
        assertThat(result).hasSize(2);
        assertThat(result.get(0).getId()).isEqualTo("msg-1"); // 创建时间更早的排第一
        assertThat(result.get(1).getId()).isEqualTo("msg-2");
    }

    @Test
    @DisplayName("根据会话ID和角色查询消息")
    void findBySessionIdAndRole_ReturnsFilteredMessages() {
        // When
        List<MessageEntity> result = repository.findBySessionIdAndRole(sessionId, MessageRole.USER);

        // Then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getId()).isEqualTo("msg-1");
        assertThat(result.get(0).getRole()).isEqualTo(MessageRole.USER);
    }

    @Test
    @DisplayName("根据会话ID查询助手消息")
    void findBySessionIdAndRole_AssistantMessages() {
        // When
        List<MessageEntity> result = repository.findBySessionIdAndRole(sessionId, MessageRole.ASSISTANT);

        // Then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getId()).isEqualTo("msg-2");
        assertThat(result.get(0).getRole()).isEqualTo(MessageRole.ASSISTANT);
    }

    @Test
    @DisplayName("查询不存在的会话消息 - 返回空列表")
    void findBySessionIdOrderByCreatedAtAsc_NoMessages_ReturnsEmpty() {
        // When
        List<MessageEntity> result = repository.findBySessionIdOrderByCreatedAtAsc("nonexistent-session");

        // Then
        assertThat(result).isEmpty();
    }

    @Test
    @DisplayName("根据ID查询消息 - 使用继承的findById")
    void findById_ExistingMessage_ReturnsMessage() {
        // When
        var result = repository.findById("msg-1");

        // Then
        assertThat(result).isPresent();
        assertThat(result.get().getId()).isEqualTo("msg-1");
        assertThat(result.get().getContent()).isEqualTo("用户消息1");
    }

    @Test
    @DisplayName("根据ID查询消息 - 不存在返回空")
    void findById_NonexistentMessage_ReturnsEmpty() {
        // When
        var result = repository.findById("nonexistent");

        // Then
        assertThat(result).isEmpty();
    }

    @Test
    @DisplayName("保存新消息 - 使用继承的save")
    void save_NewMessage_PersistsMessage() {
        // Given
        MessageEntity newMessage = new MessageEntity();
        newMessage.setId("new-msg");
        newMessage.setSessionId(sessionId);
        newMessage.setRole(MessageRole.USER);
        newMessage.setContent("新消息");
        newMessage.setCreatedAt(LocalDateTime.now());

        // When
        MessageEntity saved = repository.save(newMessage);

        // Then
        assertThat(saved.getId()).isEqualTo("new-msg");
        assertThat(repository.findById("new-msg")).isPresent();
    }

    @Test
    @DisplayName("保存系统消息")
    void save_SystemMessage_PersistsMessage() {
        // Given
        MessageEntity systemMessage = new MessageEntity();
        systemMessage.setId("system-msg");
        systemMessage.setSessionId(sessionId);
        systemMessage.setRole(MessageRole.SYSTEM);
        systemMessage.setContent("系统提示词");
        systemMessage.setCreatedAt(LocalDateTime.now());

        // When
        MessageEntity saved = repository.save(systemMessage);

        // Then
        assertThat(saved.getRole()).isEqualTo(MessageRole.SYSTEM);
        assertThat(repository.findById("system-msg")).isPresent();
    }

    @Test
    @DisplayName("删除消息 - 使用继承的deleteById")
    void deleteById_ExistingMessage_RemovesMessage() {
        // When
        repository.deleteById("msg-1");

        // Then
        assertThat(repository.findById("msg-1")).isEmpty();
    }

    @Test
    @DisplayName("查询所有消息 - 使用继承的findAll")
    void findAll_ReturnsAllMessages() {
        // When
        List<MessageEntity> result = repository.findAll();

        // Then
        assertThat(result).hasSizeGreaterThanOrEqualTo(2);
    }

    @Test
    @DisplayName("统计消息数量 - 使用继承的count")
    void count_ReturnsMessageCount() {
        // When
        long count = repository.count();

        // Then
        assertThat(count).isGreaterThanOrEqualTo(2);
    }

    @Test
    @DisplayName("检查消息是否存在 - 使用继承的existsById")
    void existsById_ExistingMessage_ReturnsTrue() {
        // When
        boolean exists = repository.existsById("msg-1");

        // Then
        assertThat(exists).isTrue();
    }

    @Test
    @DisplayName("检查消息是否存在 - 不存在返回false")
    void existsById_NonexistentMessage_ReturnsFalse() {
        // When
        boolean exists = repository.existsById("nonexistent");

        // Then
        assertThat(exists).isFalse();
    }

    @Test
    @DisplayName("更新消息 - 修改内容")
    void update_ExistingMessage_ModifiesMessage() {
        // Given
        message1.setContent("更新后的内容");

        // When
        repository.save(message1);
        entityManager.flush();
        entityManager.clear();

        // Then
        var updated = repository.findById("msg-1");
        assertThat(updated).isPresent();
        assertThat(updated.get().getContent()).isEqualTo("更新后的内容");
    }

    @Test
    @DisplayName("同一会话的多条消息 - 按时间正确排序")
    void findBySessionIdOrderByCreatedAtAsc_MultipleMessages_ReturnsInCorrectOrder() {
        // Given
        MessageEntity msg3 = new MessageEntity();
        msg3.setId("msg-3");
        msg3.setSessionId(sessionId);
        msg3.setRole(MessageRole.USER);
        msg3.setContent("用户消息2");
        msg3.setCreatedAt(LocalDateTime.of(2024, 1, 1, 12, 2));

        MessageEntity msg4 = new MessageEntity();
        msg4.setId("msg-4");
        msg4.setSessionId(sessionId);
        msg4.setRole(MessageRole.ASSISTANT);
        msg4.setContent("助手回复2");
        msg4.setCreatedAt(LocalDateTime.of(2024, 1, 1, 12, 3));

        entityManager.persist(msg3);
        entityManager.persist(msg4);
        entityManager.flush();

        // When
        List<MessageEntity> result = repository.findBySessionIdOrderByCreatedAtAsc(sessionId);

        // Then
        assertThat(result).hasSize(4);
        assertThat(result.get(0).getId()).isEqualTo("msg-1");
        assertThat(result.get(1).getId()).isEqualTo("msg-2");
        assertThat(result.get(2).getId()).isEqualTo("msg-3");
        assertThat(result.get(3).getId()).isEqualTo("msg-4");
    }

    @Test
    @DisplayName("查询空角色结果 - 返回空列表")
    void findBySessionIdAndRole_NoMatchingMessages_ReturnsEmpty() {
        // When
        List<MessageEntity> result = repository.findBySessionIdAndRole(sessionId, MessageRole.SYSTEM);

        // Then
        assertThat(result).isEmpty();
    }
}
