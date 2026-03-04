package com.platform.interfaces.rest.dto.conversation;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 会话详情响应
 *
 * 对应Python: get_conversation的返回值
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ConversationDetailResponse {
    private ConversationDetail conversation;
    private List<MessageItem> messages;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ConversationDetail {
        private String sessionId;
        private String title;
        private String toolId;
        private LocalDateTime createdAt;
        private LocalDateTime updatedAt;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class MessageItem {
        private String role;
        private String content;
        private LocalDateTime createdAt;
    }
}
