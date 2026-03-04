package com.aieducenter.studio.domain.ai;

import com.aieducenter.studio.domain.artifact.Artifact;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Message领域实体单元测试
 */
@DisplayName("Message领域实体单元测试")
class MessageTest {

    @Test
    @DisplayName("检查用户消息 - 返回true")
    void isFromUser_UserRole_ReturnsTrue() {
        // Given
        Message message = new Message();
        message.setRole(MessageRole.USER);

        // When
        boolean result = message.isFromUser();

        // Then
        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("检查助手消息 - 返回true")
    void isFromAssistant_AssistantRole_ReturnsTrue() {
        // Given
        Message message = new Message();
        message.setRole(MessageRole.ASSISTANT);

        // When
        boolean result = message.isFromAssistant();

        // Then
        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("检查系统消息 - 返回true")
    void isSystemPrompt_SystemRole_ReturnsTrue() {
        // Given
        Message message = new Message();
        message.setRole(MessageRole.SYSTEM);

        // When
        boolean result = message.isSystemPrompt();

        // Then
        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("检查是否包含成果物 - 有成果物返回true")
    void hasArtifact_WithArtifact_ReturnsTrue() {
        // Given
        Message message = new Message();
        Artifact artifact = new Artifact();
        message.setArtifact(artifact);

        // When
        boolean result = message.hasArtifact();

        // Then
        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("检查是否包含成果物 - 无成果物返回false")
    void hasArtifact_WithoutArtifact_ReturnsFalse() {
        // Given
        Message message = new Message();
        message.setArtifact(null);

        // When
        boolean result = message.hasArtifact();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("获取消息内容长度 - 有内容")
    void getContentLength_WithContent_ReturnsLength() {
        // Given
        Message message = new Message();
        message.setContent("测试消息内容");

        // When
        int length = message.getContentLength();

        // Then
        assertThat(length).isEqualTo(6);
    }

    @Test
    @DisplayName("获取消息内容长度 - 内容为null")
    void getContentLength_NullContent_ReturnsZero() {
        // Given
        Message message = new Message();
        message.setContent(null);

        // When
        int length = message.getContentLength();

        // Then
        assertThat(length).isEqualTo(0);
    }

    @Test
    @DisplayName("创建用户消息 - 工厂方法")
    void createUserMessage_FactoryMethod() {
        // When
        Message message = Message.createUserMessage("session-123", "用户输入的消息");

        // Then
        assertThat(message.getId()).isEqualTo("0"); // 数据库生成
        assertThat(message.getSessionId()).isEqualTo("session-123");
        assertThat(message.getRole()).isEqualTo(MessageRole.USER);
        assertThat(message.getContent()).isEqualTo("用户输入的消息");
        assertThat(message.getArtifact()).isNull();
        assertThat(message.getCreatedAt()).isNotNull();
        assertThat(message.getCreatedAt()).isBeforeOrEqualTo(LocalDateTime.now());
    }

    @Test
    @DisplayName("创建助手消息 - 工厂方法（无成果物）")
    void createAssistantMessage_FactoryMethod_NoArtifact() {
        // When
        Message message = Message.createAssistantMessage("session-123", "AI回复", null);

        // Then
        assertThat(message.getId()).isEqualTo("0");
        assertThat(message.getSessionId()).isEqualTo("session-123");
        assertThat(message.getRole()).isEqualTo(MessageRole.ASSISTANT);
        assertThat(message.getContent()).isEqualTo("AI回复");
        assertThat(message.getArtifact()).isNull();
        assertThat(message.getCreatedAt()).isNotNull();
    }

    @Test
    @DisplayName("创建助手消息 - 工厂方法（有成果物）")
    void createAssistantMessage_FactoryMethod_WithArtifact() {
        // Given
        Artifact artifact = new Artifact();
        artifact.setType("html");
        artifact.setContent("<html>...</html>");

        // When
        Message message = Message.createAssistantMessage("session-123", "AI回复", artifact);

        // Then
        assertThat(message.getRole()).isEqualTo(MessageRole.ASSISTANT);
        assertThat(message.getArtifact()).isNotNull();
        assertThat(message.getArtifact().getType()).isEqualTo("html");
    }

    @Test
    @DisplayName("生成消息ID - 返回非空UUID")
    void generateMessageId_ReturnsNonEmptyUUID() {
        // When
        String messageId = Message.generateMessageId();

        // Then
        assertThat(messageId).isNotNull();
        assertThat(messageId).isNotEmpty();
        assertThat(messageId).matches("^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$");
    }

    @Test
    @DisplayName("生成多个消息ID - 每个都不同")
    void generateMessageId_MultipleCalls_GeneratesUniqueIds() {
        // When
        String id1 = Message.generateMessageId();
        String id2 = Message.generateMessageId();
        String id3 = Message.generateMessageId();

        // Then
        assertThat(id1).isNotEqualTo(id2);
        assertThat(id2).isNotEqualTo(id3);
        assertThat(id1).isNotEqualTo(id3);
    }

    @Test
    @DisplayName("使用setter设置所有字段 - 工作正常")
    void setterPattern_Works() {
        // Given
        LocalDateTime now = LocalDateTime.now();
        Artifact artifact = new Artifact();

        // When
        Message message = new Message();
        message.setId("msg-123");
        message.setSessionId("session-456");
        message.setRole(MessageRole.USER);
        message.setContent("内容");
        message.setArtifact(artifact);
        message.setCreatedAt(now);

        // Then
        assertThat(message.getId()).isEqualTo("msg-123");
        assertThat(message.getSessionId()).isEqualTo("session-456");
        assertThat(message.getRole()).isEqualTo(MessageRole.USER);
        assertThat(message.getContent()).isEqualTo("内容");
        assertThat(message.getArtifact()).isEqualTo(artifact);
        assertThat(message.getCreatedAt()).isEqualTo(now);
    }

    @Test
    @DisplayName("用户消息 - isFromAssistant返回false")
    void isFromAssistant_UserMessage_ReturnsFalse() {
        // Given
        Message message = new Message();
        message.setRole(MessageRole.USER);

        // When
        boolean result = message.isFromAssistant();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("助手消息 - isFromUser返回false")
    void isFromUser_AssistantMessage_ReturnsFalse() {
        // Given
        Message message = new Message();
        message.setRole(MessageRole.ASSISTANT);

        // When
        boolean result = message.isFromUser();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("空内容 - getContentLength返回0")
    void getContentLength_EmptyContent_ReturnsZero() {
        // Given
        Message message = new Message();
        message.setContent("");

        // When
        int length = message.getContentLength();

        // Then
        assertThat(length).isEqualTo(0);
    }
}
