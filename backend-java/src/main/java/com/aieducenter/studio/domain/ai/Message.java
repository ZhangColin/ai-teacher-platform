package com.platform.domain.ai;

import com.platform.domain.artifact.Artifact;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * 消息实体
 *
 * 对应Python: backend/src/domain/entities/message.py
 * 表示对话中的一条消息
 *
 * @author AI Teacher Platform
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Message {

    /**
     * 消息唯一标识（UUID字符串）
     * 对应Python: id: str
     */
    private String id;

    /**
     * 所属会话ID
     * 对应Python: session_id: str
     */
    private String sessionId;

    /**
     * 消息角色
     * 对应Python: role: MessageRole
     */
    private MessageRole role;

    /**
     * 消息内容
     * 对应Python: content: str
     */
    private String content;

    /**
     * 可选的成果物（AI生成的内容）
     * 对应Python: artifact: Optional[Artifact]
     */
    private Artifact artifact;

    /**
     * 创建时间
     * 对应Python: created_at: datetime
     */
    private LocalDateTime createdAt;

    /**
     * 检查消息是否来自用户
     * 对应Python: is_from_user() -> bool
     *
     * @return true-用户消息，false-其他
     */
    public boolean isFromUser() {
        return role.isUserMessage();
    }

    /**
     * 检查消息是否来自助手
     * 对应Python: is_from_assistant() -> bool
     *
     * @return true-助手消息，false-其他
     */
    public boolean isFromAssistant() {
        return role.isAssistantMessage();
    }

    /**
     * 检查是否为系统提示词
     * 对应Python: is_system_prompt() -> bool
     *
     * @return true-系统消息，false-其他
     */
    public boolean isSystemPrompt() {
        return role.isSystemMessage();
    }

    /**
     * 检查是否包含成果物
     * 对应Python: has_artifact() -> bool
     *
     * @return true-包含成果物，false-不包含
     */
    public boolean hasArtifact() {
        return artifact != null;
    }

    /**
     * 获取消息内容长度
     * 对应Python: get_content_length() -> int
     *
     * @return 内容长度
     */
    public int getContentLength() {
        return content != null ? content.length() : 0;
    }

    /**
     * 创建用户消息（工厂方法）
     * 对应Python: @classmethod create_user_message(cls, session_id, content) -> Message
     *
     * @param sessionId 会话ID
     * @param content 消息内容
     * @return 用户消息实例
     */
    public static Message createUserMessage(String sessionId, String content) {
        Message message = new Message();
        message.id = "0"; // 数据库生成
        message.sessionId = sessionId;
        message.role = MessageRole.USER;
        message.content = content;
        message.artifact = null;
        message.createdAt = LocalDateTime.now();
        return message;
    }

    /**
     * 创建助手消息（工厂方法）
     * 对应Python: @classmethod create_assistant_message(cls, session_id, content, artifact) -> Message
     *
     * @param sessionId 会话ID
     * @param content 消息内容
     * @param artifact 可选的成果物
     * @return 助手消息实例
     */
    public static Message createAssistantMessage(String sessionId, String content, Artifact artifact) {
        Message message = new Message();
        message.id = "0"; // 数据库生成
        message.sessionId = sessionId;
        message.role = MessageRole.ASSISTANT;
        message.content = content;
        message.artifact = artifact;
        message.createdAt = LocalDateTime.now();
        return message;
    }

    /**
     * 生成消息ID（UUID）
     *
     * @return UUID字符串
     */
    public static String generateMessageId() {
        return UUID.randomUUID().toString();
    }
}
