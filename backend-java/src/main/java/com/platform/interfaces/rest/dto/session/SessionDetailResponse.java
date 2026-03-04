package com.platform.interfaces.rest.dto.session;

import com.platform.interfaces.rest.dto.Message;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 会话详情响应
 *
 * 对应Python: SessionDetailResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SessionDetailResponse {
    private String sessionId;
    private String toolId;
    private String title;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private List<MessageItem> messages;

    /**
     * 消息项
     */
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
