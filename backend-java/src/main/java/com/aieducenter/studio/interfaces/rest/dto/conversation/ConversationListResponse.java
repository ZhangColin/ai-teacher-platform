package com.aieducenter.studio.interfaces.rest.dto.conversation;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 会话列表响应
 *
 * 对应Python: ConversationListResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ConversationListResponse {
    private List<ConversationDTO> conversations;
}
