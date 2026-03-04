package com.platform.interfaces.rest.dto;

import com.platform.domain.artifact.Artifact;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 聊天响应DTO
 *
 * 对应Python: backend/src/models.py中的ChatResponse
 *
 * @author AI Teacher Platform
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ChatResponse {

    /**
     * AI回复内容
     * 对应Python: reply: str
     */
    private String reply;

    /**
     * 解析出的成果物列表
     * 对应Python: artifacts: List[Artifact]
     */
    private List<Artifact> artifacts;

    /**
     * 会话ID
     * 对应Python: session_id: str
     */
    private String sessionId;
}
