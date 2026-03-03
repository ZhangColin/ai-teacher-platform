package com.platform.application.service;

import com.platform.infrastructure.ai.provider.ProviderFactory;
import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.output.Response;
import dev.langchain4j.data.message.AiMessage;
import dev.langchain4j.data.message.UserMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

/**
 * 标题生成器
 *
 * 对应Python: backend/src/services/title_generator.py
 *
 * @author AI Teacher Platform
 */
@Service
public class TitleGenerator {

    private static final Logger logger = LoggerFactory.getLogger(TitleGenerator.class);

    private final ChatLanguageModel chatModel;

    public TitleGenerator(ProviderFactory providerFactory) {
        // 使用ProviderFactory获取流式模型用于标题生成
        this.chatModel = null; // TODO: 需要非流式模型
    }

    /**
     * 生成会话标题
     *
     * 对应Python: async def generate_title(...)
     *
     * @param userMessage 用户消息
     * @param assistantMessage AI回复（可选）
     * @return 生成的标题
     */
    public Mono<String> generateTitle(String userMessage, String assistantMessage) {
        String userMsg = userMessage.strip();

        // 如果用户消息为空，直接返回默认标题
        if (userMsg.isEmpty()) {
            return Mono.just("新对话");
        }

        // TODO: 实现AI标题生成
        // 暂时使用降级方案
        return Mono.just(fallbackTitle(userMessage));
    }

    /**
     * 降级标题生成（简单截取）
     *
     * 对应Python: def _fallback_title(...)
     *
     * @param userMessage 用户消息
     * @return 截取的标题
     */
    public String fallbackTitle(String userMessage) {
        String msg = userMessage.strip();

        if (msg.isEmpty()) {
            return "新对话";
        }

        // 去除换行符
        msg = msg.replace("\n", " ").replace("\r", " ");

        // 截取前30个字符
        if (msg.length() > 30) {
            return msg.substring(0, 30);
        }
        return msg;
    }

    /**
     * 清理标题，移除标点符号
     *
     * 对应Python: def _clean_title(...)
     */
    private String cleanTitle(String title) {
        String punctuation = "\"'。，！？、：；\"\"'《》【】（）[]{}、，。！？；：";

        for (char c : punctuation.toCharArray()) {
            title = title.replace(c, ' ');
        }

        return title.trim().replaceAll("\\s+", " ");
    }
}
