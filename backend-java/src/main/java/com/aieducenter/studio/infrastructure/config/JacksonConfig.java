package com.platform.infrastructure.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

/**
 * Jackson配置
 *
 * 统一JSON字段命名为snake_case，与前端保持一致
 *
 * 前端示例：
 * - 请求: {"message": "hello", "session_id": "123"}
 * - 响应: {"user_id": "456", "session_id": "789"}
 *
 * @author AI Teacher Platform
 */
@Configuration
public class JacksonConfig {

    @Bean
    @Primary
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();

        // 注册JavaTimeModule以支持Java 8日期时间类型
        mapper.registerModule(new JavaTimeModule());

        // 禁用将日期写为时间戳
        mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

        // 统一使用snake_case命名策略
        // 这样Java的camelCase字段会自动转换为snake_case的JSON字段
        // 例如: userId -> user_id, sessionId -> session_id
        mapper.setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);

        return mapper;
    }
}
