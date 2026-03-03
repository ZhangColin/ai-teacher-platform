package com.platform.application.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

/**
 * 标题生成器（占位符）
 *
 * 对应Python: backend/src/services/title_generator.py
 * TODO: 完整实现
 *
 * @author AI Teacher Platform
 */
@Service
public class TitleGenerator {

    private static final Logger logger = LoggerFactory.getLogger(TitleGenerator.class);

    /**
     * 生成会话标题
     *
     * @param userMessage 用户消息
     * @param assistantMessage AI回复
     * @return 生成的标题
     */
    public Mono<String> generateTitle(String userMessage, String assistantMessage) {
        logger.info("生成会话标题 - 用户消息: {}", userMessage.substring(0, Math.min(50, userMessage.length())));

        // TODO: 使用AI生成标题
        return Mono.just(fallbackTitle(userMessage));
    }

    /**
     * 降级标题生成（简单截取）
     *
     * @param userMessage 用户消息
     * @return 截取的标题
     */
    public String fallbackTitle(String userMessage) {
        // 截取前20个字符作为标题
        int maxLength = 20;
        if (userMessage.length() <= maxLength) {
            return userMessage;
        }
        return userMessage.substring(0, maxLength) + "...";
    }
}
