package com.platform.infrastructure.ai.provider;

import com.platform.domain.ai.Message;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * AI提供商接口
 *
 * 对应Python: backend/src/infrastructure/providers/base.py
 * 所有AI提供商（OpenAI、DeepSeek、Kimi等）都必须实现此接口
 *
 * @author AI Teacher Platform
 */
public interface AIProvider {

    /**
     * 流式对话
     * 对应Python: async def chat_stream(...) -> AsyncGenerator[str, None]
     *
     * @param messages 消息列表
     * @param model 模型名称
     * @param temperature 温度参数（0-1）
     * @param maxTokens 最大生成token数
     * @return 流式返回的文本片段（响应式Flux）
     */
    Flux<String> chatStream(
            java.util.List<Message> messages,
            String model,
            double temperature,
            Integer maxTokens
    );

    /**
     * 非流式对话
     * 对应Python: async def chat(...) -> str
     *
     * @param messages 消息列表
     * @param model 模型名称
     * @param temperature 温度参数（0-1）
     * @param maxTokens 最大生成token数
     * @return 完整的AI响应文本（响应式Mono）
     */
    Mono<String> chat(
            java.util.List<Message> messages,
            String model,
            double temperature,
            Integer maxTokens
    );

    /**
     * 生成图片
     * 对应Python: async def generate_image(...) -> str
     *
     * @param prompt 图片描述提示词
     * @param size 图片尺寸
     * @return 图片URL或base64编码（响应式Mono）
     */
    Mono<String> generateImage(
            String prompt,
            String size
    );

    /**
     * 生成音频
     * 对应Python: async def generate_audio(...) -> str
     *
     * @param text 要转换为音频的文本
     * @param voice 音色/声音
     * @return 音频文件URL或base64编码（响应式Mono）
     */
    Mono<String> generateAudio(
            String text,
            String voice
    );

    /**
     * 获取支持的模型列表
     * 对应Python: def get_supported_models() -> List[str]
     *
     * @return 支持的模型名称列表
     */
    java.util.List<String> getSupportedModels();

    /**
     * 验证模型是否支持
     * 对应Python: def validate_model(model: str) -> bool
     *
     * @param model 模型名称
     * @return 是否支持该模型
     */
    default boolean validateModel(String model) {
        return getSupportedModels().contains(model);
    }
}
