package com.platform.interfaces.rest.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 消息DTO
 *
 * 对应Python: Message
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Message {
    private String messageId;
    private String sessionId;
    private String role;  // "user", "assistant", "system"
    private String content;
    private LocalDateTime createdAt;
    private LocalDateTime timestamp;
    private List<Artifact> artifacts;
    private String mediaContent;  // 多模态内容（Base64或URL）
}
