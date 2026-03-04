package com.platform.infrastructure.ai.langchain4j;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.openai.OpenAiChatModel;
import dev.langchain4j.model.openai.OpenAiStreamingChatModel;
import dev.langchain4j.data.message.AiMessage;
import dev.langchain4j.data.message.ChatMessage;
import dev.langchain4j.data.message.UserMessage;
import dev.langchain4j.model.openai.OpenAiImageModel;
import dev.langchain4j.model.image.ImageModel;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

import java.time.Duration;
import java.util.List;

/**
 * LangChain4j配置类
 *
 * 对应Python: backend/src/services/ai_service.py
 * 提供LLM模型的高级封装，支持：
 * - 流式/非流式对话
 * - 工具调用（Function Calling）
 * - 多模态支持（图像、音频）
 * - 记忆管理
 *
 * @author AI Teacher Platform
 */
@Configuration
public class LangChain4jConfig {

    private static final Logger logger = LoggerFactory.getLogger(LangChain4jConfig.class);

    /**
     * OpenAI流式聊天模型
     * 用于SSE实时响应
     *
     * @return OpenAiStreamingChatModel实例
     */
    @Bean
    @Primary
    public OpenAiStreamingChatModel openAiStreamingChatModel(
            @Value("${ai.provider.current:deepseek}") String provider,
            @Value("${ai.providers.openai.api-key:}") String openaiKey,
            @Value("${ai.providers.openai.base-url:https://api.openai.com/v1}") String openaiBaseUrl,
            @Value("${ai.providers.deepseek.api-key:}") String deepseekKey,
            @Value("${ai.providers.deepseek.base-url:https://api.deepseek.com/v1}") String deepseekBaseUrl,
            @Value("${ai.providers.kimi.api-key:}") String kimiKey,
            @Value("${ai.providers.kimi.base-url:https://api.moonshot.cn/v1}") String kimiBaseUrl
    ) {
        String apiKey;
        String baseUrl;
        String modelName;

        // 根据provider选择配置
        switch (provider.toLowerCase()) {
            case "openai":
                apiKey = openaiKey;
                baseUrl = openaiBaseUrl;
                modelName = "gpt-4";
                break;
            case "deepseek":
                apiKey = deepseekKey;
                baseUrl = deepseekBaseUrl;
                modelName = "deepseek-chat";
                break;
            case "kimi":
                apiKey = kimiKey;
                baseUrl = kimiBaseUrl;
                modelName = "moonshot-v1-128k";
                break;
            default:
                throw new IllegalArgumentException("Unknown provider: " + provider);
        }

        if (apiKey == null || apiKey.trim().isEmpty()) {
            throw new IllegalArgumentException(
                "Missing API key for provider: " + provider +
                ". Please configure: ai.providers." + provider + ".api-key"
            );
        }

        logger.info("Initializing LangChain4j StreamingChatModel: provider={}, model={}", provider, modelName);

        return OpenAiStreamingChatModel.builder()
            .apiKey(apiKey)
            .baseUrl(baseUrl)
            .modelName(modelName)
            .temperature(0.7)
            .timeout(Duration.ofSeconds(60))
            .build();
    }

    /**
     * OpenAI非流式聊天模型
     * 用于普通对话
     *
     * @return OpenAiChatModel实例
     */
    @Bean
    public ChatLanguageModel openAiChatModel(
            @Value("${ai.provider.current:deepseek}") String provider,
            @Value("${ai.providers.openai.api-key:}") String openaiKey,
            @Value("${ai.providers.openai.base-url:https://api.openai.com/v1}") String openaiBaseUrl,
            @Value("${ai.providers.deepseek.api-key:}") String deepseekKey,
            @Value("${ai.providers.deepseek.base-url:https://api.deepseek.com/v1}") String deepseekBaseUrl,
            @Value("${ai.providers.kimi.api-key:}") String kimiKey,
            @Value("${ai.providers.kimi.base-url:https://api.moonshot.cn/v1}") String kimiBaseUrl
    ) {
        String apiKey;
        String baseUrl;
        String modelName;

        switch (provider.toLowerCase()) {
            case "openai":
                apiKey = openaiKey;
                baseUrl = openaiBaseUrl;
                modelName = "gpt-4";
                break;
            case "deepseek":
                apiKey = deepseekKey;
                baseUrl = deepseekBaseUrl;
                modelName = "deepseek-chat";
                break;
            case "kimi":
                apiKey = kimiKey;
                baseUrl = kimiBaseUrl;
                modelName = "moonshot-v1-128k";
                break;
            default:
                throw new IllegalArgumentException("Unknown provider: " + provider);
        }

        if (apiKey == null || apiKey.trim().isEmpty()) {
            throw new IllegalArgumentException(
                "Missing API key for provider: " + provider
            );
        }

        logger.info("Initializing LangChain4j ChatLanguageModel: provider={}, model={}", provider, modelName);

        return OpenAiChatModel.builder()
            .apiKey(apiKey)
            .baseUrl(baseUrl)
            .modelName(modelName)
            .temperature(0.7)
            .timeout(Duration.ofSeconds(60))
            .maxRetries(3)
            .build();
    }

    /**
     * OpenAI图像生成模型（DALL-E）
     * 仅在provider为openai时可用
     *
     * @return ImageModel实例
     */
    @Bean(name = "imageModel")
    public ImageModel openAiImageModel(
            @Value("${ai.providers.openai.api-key:}") String apiKey,
            @Value("${ai.providers.openai.base-url:https://api.openai.com/v1}") String baseUrl
    ) {
        if (apiKey == null || apiKey.trim().isEmpty()) {
            logger.warn("OpenAI API key not configured, image generation will be disabled");
            return null;
        }

        logger.info("Initializing LangChain4j ImageModel (DALL-E)");

        return OpenAiImageModel.builder()
            .apiKey(apiKey)
            .baseUrl(baseUrl)
            .modelName("dall-e-3")
            .size("1024x1024")
            .quality("standard")
            .timeout(Duration.ofSeconds(30))
            .maxRetries(2)
            .build();
    }

    /**
     * 创建ChatMessage列表（辅助方法）
     * 将领域层的Message转换为LangChain4j的ChatMessage
     *
     * @param messages 领域层消息列表
     * @return LangChain4j消息列表
     */
    public static List<ChatMessage> toChatMessages(List<com.platform.domain.ai.Message> messages) {
        return messages.stream()
            .map(LangChain4jConfig::toChatMessage)
            .toList();
    }

    /**
     * 创建单个ChatMessage（辅助方法）
     *
     * @param message 领域层消息
     * @return LangChain4j消息
     */
    public static ChatMessage toChatMessage(com.platform.domain.ai.Message message) {
        return switch (message.getRole()) {
            case USER -> new UserMessage(message.getContent());
            case ASSISTANT, SYSTEM -> new AiMessage(message.getContent());
        };
    }
}
