package com.platform.interfaces.rest;

import com.platform.application.service.SessionService;
import com.platform.domain.ai.Message;
import com.platform.interfaces.rest.dto.UserInfo;
import com.platform.interfaces.rest.dto.session.SessionDetailResponse;
import com.platform.interfaces.rest.dto.session.UpdateSessionRequest;
import com.platform.interfaces.rest.dto.session.UpdateSessionResponse;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 会话管理控制器
 *
 * 对应Python: backend/src/interfaces/routers/sessions/sessions.py
 *
 * 端点列表：
 * - GET    /api/v1/sessions/{session_id} - 获取会话详情
 * - PATCH  /api/v1/sessions/{session_id} - 更新会话标题
 * - DELETE /api/v1/sessions/{session_id} - 删除会话
 * - GET    /api/v1/agents/{agent_id}/sessions - 获取代理的所有会话（已废弃）
 *
 * @author AI Teacher Platform
 */
@RestController
@RequestMapping("/api/v1")
public class SessionController {

    private static final Logger logger = LoggerFactory.getLogger(SessionController.class);

    private final SessionService sessionService;

    public SessionController(SessionService sessionService) {
        this.sessionService = sessionService;
    }

    /**
     * 获取指定会话的完整消息历史
     * GET /api/v1/sessions/{session_id}
     */
    @GetMapping("/sessions/{session_id}")
    public ResponseEntity<SessionDetailResponse> getSessionDetail(
            @PathVariable("session_id") String sessionId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            // 获取会话（验证是否属于当前用户）
            var session = sessionService.getSessionById(sessionId, currentUser.getUserId());
            if (session == null) {
                return ResponseEntity.notFound().build();
            }

            // 获取消息列表
            List<Message> domainMessages = sessionService.getSessionMessages(sessionId);

            // 转换为 DTO
            var messages = domainMessages.stream()
                .map(msg -> SessionDetailResponse.MessageItem.builder()
                    .role(msg.getRole().name())
                    .content(msg.getContent())
                    .createdAt(msg.getCreatedAt())
                    .build())
                .toList();

            logger.info("获取会话消息 - 会话ID: {}, 消息数量: {}", sessionId, messages.size());

            return ResponseEntity.ok(SessionDetailResponse.builder()
                .sessionId(session.getSessionId())
                .toolId(session.getToolId())
                .title(session.getTitle())
                .createdAt(session.getCreatedAt())
                .updatedAt(session.getUpdatedAt())
                .messages(messages)
                .build());
        } catch (Exception e) {
            logger.error("获取会话详情失败: {}", e.getMessage(), e);
            throw new RuntimeException("获取会话详情失败: " + e.getMessage());
        }
    }

    /**
     * 更新指定会话的标题
     * PATCH /api/v1/sessions/{session_id}
     */
    @PatchMapping("/sessions/{session_id}")
    public ResponseEntity<UpdateSessionResponse> updateSessionTitle(
            @PathVariable("session_id") String sessionId,
            @Valid @RequestBody UpdateSessionRequest request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            var session = sessionService.updateTitle(sessionId, request.getTitle(), currentUser.getUserId());

            if (session == null) {
                return ResponseEntity.notFound().build();
            }

            return ResponseEntity.ok(UpdateSessionResponse.builder()
                .sessionId(session.getSessionId())
                .title(session.getTitle())
                .build());
        } catch (Exception e) {
            logger.error("更新会话标题失败: {}", e.getMessage(), e);
            throw new RuntimeException("更新会话标题失败: " + e.getMessage());
        }
    }

    /**
     * 删除指定会话（级联删除消息和成果物）
     * DELETE /api/v1/sessions/{session_id}
     */
    @DeleteMapping("/sessions/{session_id}")
    public ResponseEntity<Map<String, String>> deleteSession(
            @PathVariable("session_id") String sessionId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            boolean success = sessionService.deleteSession(sessionId, currentUser.getUserId());

            if (!success) {
                return ResponseEntity.notFound().build();
            }

            return ResponseEntity.ok(Map.of("message", "Session deleted successfully"));
        } catch (Exception e) {
            logger.error("删除会话失败: {}", e.getMessage(), e);
            throw new RuntimeException("删除会话失败: " + e.getMessage());
        }
    }

    /**
     * 获取指定代理的所有会话（已废弃，保留兼容性）
     * GET /api/v1/agents/{agent_id}/sessions
     */
    @GetMapping("/agents/{agent_id}/sessions")
    public ResponseEntity<Map<String, List<?>>> getAgentSessions(
            @PathVariable("agent_id") String agentId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        // 此接口已废弃，返回空列表
        logger.warn("调用了已废弃的端点: GET /api/v1/agents/{}/sessions", agentId);
        return ResponseEntity.ok(Map.of("sessions", List.of()));
    }
}
