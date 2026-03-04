package com.platform.infrastructure.ai.provider;

import com.platform.domain.ai.Message;
import com.platform.domain.ai.MessageRole;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * DeepSeek API提供商实现
 *
 * 对应Python: backend/src/infrastructure/providers/deepseek_provider.py
 *
 * DeepSeek专注于对话能力，兼容OpenAI协议
 * - 支持流式和非流式对话
 * - 不支持图片生成（使用NotImplementedError）
 * - 不支持音频生成（使用NotImplementedError）
 *
 * 支持的模型：
 * - deepseek-chat: 通用对话模型
 * - deepseek-coder: 代码专用模型
 *
 * @author AI Teacher Platform
 */
public class DeepSeekProvider implements AIProvider {

    private static final Logger logger = LoggerFactory.getLogger(DeepSeekProvider.class);

    private final String apiKey;
    private final String baseUrl;
    private final WebClient webClient;

    /**
     * 初始化DeepSeek Provider
     * 对应Python: def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com")
     *
     * @param apiKey DeepSeek API密钥
     * @param baseUrl API基础URL（默认为DeepSeek官方API地址）
     */
    public DeepSeekProvider(String apiKey, String baseUrl) {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.webClient = WebClient.builder()
            .baseUrl(baseUrl)
            .defaultHeader("Authorization", "Bearer " + apiKey)
            .defaultHeader("Content-Type", MediaType.APPLICATION_JSON_VALUE)
            .build();
        logger.info("DeepSeek Provider initialized with base_url: {}", baseUrl);
    }

    @Override
    public java.util.List<String> getSupportedModels() {
        // 对应Python: return ["deepseek-chat", "deepseek-coder"]
        return List.of("deepseek-chat", "deepseek-coder");
    }

    @Override
    public Flux<String> chatStream(
            List<Message> messages,
            String model,
            double temperature,
            Integer maxTokens
    ) {
        // 对应Python: async def chat_stream(...) -> AsyncGenerator[str, None]
        try {
            // 转换消息格式
            List<Map<String, String>> deepseekMessages = convertMessages(messages);

            // 构建请求体
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", model);
            requestBody.put("messages", deepseekMessages);
            requestBody.put("temperature", temperature);
            if (maxTokens != null) {
                requestBody.put("max_tokens", maxTokens);
            }
            requestBody.put("stream", true);

            // 调用DeepSeek API (流式)
            return webClient.post()
                .uri("/chat/completions")
                .bodyValue(requestBody)
                .retrieve()
                .bodyToFlux(String.class)
                .map(this::extractContent);

        } catch (Exception e) {
            logger.error("DeepSeek stream chat error: {}", e.getMessage(), e);
            return Flux.error(e);
        }
    }

    @Override
    public Mono<String> chat(
            List<Message> messages,
            String model,
            double temperature,
            Integer maxTokens
    ) {
        // 对应Python: async def chat(...) -> str
        try {
            // 转换消息格式
            List<Map<String, String>> deepseekMessages = convertMessages(messages);

            // 构建请求体
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", model);
            requestBody.put("messages", deepseekMessages);
            requestBody.put("temperature", temperature);
            if (maxTokens != null) {
                requestBody.put("max_tokens", maxTokens);
            }
            requestBody.put("stream", false);

            // 调用DeepSeek API
            return webClient.post()
                .uri("/chat/completions")
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(Map.class)
                .map(response -> {
                    // 提取消息内容
                    Map<String, Object> choices = (Map<String, Object>) response.get("choices");
                    if (choices != null && !choices.isEmpty()) {
                        Map<String, Object> firstChoice = (Map<String, Object>) choices.get(0);
                        Map<String, Object> message = (Map<String, Object>) firstChoice.get("message");
                        if (message != null) {
                            return (String) message.get("content");
                        }
                    }
                    return "";
                });

        } catch (Exception e) {
            logger.error("DeepSeek chat error: {}", e.getMessage(), e);
            return Mono.error(e);
        }
    }

    @Override
    public Mono<String> generateImage(String prompt, String size) {
        // 对应Python: async def generate_image(...) -> NotImplementedError
        // DeepSeek不支持图片生成
        return Mono.error(new UnsupportedOperationException(
            "DeepSeek does not support image generation. " +
            "Please use a provider that supports multimodal capabilities like OpenAI."
        ));
    }

    @Override
    public Mono<String> generateAudio(String text, String voice) {
        // 对应Python: async def generate_audio(...) -> NotImplementedError
        // DeepSeek不支持音频生成
        return Mono.error(new UnsupportedOperationException(
            "DeepSeek does not support audio generation. " +
            "Please use a provider that supports multimodal capabilities like OpenAI."
        ));
    }

    /**
     * 将Message对象列表转换为DeepSeek API格式
     * 对应Python: def _convert_messages(self, messages: List[Message]) -> List[dict]
     *
     * @param messages Message对象列表
     * @return DeepSeek格式的消息列表（与OpenAI格式相同）
     */
    private List<Map<String, String>> convertMessages(List<Message> messages) {
        List<Map<String, String>> deepseekMessages = new java.util.ArrayList<>();

        for (Message message : messages) {
            Map<String, String> msgDict = new HashMap<>();
            msgDict.put("role", convertRole(message.getRole()));
            msgDict.put("content", message.getContent());
            deepseekMessages.add(msgDict);
        }

        return deepseekMessages;
    }

    /**
     * 转换消息角色
     * 对应Python: def _convert_role(self, role: MessageRole) -> str
     *
     * @param role MessageRole枚举
     * @return DeepSeek格式的角色字符串（与OpenAI格式相同）
     */
    private String convertRole(MessageRole role) {
        if (role == null) {
            return "user";
        }

        switch (role) {
            case SYSTEM:
                return "system";
            case USER:
                return "user";
            case ASSISTANT:
                return "assistant";
            default:
                return "user"; // 默认为user
        }
    }

    /**
     * 从SSE响应中提取内容
     *
     * @param sseLine SSE数据行
     * @return 提取的内容
     */
    private String extractContent(String sseLine) {
        try {
            if (sseLine.startsWith("data: ")) {
                String json = sseLine.substring(6);
                com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
                com.fasterxml.jackson.databind.JsonNode root = mapper.readTree(json);
                com.fasterxml.jackson.databind.JsonNode choices = root.path("choices");
                if (choices.isArray() && choices.size() > 0) {
                    com.fasterxml.jackson.databind.JsonNode delta = choices.get(0).path("delta");
                    if (delta != null) {
                        com.fasterxml.jackson.databind.JsonNode content = delta.path("content");
                        if (content != null) {
                            return content.asText();
                        }
                    }
                }
            }
            return "";
        } catch (Exception e) {
            return "";
        }
    }
}
