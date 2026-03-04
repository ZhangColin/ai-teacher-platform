package com.platform.domain.ai;

/**
 * 消息角色枚举
 *
 * 对应Python: backend/src/domain/value_objects/message_role.py
 * 表示对话中消息的角色（用户/助手/系统）
 *
 * @author AI Teacher Platform
 */
public enum MessageRole {

    /**
     * 用户消息
     * 对应Python: MessageRole.USER = "user"
     */
    USER("user"),

    /**
     * AI助手消息
     * 对应Python: MessageRole.ASSISTANT = "assistant"
     */
    ASSISTANT("assistant"),

    /**
     * 系统提示词消息
     * 对应Python: MessageRole.SYSTEM = "system"
     */
    SYSTEM("system");

    private final String value;

    MessageRole(String value) {
        this.value = value;
    }

    /**
     * 获取角色值
     *
     * @return 角色字符串
     */
    public String getValue() {
        return value;
    }

    /**
     * 检查是否为用户消息
     * 对应Python: is_user_message() -> bool
     *
     * @return true-用户消息，false-其他
     */
    public boolean isUserMessage() {
        return this == USER;
    }

    /**
     * 检查是否为助手消息
     * 对应Python: is_assistant_message() -> bool
     *
     * @return true-助手消息，false-其他
     */
    public boolean isAssistantMessage() {
        return this == ASSISTANT;
    }

    /**
     * 检查是否为系统消息
     * 对应Python: is_system_message() -> bool
     *
     * @return true-系统消息，false-其他
     */
    public boolean isSystemMessage() {
        return this == SYSTEM;
    }

    /**
     * 从字符串创建MessageRole
     *
     * @param value 角色字符串
     * @return MessageRole枚举
     */
    public static MessageRole fromValue(String value) {
        for (MessageRole role : values()) {
            if (role.value.equals(value)) {
                return role;
            }
        }
        // 默认返回用户角色
        return USER;
    }
}
