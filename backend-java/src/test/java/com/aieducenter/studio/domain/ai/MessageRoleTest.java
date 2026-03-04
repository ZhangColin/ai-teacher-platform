package com.aieducenter.studio.domain.ai;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * MessageRole枚举单元测试
 */
@DisplayName("MessageRole枚举单元测试")
class MessageRoleTest {

    @Test
    @DisplayName("USER角色 - 值为user")
    void userRole_ValueIsUser() {
        // When
        String value = MessageRole.USER.getValue();

        // Then
        assertThat(value).isEqualTo("user");
    }

    @Test
    @DisplayName("ASSISTANT角色 - 值为assistant")
    void assistantRole_ValueIsAssistant() {
        // When
        String value = MessageRole.ASSISTANT.getValue();

        // Then
        assertThat(value).isEqualTo("assistant");
    }

    @Test
    @DisplayName("SYSTEM角色 - 值为system")
    void systemRole_ValueIsSystem() {
        // When
        String value = MessageRole.SYSTEM.getValue();

        // Then
        assertThat(value).isEqualTo("system");
    }

    @Test
    @DisplayName("USER - isUserMessage返回true")
    void userRole_IsUserMessage_ReturnsTrue() {
        // When
        boolean result = MessageRole.USER.isUserMessage();

        // Then
        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("USER - isAssistantMessage返回false")
    void userRole_IsAssistantMessage_ReturnsFalse() {
        // When
        boolean result = MessageRole.USER.isAssistantMessage();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("USER - isSystemMessage返回false")
    void userRole_IsSystemMessage_ReturnsFalse() {
        // When
        boolean result = MessageRole.USER.isSystemMessage();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("ASSISTANT - isUserMessage返回false")
    void assistantRole_IsUserMessage_ReturnsFalse() {
        // When
        boolean result = MessageRole.ASSISTANT.isUserMessage();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("ASSISTANT - isAssistantMessage返回true")
    void assistantRole_IsAssistantMessage_ReturnsTrue() {
        // When
        boolean result = MessageRole.ASSISTANT.isAssistantMessage();

        // Then
        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("ASSISTANT - isSystemMessage返回false")
    void assistantRole_IsSystemMessage_ReturnsFalse() {
        // When
        boolean result = MessageRole.ASSISTANT.isSystemMessage();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("SYSTEM - isUserMessage返回false")
    void systemRole_IsUserMessage_ReturnsFalse() {
        // When
        boolean result = MessageRole.SYSTEM.isUserMessage();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("SYSTEM - isAssistantMessage返回false")
    void systemRole_IsAssistantMessage_ReturnsFalse() {
        // When
        boolean result = MessageRole.SYSTEM.isAssistantMessage();

        // Then
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("SYSTEM - isSystemMessage返回true")
    void systemRole_IsSystemMessage_ReturnsTrue() {
        // When
        boolean result = MessageRole.SYSTEM.isSystemMessage();

        // Then
        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("fromValue - user字符串返回USER")
    void fromValue_UserString_ReturnsUSER() {
        // When
        MessageRole role = MessageRole.fromValue("user");

        // Then
        assertThat(role).isEqualTo(MessageRole.USER);
    }

    @Test
    @DisplayName("fromValue - assistant字符串返回ASSISTANT")
    void fromValue_AssistantString_ReturnsASSISTANT() {
        // When
        MessageRole role = MessageRole.fromValue("assistant");

        // Then
        assertThat(role).isEqualTo(MessageRole.ASSISTANT);
    }

    @Test
    @DisplayName("fromValue - system字符串返回SYSTEM")
    void fromValue_SystemString_ReturnsSYSTEM() {
        // When
        MessageRole role = MessageRole.fromValue("system");

        // Then
        assertThat(role).isEqualTo(MessageRole.SYSTEM);
    }

    @Test
    @DisplayName("fromValue - 无效字符串返回USER（默认）")
    void fromValue_InvalidString_ReturnsUSER() {
        // When
        MessageRole role = MessageRole.fromValue("invalid");

        // Then
        assertThat(role).isEqualTo(MessageRole.USER);
    }

    @Test
    @DisplayName("fromValue - 空字符串返回USER（默认）")
    void fromValue_EmptyString_ReturnsUSER() {
        // When
        MessageRole role = MessageRole.fromValue("");

        // Then
        assertThat(role).isEqualTo(MessageRole.USER);
    }

    @Test
    @DisplayName("fromValue - null字符串返回USER（默认）")
    void fromValue_NullString_ReturnsUSER() {
        // When
        MessageRole role = MessageRole.fromValue(null);

        // Then
        assertThat(role).isEqualTo(MessageRole.USER);
    }

    @Test
    @DisplayName("枚举值 - 大小写敏感")
    void fromValue_CaseSensitive() {
        // When
        MessageRole role1 = MessageRole.fromValue("user");
        MessageRole role2 = MessageRole.fromValue("USER");
        MessageRole role3 = MessageRole.fromValue("User");

        // Then
        assertThat(role1).isEqualTo(MessageRole.USER);
        assertThat(role2).isNotEqualTo(MessageRole.USER); // "USER"无效，返回默认USER
        assertThat(role3).isNotEqualTo(MessageRole.USER); // "User"无效，返回默认USER
    }

    @Test
    @DisplayName("枚举 - 包含3个值")
    void enum_ContainsThreeValues() {
        // When
        MessageRole[] values = MessageRole.values();

        // Then
        assertThat(values).hasSize(3);
        assertThat(values).containsExactly(MessageRole.USER, MessageRole.ASSISTANT, MessageRole.SYSTEM);
    }

    @Test
    @DisplayName("枚举valueOf - 正常工作")
    void enumValueOf_Works() {
        // When
        MessageRole user = MessageRole.valueOf("USER");
        MessageRole assistant = MessageRole.valueOf("ASSISTANT");
        MessageRole system = MessageRole.valueOf("SYSTEM");

        // Then
        assertThat(user).isEqualTo(MessageRole.USER);
        assertThat(assistant).isEqualTo(MessageRole.ASSISTANT);
        assertThat(system).isEqualTo(MessageRole.SYSTEM);
    }
}
