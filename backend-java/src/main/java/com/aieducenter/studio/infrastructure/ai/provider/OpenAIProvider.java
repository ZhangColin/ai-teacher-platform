package com.platform.infrastructure.ai.provider;

import com.platform.domain.ai.Message;
import com.platform.domain.ai.MessageRole;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * OpenAI API提供商实现
 *
 * 对应Python: backend/src/infrastructure/providers/openai_provider.py
 *
 * 支持功能：
 * - 流式和非流式对话
 * - 图片生成 (DALL-E)
 * - 音频生成 (TTS)
 *
 * @author AI Teacher Platform
 */
public class OpenAIProvider implements AIProvider {

    private static final Logger logger = LoggerFactory.getLogger(OpenAIProvider.class);

    private final String apiKey;
    private final String baseUrl;
    private final WebClient webClient;

    /**
     * 初始化OpenAI Provider
     * 对应Python: def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1")
     *
     * @param apiKey OpenAI API密钥
     * @param baseUrl API基础URL（默认为官方API地址）
     */
    public OpenAIProvider(String apiKey, String baseUrl) {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.webClient = WebClient.builder()
            .baseUrl(baseUrl)
            .defaultHeader("Authorization", "Bearer " + apiKey)
            .defaultHeader("Content-Type", MediaType.APPLICATION_JSON_VALUE)
            .build();
        logger.info("OpenAI Provider initialized with base_url: {}", baseUrl);
    }

    @Override
    public java.util.List<String> getSupportedModels() {
        // 对应Python: return ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        return List.of("gpt-4", "gpt-4-turbo", "gpt-3.5-turbo");
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
            List<Map<String, String>> openaiMessages = convertMessages(messages);

            // 构建请求体
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", model);
            requestBody.put("messages", openaiMessages);
            requestBody.put("temperature", temperature);
            if (maxTokens != null) {
                requestBody.put("max_tokens", maxTokens);
            }
            requestBody.put("stream", true);

            // 调用OpenAI API (流式)
            return webClient.post()
                .uri("/chat/completions")
                .bodyValue(requestBody)
                .retrieve()
                .bodyToFlux(String.class)
                .map(this::extractContent);

        } catch (Exception e) {
            logger.error("OpenAI stream chat error: {}", e.getMessage(), e);
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
            List<Map<String, String>> openaiMessages = convertMessages(messages);

            // 构建请求体
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", model);
            requestBody.put("messages", openaiMessages);
            requestBody.put("temperature", temperature);
            if (maxTokens != null) {
                requestBody.put("max_tokens", maxTokens);
            }
            requestBody.put("stream", false);

            // 调用OpenAI API
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
            logger.error("OpenAI chat error: {}", e.getMessage(), e);
            return Mono.error(e);
        }
    }

    @Override
    public Mono<String> generateImage(String prompt, String size) {
        // 对应Python: async def generate_image(...) -> str
        try {
            // 构建请求体
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", "dall-e-3");
            requestBody.put("prompt", prompt);
            requestBody.put("size", size);

            // 调用OpenAI API
            return webClient.post()
                .uri("/images/generations")
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(Map.class)
                .map(response -> {
                    // 提取图片URL
                    List<Map<String, Object>> data = (List<Map<String, Object>>) response.get("data");
                    if (data != null && !data.isEmpty()) {
                        Map<String, Object> firstImage = data.get(0);
                        if (firstImage != null) {
                            return (String) firstImage.get("url");
                        }
                    }
                    return "";
                });

        } catch (Exception e) {
            logger.error("OpenAI image generation error: {}", e.getMessage(), e);
            return Mono.error(e);
        }
    }

    @Override
    public Mono<String> generateAudio(String text, String voice) {
        // 对应Python: async def generate_audio(...) -> str
        try {
            // 构建请求体
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", "tts-1");
            requestBody.put("voice", voice);
            requestBody.put("input", text);

            // 调用OpenAI API
            return webClient.post()
                .uri("/audio/speech")
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(byte[].class)
                .map(audioContent -> {
                    // 将音频内容转为base64
                    String base64Audio = java.util.Base64.getEncoder().encodeToString(audioContent);
                    return "data:audio/mp3;base64," + base64Audio;
                });

        } catch (Exception e) {
            logger.error("OpenAI audio generation error: {}", e.getMessage(), e);
            return Mono.error(e);
        }
    }

    /**
     * 将Message对象列表转换为OpenAI API格式
     * 对应Python: def _convert_messages(self, messages: List[Message]) -> List[dict]
     *
     * @param messages Message对象列表
     * @return OpenAI格式的消息列表
     */
    private List<Map<String, String>> convertMessages(List<Message> messages) {
        List<Map<String, String>> openaiMessages = new java.util.ArrayList<>();

        for (Message message : messages) {
            Map<String, String> msgDict = new HashMap<>();
            msgDict.put("role", convertRole(message.getRole()));
            msgDict.put("content", message.getContent());
            openaiMessages.add(msgDict);
        }

        return openaiMessages;
    }

    /**
     * 转换消息角色
     * 对应Python: def _convert_role(self, role: MessageRole) -> str
     *
     * @param role MessageRole枚举
     * @return OpenAI格式的角色字符串
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
