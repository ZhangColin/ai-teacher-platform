package com.aieducenter.studio.interfaces.rest;

import com.aieducenter.studio.application.service.SessionService;
import com.aieducenter.studio.interfaces.rest.dto.UserInfo;
import com.aieducenter.studio.interfaces.rest.dto.conversation.ConversationDTO;
import com.aieducenter.studio.interfaces.rest.dto.conversation.ConversationDetailResponse;
import com.aieducenter.studio.interfaces.rest.dto.conversation.ConversationListResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 会话管理控制器
 *
 * 对应Python: backend/src/interfaces/routers/tools/conversations.py
 *
 * 端点列表：
 * - GET    /api/v1/tools/{tool_id}/conversations - 获取会话列表
 * - DELETE /api/v1/tools/{tool_id}/conversations/{conv_id} - 删除会话
 * - GET    /api/v1/tools/{tool_id}/conversations/{conv_id} - 获取会话详情
 *
 * @author AI Teacher Platform
 */
@RestController
@RequestMapping("/api/v1/tools")
public class ConversationController {

    private static final Logger logger = LoggerFactory.getLogger(ConversationController.class);

    private final SessionService sessionService;

    public ConversationController(SessionService sessionService) {
        this.sessionService = sessionService;
    }

    /**
     * 获取用户在指定工具下的会话列表
     * GET /api/v1/tools/{tool_id}/conversations
     */
    @GetMapping("/{tool_id}/conversations")
    public ResponseEntity<ConversationListResponse> getConversations(
            @PathVariable("tool_id") String toolId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            var sessions = sessionService.getSessionsByUserAndTool(
                currentUser.getUserId(),
                toolId
            );

            List<ConversationDTO> conversationItems = sessions.stream()
                .map(s -> ConversationDTO.builder()
                    .sessionId(s.getSessionId())
                    .title(s.getTitle())
                    .updatedAt(s.getUpdatedAt())
                    .build())
                .toList();

            return ResponseEntity.ok(ConversationListResponse.builder()
                .conversations(conversationItems)
                .build());
        } catch (Exception e) {
            logger.error("Get conversations error: {}", e.getMessage(), e);
            throw new RuntimeException("获取会话列表失败: " + e.getMessage());
        }
    }

    /**
     * 删除指定会话
     * DELETE /api/v1/tools/{tool_id}/conversations/{conv_id}
     */
    @DeleteMapping("/{tool_id}/conversations/{conv_id}")
    public ResponseEntity<Map<String, String>> deleteConversation(
            @PathVariable("tool_id") String toolId,
            @PathVariable("conv_id") String convId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            // 验证会话存在
            var session = sessionService.getSessionById(convId, currentUser.getUserId());
            if (session == null) {
                return ResponseEntity.notFound().build();
            }

            // 验证会话属于当前用户且属于指定工具
            if (!session.getUserId().equals(currentUser.getUserId())) {
                throw new IllegalArgumentException("Access denied");
            }

            if (!session.getToolId().equals(toolId)) {
                throw new IllegalArgumentException("Conversation does not belong to specified tool");
            }

            // 删除会话
            boolean success = sessionService.deleteSession(convId, currentUser.getUserId());

            if (!success) {
                throw new RuntimeException("Failed to delete conversation");
            }

            return ResponseEntity.ok(Map.of("message", "Conversation deleted successfully"));
        } catch (IllegalArgumentException e) {
            throw e;
        } catch (Exception e) {
            logger.error("Delete conversation error: {}", e.getMessage(), e);
            throw new RuntimeException("删除会话失败: " + e.getMessage());
        }
    }

    /**
     * 获取会话详情（包含消息历史）
     * GET /api/v1/tools/{tool_id}/conversations/{conv_id}
     */
    @GetMapping("/{tool_id}/conversations/{conv_id}")
    public ResponseEntity<ConversationDetailResponse> getConversation(
            @PathVariable("tool_id") String toolId,
            @PathVariable("conv_id") String convId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            // 获取会话
            var session = sessionService.getSessionById(convId, currentUser.getUserId());
            if (session == null) {
                return ResponseEntity.notFound().build();
            }

            // 验证权限
            if (!session.getUserId().equals(currentUser.getUserId())) {
                throw new IllegalArgumentException("Access denied");
            }

            if (!session.getToolId().equals(toolId)) {
                throw new IllegalArgumentException("Conversation does not belong to specified tool");
            }

            // 获取消息
            var messages = sessionService.getSessionMessages(convId);

            // 转换为API格式
            var messageItems = messages.stream()
                .map(msg -> ConversationDetailResponse.MessageItem.builder()
                    .role(msg.getRole().name())
                    .content(msg.getContent())
                    .createdAt(msg.getCreatedAt())
                    .build())
                .toList();

            return ResponseEntity.ok(ConversationDetailResponse.builder()
                .conversation(ConversationDetailResponse.ConversationDetail.builder()
                    .sessionId(session.getSessionId())
                    .title(session.getTitle())
                    .toolId(session.getToolId())
                    .createdAt(session.getCreatedAt())
                    .updatedAt(session.getUpdatedAt())
                    .build())
                .messages(messageItems)
                .build());
        } catch (IllegalArgumentException e) {
            throw e;
        } catch (Exception e) {
            logger.error("Get conversation error: {}", e.getMessage(), e);
            throw new RuntimeException("获取会话详情失败: " + e.getMessage());
        }
    }
}
