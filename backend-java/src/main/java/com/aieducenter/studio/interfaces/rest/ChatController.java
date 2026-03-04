package com.platform.interfaces.rest;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.platform.application.service.AIService;
import com.platform.application.service.ArtifactParser;
import com.platform.application.service.SessionService;
import com.platform.application.service.TitleGenerator;
import com.platform.application.service.ToolService;
import com.platform.domain.ai.Message;
import com.platform.domain.ai.MessageRole;
import com.platform.domain.session.Session;
import com.platform.interfaces.rest.dto.ChatRequest;
import com.platform.interfaces.rest.dto.ChatResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 聊天控制器
 *
 * 对应Python: backend/src/interfaces/routers/tools/chat.py
 * 提供流式和非流式对话接口
 *
 * @author AI Teacher Platform
 */
@RestController
@RequestMapping("/api/v1/tools")
public class ChatController {

    private static final Logger logger = LoggerFactory.getLogger(ChatController.class);

    private final AIService aiService;
    private final SessionService sessionService;
    private final ToolService toolService;
    private final TitleGenerator titleGenerator;
    private final ArtifactParser artifactParser;
    private final ObjectMapper objectMapper;

    public ChatController(
            AIService aiService,
            SessionService sessionService,
            ToolService toolService,
            TitleGenerator titleGenerator,
            ArtifactParser artifactParser,
            ObjectMapper objectMapper
    ) {
        this.aiService = aiService;
        this.sessionService = sessionService;
        this.toolService = toolService;
        this.titleGenerator = titleGenerator;
        this.artifactParser = artifactParser;
        this.objectMapper = objectMapper;
    }

    /**
     * 流式对话接口
     *
     * 对应Python: @router.post("/tools/{tool_id}/chat/stream")
     * 使用Server-Sent Events (SSE)返回AI的流式响应
     *
     * @param toolId 工具ID
     * @param request 聊天请求
     * @return SSE流式响应
     */
    @PostMapping(value = "/{tool_id}/chat/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> chatStream(
            @PathVariable("tool_id") String toolId,
            @RequestBody ChatRequest request
    ) {
        String userId = getCurrentUserId();

        logger.info("流式对话请求 - toolId: {}, userId: {}, message: {}...",
            toolId, userId, request.getMessage().substring(0, Math.min(50, request.getMessage().length())));

        // 获取工具配置
        String systemPrompt = toolService.getSystemPrompt(toolId);
        String modelConfig = toolService.getModelConfig(toolId);

        // 处理会话
        String sessionId = request.getSessionId();
        Session session;

        if (sessionId == null || sessionId.isEmpty()) {
            // 创建新会话
            session = sessionService.createSession(
                userId,
                toolId,
                request.getMessage().substring(0, Math.min(50, request.getMessage().length()))
            );
            sessionId = session.getSessionId();
            logger.info("创建新会话: {}", sessionId);
        }

        // 准备消息历史
        List<Message> history;
        if (request.getHistory() != null && !request.getHistory().isEmpty()) {
            history = request.getHistory();
        } else {
            history = sessionService.getSessionMessages(sessionId);
        }

        // 保存用户消息
        sessionService.addMessage(sessionId, "user", request.getMessage(), userId);

        // 发送session_id事件
        Flux<String> sessionEvent = Flux.just(createSseEvent(Map.of(
            "type", "session_id",
            "session_id", sessionId
        )));

        // 获取AI流式响应
        Flux<String> contentStream = aiService.chatStream(systemPrompt, history, request.getMessage())
            .map(chunk -> createSseEvent(Map.of("content", chunk)))
            .doOnComplete(() -> {
                logger.info("流式输出完成");
            });

        // 发送结束标记
        Flux<String> doneEvent = Flux.just("data: [DONE]\n\n");

        // 检查是否需要生成标题
        Flux<String> titleEvent = checkAndGenerateTitle(sessionId, request.getMessage(), userId);

        // 组合所有事件
        return Flux.concat(sessionEvent, contentStream, doneEvent, titleEvent)
            .doOnError(e -> logger.error("Chat stream error: {}", e.getMessage(), e))
            .onErrorResume(e -> Flux.just(createSseEvent(Map.of("error", e.getMessage()))));
    }

    /**
     * 非流式对话接口
     *
     * 对应Python: @router.post("/tools/{tool_id}/chat")
     * 返回完整的AI响应
     *
     * @param toolId 工具ID
     * @param request 聊天请求
     * @return 聊天响应
     */
    @PostMapping("/{tool_id}/chat")
    public Mono<ChatResponse> chat(
            @PathVariable("tool_id") String toolId,
            @RequestBody ChatRequest request
    ) {
        String userId = getCurrentUserId();

        logger.info("非流式对话请求 - toolId: {}, userId: {}, message: {}...",
            toolId, userId, request.getMessage().substring(0, Math.min(50, request.getMessage().length())));

        // 获取工具配置
        String systemPrompt = toolService.getSystemPrompt(toolId);

        // 处理会话
        String sessionId = request.getSessionId();
        Session session;

        if (sessionId == null || sessionId.isEmpty()) {
            // 创建新会话
            session = sessionService.createSession(
                userId,
                toolId,
                request.getMessage().substring(0, Math.min(50, request.getMessage().length()))
            );
            sessionId = session.getSessionId();
        }

        // 创建最终引用供lambda使用
        final String finalSessionId = sessionId;
        final String finalUserId = userId;
        final String finalUserMessage = request.getMessage();

        // 准备消息历史
        List<Message> history;
        if (request.getHistory() != null && !request.getHistory().isEmpty()) {
            history = request.getHistory();
        } else {
            history = sessionService.getSessionMessages(sessionId);
        }

        // 保存用户消息
        sessionService.addMessage(sessionId, "user", request.getMessage(), userId);

        // 获取AI响应
        return aiService.chat(systemPrompt, history, request.getMessage())
            .flatMap(response -> {
                // 保存AI消息
                sessionService.addMessage(finalSessionId, "assistant", response, finalUserId);

                // 解析成果物
                var artifacts = artifactParser.parseFromMarkdown(response);

                // 检查是否需要生成标题
                int messageCount = sessionService.getMessageCount(finalSessionId, finalUserId);
                if (messageCount == 2) { // 第一轮对话
                    return generateTitleAndUpdate(finalUserMessage, response, finalSessionId, finalUserId)
                        .then(Mono.just(new ChatResponse(response, artifacts, finalSessionId)));
                }

                return Mono.just(new ChatResponse(response, artifacts, finalSessionId));
            })
            .doOnError(e -> logger.error("Chat endpoint error: {}", e.getMessage(), e));
    }

    /**
     * 检查并生成标题（流式）
     */
    private Flux<String> checkAndGenerateTitle(String sessionId, String userMessage, String userId) {
        int messageCount = sessionService.getMessageCount(sessionId, userId);

        if (messageCount == 2) { // 第一轮对话
            return Flux.defer(() -> {
                try {
                    // 生成标题（阻塞调用，实际应该异步）
                    String title = titleGenerator.fallbackTitle(userMessage);
                    // 更新会话标题
                    // sessionService.updateTitle(sessionId, title, userId); // TODO: 实现更新方法

                    return Flux.just(createSseEvent(Map.of(
                        "type", "title_generated",
                        "session_id", sessionId,
                        "title", title
                    )));
                } catch (Exception e) {
                    logger.error("生成标题失败: {}", e.getMessage(), e);
                    return Flux.empty();
                }
            });
        }

        return Flux.empty();
    }

    /**
     * 生成标题并更新会话
     */
    private Mono<Void> generateTitleAndUpdate(String userMessage, String assistantMessage, String sessionId, String userId) {
        return titleGenerator.generateTitle(userMessage, assistantMessage)
            .doOnNext(title -> {
                // TODO: sessionService.updateTitle(sessionId, title, userId);
                logger.info("会话标题已生成: {}", title);
            })
            .then();
    }

    /**
     * 获取当前用户ID
     */
    private String getCurrentUserId() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null && authentication.isAuthenticated()) {
            return authentication.getName();
        }
        // TODO: 应该抛出未授权异常
        return "anonymous";
    }

    /**
     * 创建SSE事件
     */
    private String createSseEvent(Map<String, Object> data) {
        try {
            String json = objectMapper.writeValueAsString(data);
            return "data: " + json + "\n\n";
        } catch (Exception e) {
            logger.error("JSON序列化失败: {}", e.getMessage(), e);
            return "data: {\"error\": \"Failed to serialize response\"}\n\n";
        }
    }
}
