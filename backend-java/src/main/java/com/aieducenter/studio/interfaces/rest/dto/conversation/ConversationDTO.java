package com.platform.interfaces.rest.dto.conversation;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 会话DTO
 *
 * 对应Python: ConversationItem
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ConversationDTO {
    private String sessionId;
    private String title;
    private LocalDateTime updatedAt;
}
