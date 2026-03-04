package com.platform.application.service;

import com.platform.domain.ai.Message;
import com.platform.infrastructure.ai.langchain4j.LangChain4jConfig;
import dev.langchain4j.data.message.AiMessage;
import dev.langchain4j.data.message.ChatMessage;
import dev.langchain4j.data.message.SystemMessage;
import dev.langchain4j.data.message.UserMessage;
import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.openai.OpenAiStreamingChatModel;
import dev.langchain4j.model.output.Response;
import dev.langchain4j.model.StreamingResponseHandler;
import dev.langchain4j.service.TokenStream;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * AI服务
 *
 * 对应Python: backend/src/services/ai_service.py
 * 提供LLM对话功能，支持流式和非流式对话
 *
 * 功能：
 * - 流式对话（SSE实时响应）
 * - 非流式对话（完整响应）
 * - 自动继续生成（检测到未完成代码时）
 * - 欢迎消息生成
 *
 * @author AI Teacher Platform
 */
@Service
public class AIService {

    private static final Logger logger = LoggerFactory.getLogger(AIService.class);

    private final OpenAiStreamingChatModel streamingModel;
    private final ChatLanguageModel chatModel;

    /**
     * 构造函数，注入LangChain4j模型
     */
    public AIService(
            OpenAiStreamingChatModel streamingModel,
            ChatLanguageModel chatModel
    ) {
        this.streamingModel = streamingModel;
        this.chatModel = chatModel;
    }

    /**
     * 流式对话
     *
     * 对应Python: async def chat_stream(...)
     *
     * @param systemPrompt 系统提示词
     * @param history 历史消息
     * @param userMessage 用户消息
     * @return 流式响应
     */
    public Flux<String> chatStream(
            String systemPrompt,
            List<Message> history,
            String userMessage
    ) {
        return chatStream(systemPrompt, history, userMessage, 3);
    }

    /**
     * 流式对话（带最大继续次数）
     *
     * 对应Python: async def chat_stream(..., max_continue: int = 3)
     *
     * @param systemPrompt 系统提示词
     * @param history 历史消息
     * @param userMessage 用户消息
     * @param maxContinue 最大继续生成次数
     * @return 流式响应
     */
    public Flux<String> chatStream(
            String systemPrompt,
            List<Message> history,
            String userMessage,
            int maxContinue
    ) {
        logger.info(
            "流式对话请求 - 系统提示词长度: {}, 历史消息数: {}, 用户消息: {}...",
            systemPrompt.length(),
            history.size(),
            userMessage.length() > 50 ? userMessage.substring(0, 50) : userMessage
        );

        // 构建消息列表
        List<ChatMessage> messages = buildMessages(systemPrompt, history, userMessage);

        // 使用LangChain4j流式模型
        return Flux.create(sink -> {
            try {
                streamingModel.generate(messages.stream().toList(),
                    new StreamingResponseHandler<AiMessage>() {
                        @Override
                        public void onNext(String token) {
                            sink.next(token);
                        }

                        @Override
                        public void onComplete(Response<AiMessage> response) {
                            String result = response.content().text();
                            logger.info("流式输出完成，内容长度: {}", result.length());

                            // 检查是否需要继续生成
                            if (shouldAutoContinue(result, maxContinue)) {
                                // 自动继续生成逻辑
                                autoContinue(messages, result, maxContinue, sink);
                            } else {
                                sink.complete();
                            }
                        }

                        @Override
                        public void onError(Throwable error) {
                            sink.error(error);
                        }
                    }
                );
            } catch (Exception e) {
                logger.error("AI服务调用异常（流式对话）: {}", e.getMessage(), e);
                sink.error(e);
            }
        });
    }

    /**
     * 非流式对话
     *
     * 对应Python: async def chat(...)
     *
     * @param systemPrompt 系统提示词
     * @param history 历史消息
     * @param userMessage 用户消息
     * @return 完整响应
     */
    public Mono<String> chat(
            String systemPrompt,
            List<Message> history,
            String userMessage
    ) {
        return chat(systemPrompt, history, userMessage, 3);
    }

    /**
     * 非流式对话（带最大继续次数）
     *
     * 对应Python: async def chat(..., max_continue: int = 3)
     *
     * @param systemPrompt 系统提示词
     * @param history 历史消息
     * @param userMessage 用户消息
     * @param maxContinue 最大继续生成次数
     * @return 完整响应
     */
    public Mono<String> chat(
            String systemPrompt,
            List<Message> history,
            String userMessage,
            int maxContinue
    ) {
        logger.info(
            "对话请求 - 系统提示词长度: {}, 历史消息数: {}, 用户消息: {}...",
            systemPrompt.length(),
            history.size(),
            userMessage.length() > 50 ? userMessage.substring(0, 50) : userMessage
        );

        // 构建消息列表
        List<ChatMessage> messages = buildMessages(systemPrompt, history, userMessage);

        return Mono.fromCallable(() -> {
            Response<AiMessage> response = chatModel.generate(messages);
            String result = response.content().text();
            logger.info("AI返回的回复长度: {} 字符", result.length());

            // 检查是否需要继续生成
            if (shouldAutoContinue(result, maxContinue)) {
                return autoContinueSync(messages, result, maxContinue);
            }

            return result;
        })
        .onErrorMap(e -> {
            logger.error("AI服务调用异常（对话）: {}", e.getMessage(), e);
            return new RuntimeException("AI服务调用失败: " + e.getMessage(), e);
        });
    }

    /**
     * 生成欢迎消息
     *
     * 对应Python: async def generate_welcome_message(...)
     *
     * @param systemPrompt 系统提示词
     * @return 欢迎消息
     */
    public Mono<String> generateWelcomeMessage(String systemPrompt) {
        logger.info("生成欢迎消息 - 系统提示词长度: {} 字符", systemPrompt.length());

        List<ChatMessage> messages = List.of(
            new SystemMessage(systemPrompt),
            new UserMessage("请用一句话介绍你自己，并询问用户需要什么帮助。")
        );

        return Mono.fromCallable(() -> {
            Response<AiMessage> response = chatModel.generate(messages);
            String result = response.content().text();
            logger.info("AI返回的欢迎消息: {}...", result.length() > 100 ? result.substring(0, 100) : result);
            return result;
        })
        .onErrorReturn("你好！我是你的AI助手。请告诉我你需要什么帮助。");
    }

    /**
     * 构建消息列表
     *
     * @param systemPrompt 系统提示词
     * @param history 历史消息
     * @param userMessage 用户消息
     * @return LangChain4j消息列表
     */
    private List<ChatMessage> buildMessages(
            String systemPrompt,
            List<Message> history,
            String userMessage
    ) {
        List<ChatMessage> messages = new ArrayList<>();

        // 添加系统提示词
        messages.add(new SystemMessage(systemPrompt));

        // 添加历史消息
        for (Message msg : history) {
            messages.add(LangChain4jConfig.toChatMessage(msg));
        }

        // 添加当前用户消息
        messages.add(new UserMessage(userMessage));

        return messages;
    }

    /**
     * 检查是否需要自动继续生成
     *
     * 对应Python: AIService._should_auto_continue(...)
     *
     * @param content 当前内容
     * @param maxContinue 剩余继续次数
     * @return 是否需要继续
     */
    private boolean shouldAutoContinue(String content, int maxContinue) {
        if (maxContinue <= 0) {
            return false;
        }

        // 检查是否是HTML内容且未完成
        if (isHtmlContent(content) && !isHtmlComplete(content)) {
            logger.info("检测到未完成的HTML内容，需要继续生成");
            return true;
        }

        // 检查是否包含未闭合的代码块
        if (hasUnclosedCodeBlock(content)) {
            logger.info("检测到未闭合的代码块，需要继续生成");
            return true;
        }

        return false;
    }

    /**
     * 检查内容是否是HTML
     */
    private boolean isHtmlContent(String content) {
        return content.toLowerCase().contains("<html") ||
               content.toLowerCase().contains("<!doctype");
    }

    /**
     * 检查HTML是否完整
     *
     * 对应Python: AIService._find_html_end_position(...)
     */
    private boolean isHtmlComplete(String content) {
        Pattern pattern = Pattern.compile("</html>", Pattern.CASE_INSENSITIVE);
        Matcher matcher = pattern.matcher(content);
        return matcher.find();
    }

    /**
     * 检查是否有未闭合的代码块
     */
    private boolean hasUnclosedCodeBlock(String content) {
        // 检查 ``` 标记数量
        Pattern pattern = Pattern.compile("```");
        Matcher matcher = pattern.matcher(content);
        int count = 0;
        while (matcher.find()) {
            count++;
        }
        return count % 2 != 0; // 奇数个 ``` 表示有未闭合的代码块
    }

    /**
     * 自动继续生成（同步）
     *
     * @param messages 消息列表（会被修改）
     * @param currentResult 当前结果
     * @param maxContinue 剩余继续次数
     * @return 继续生成后的完整结果
     */
    private String autoContinueSync(
            List<ChatMessage> messages,
            String currentResult,
            int maxContinue
    ) {
        String accumulatedResult = currentResult;
        int continueCount = 0;

        while (continueCount < maxContinue && shouldAutoContinue(accumulatedResult, maxContinue - continueCount)) {
            // 添加助手消息到历史
            messages.add(new AiMessage(accumulatedResult));
            // 添加继续请求
            messages.add(new UserMessage("请继续完成上述内容"));

            try {
                Response<AiMessage> response = chatModel.generate(messages);
                String continueResult = response.content().text();
                accumulatedResult += continueResult;
                continueCount++;

                logger.info(
                    "第 {} 次继续完成，当前总长度: {} 字符（本次新增: {} 字符）",
                    continueCount,
                    accumulatedResult.length(),
                    continueResult.length()
                );

            } catch (Exception e) {
                logger.error("继续生成失败: {}", e.getMessage(), e);
                break;
            }
        }

        return accumulatedResult;
    }

    /**
     * 自动继续生成（异步/流式）
     *
     * @param messages 消息列表
     * @param currentResult 当前结果
     * @param maxContinue 剩余继续次数
     * @param sink Flux sink
     */
    private void autoContinue(
            List<ChatMessage> messages,
            String currentResult,
            int maxContinue,
            reactor.core.publisher.FluxSink<String> sink
    ) {
        // TODO: 实现流式自动继续逻辑
        // 这是一个简化版本，完整的实现需要递归调用chatStream
        logger.warn("流式自动继续功能待实现");
        sink.complete();
    }
}
