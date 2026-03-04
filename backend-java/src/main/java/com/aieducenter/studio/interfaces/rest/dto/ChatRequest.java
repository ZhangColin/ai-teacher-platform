package com.aieducenter.studio.interfaces.rest.dto;

import com.aieducenter.studio.domain.ai.Message;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 聊天请求DTO
 *
 * 对应Python: backend/src/models.py中的ChatRequest
 *
 * @author AI Teacher Platform
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ChatRequest {

    /**
     * 用户消息
     * 对应Python: message: str
     */
    private String message;

    /**
     * 会话ID（可选，为空则创建新会话）
     * 对应Python: session_id: Optional[str]
     */
    private String sessionId;

    /**
     * 历史消息（可选，为空则从数据库读取）
     * 对应Python: history: Optional[List[Message]]
     */
    private List<Message> history;
}
