package com.platform.infrastructure.ai.provider;

import com.platform.domain.ai.Message;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * AI Provider工厂类
 *
 * 对应Python: backend/src/infrastructure/providers/factory.py
 * 负责创建和管理AI Provider实例
 *
 * 功能：
 * - 支持通过名称创建Provider
 * - 支持从环境变量创建Provider
 * - Provider注册表管理
 *
 * @author AI Teacher Platform
 */
@Component
public class ProviderFactory {

    private static final Logger logger = LoggerFactory.getLogger(ProviderFactory.class);

    /**
     * Provider注册表：provider名称 -> Provider实例
     * 使用单例模式，每个provider只创建一次
     */
    private final Map<String, AIProvider> providers = new HashMap<>();

    private final String currentProvider;
    private final String openaiApiKey;
    private final String openaiBaseUrl;
    private final String deepseekApiKey;
    private final String deepseekBaseUrl;
    private final String kimiApiKey;
    private final String kimiBaseUrl;

    /**
     * 构造函数，注入配置
     */
    public ProviderFactory(
            @Value("${ai.provider.current:deepseek}") String currentProvider,
            @Value("${ai.providers.openai.api-key:}") String openaiApiKey,
            @Value("${ai.providers.openai.base-url:https://api.openai.com/v1}") String openaiBaseUrl,
            @Value("${ai.providers.deepseek.api-key:}") String deepseekApiKey,
            @Value("${ai.providers.deepseek.base-url:https://api.deepseek.com/v1}") String deepseekBaseUrl,
            @Value("${ai.providers.kimi.api-key:}") String kimiApiKey,
            @Value("${ai.providers.kimi.base-url:https://api.moonshot.cn/v1}") String kimiBaseUrl
    ) {
        this.currentProvider = currentProvider.toLowerCase();
        this.openaiApiKey = openaiApiKey;
        this.openaiBaseUrl = openaiBaseUrl;
        this.deepseekApiKey = deepseekApiKey;
        this.deepseekBaseUrl = deepseekBaseUrl;
        this.kimiApiKey = kimiApiKey;
        this.kimiBaseUrl = kimiBaseUrl;

        logger.info("ProviderFactory initialized with current provider: {}", this.currentProvider);
    }

    /**
     * 创建Provider实例
     *
     * 对应Python: ProviderFactory.create()
     *
     * @param providerName Provider名称（openai, deepseek, kimi等）
     * @param apiKey API密钥
     * @param baseUrl 可选的自定义baseUrl
     * @return AIProvider实例
     * @throws IllegalArgumentException 当providerName未注册时
     */
    public AIProvider create(String providerName, String apiKey, String baseUrl) {
        // 大小写不敏感
        String providerNameLower = providerName.toLowerCase();

        // 检查是否已存在实例
        if (providers.containsKey(providerNameLower)) {
            logger.debug("Returning existing provider instance: {}", providerNameLower);
            return providers.get(providerNameLower);
        }

        // 创建新的Provider实例
        AIProvider provider = createProviderInstance(providerNameLower, apiKey, baseUrl);
        providers.put(providerNameLower, provider);
        logger.info("Created and cached provider: {}", providerNameLower);

        return provider;
    }

    /**
     * 创建Provider实例（使用默认baseUrl）
     *
     * @param providerName Provider名称
     * @param apiKey API密钥
     * @return AIProvider实例
     */
    public AIProvider create(String providerName, String apiKey) {
        return create(providerName, apiKey, null);
    }

    /**
     * 从环境变量创建Provider实例
     *
     * 对应Python: ProviderFactory.create_from_env()
     *
     * 环境变量配置（application.yml）：
     * - ai.provider.current: provider名称（openai, deepseek, kimi）
     * - ai.providers.{provider}.api-key: 对应provider的API密钥
     * - ai.providers.{provider}.base-url: 可选的自定义baseUrl
     *
     * @return AIProvider实例
     * @throws IllegalArgumentException 当provider未配置或未注册时
     */
    public AIProvider createFromEnv() {
        logger.info("Creating provider from environment: {}", currentProvider);

        String apiKey;
        String baseUrl;

        switch (currentProvider) {
            case "openai":
                apiKey = openaiApiKey;
                baseUrl = openaiBaseUrl;
                break;
            case "deepseek":
                apiKey = deepseekApiKey;
                baseUrl = deepseekBaseUrl;
                break;
            case "kimi":
                apiKey = kimiApiKey;
                baseUrl = kimiBaseUrl;
                break;
            default:
                throw new IllegalArgumentException(
                    "Unknown provider: " + currentProvider +
                    ". Available providers: openai, deepseek, kimi"
                );
        }

        if (apiKey == null || apiKey.trim().isEmpty()) {
            throw new IllegalArgumentException(
                "Missing API key for provider '" + currentProvider + "'. " +
                "Please configure: ai.providers." + currentProvider + ".api-key"
            );
        }

        return create(currentProvider, apiKey, baseUrl);
    }

    /**
     * 获取当前配置的Provider实例
     *
     * @return AIProvider实例
     */
    public AIProvider getCurrentProvider() {
        return createFromEnv();
    }

    /**
     * 创建Provider实例的内部方法
     *
     * @param providerName Provider名称（小写）
     * @param apiKey API密钥
     * @param baseUrl baseUrl（可为null，使用默认值）
     * @return AIProvider实例
     * @throws IllegalArgumentException 当providerName不支持时
     */
    private AIProvider createProviderInstance(String providerName, String apiKey, String baseUrl) {
        switch (providerName) {
            case "openai":
                return new OpenAIProvider(apiKey, baseUrl != null ? baseUrl : "https://api.openai.com/v1");

            case "deepseek":
                return new DeepSeekProvider(apiKey, baseUrl != null ? baseUrl : "https://api.deepseek.com/v1");

            case "kimi":
                return new KimiProvider(apiKey, baseUrl != null ? baseUrl : "https://api.moonshot.cn/v1");

            default:
                throw new IllegalArgumentException(
                    "Unknown provider: " + providerName +
                    ". Available providers: openai, deepseek, kimi"
                );
        }
    }

    /**
     * 获取已注册的Provider列表
     *
     * 对应Python: ProviderFactory.get_registered_providers()
     *
     * @return Provider名称列表
     */
    public List<String> getRegisteredProviders() {
        return List.of("openai", "deepseek", "kimi");
    }

    /**
     * 检查Provider是否已注册
     *
     * 对应Python: ProviderFactory.is_provider_registered()
     *
     * @param providerName Provider名称
     * @return 是否已注册
     */
    public boolean isProviderRegistered(String providerName) {
        String nameLower = providerName.toLowerCase();
        return List.of("openai", "deepseek", "kimi").contains(nameLower);
    }

    /**
     * 清除缓存的Provider实例
     * 主要用于测试场景
     */
    public void clearCache() {
        providers.clear();
        logger.debug("Provider cache cleared");
    }
}
