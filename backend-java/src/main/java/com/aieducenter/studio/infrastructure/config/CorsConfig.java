package com.aieducenter.studio.infrastructure.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

import java.util.Arrays;
import java.util.Collections;

/**
 * CORS跨域配置
 *
 * 允许前端跨域调用API
 *
 * @author AI Teacher Platform
 */
@Configuration
public class CorsConfig {

    @Bean
    public CorsFilter corsFilter() {
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        CorsConfiguration config = new CorsConfiguration();

        // 允许携带认证信息（Cookie、Authorization头等）
        config.setAllowCredentials(true);

        // 允许的源（前端开发服务器）
        // 生产环境应该修改为实际的前端域名
        config.setAllowedOrigins(Arrays.asList(
            "http://localhost:5173",      // Vue开发服务器
            "http://localhost:5174",      // 备用端口
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174"
        ));

        // 允许的HTTP方法
        config.setAllowedMethods(Arrays.asList(
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS"
        ));

        // 允许的请求头
        config.setAllowedHeaders(Collections.singletonList("*"));

        // 暴露的响应头（允许前端读取这些响应头）
        config.setExposedHeaders(Arrays.asList(
            "Content-Type",
            "Authorization",
            "X-Total-Count",
            "X-Page-Count"
        ));

        // 预检请求的缓存时间（秒）
        config.setMaxAge(3600L);

        // 对所有API路径应用CORS配置
        source.registerCorsConfiguration("/api/**", config);

        return new CorsFilter(source);
    }

    /**
     * 备用方案：使用CorsConfigurationSource Bean
     * 如果上面的CorsFilter不生效，可以使用这个方案
     */
    /*
    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();

        configuration.setAllowCredentials(true);
        configuration.setAllowedOrigins(Arrays.asList(
            "http://localhost:5173",
            "http://localhost:5174"
        ));
        configuration.setAllowedMethods(Arrays.asList(
            "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"
        ));
        configuration.setAllowedHeaders(Collections.singletonList("*"));
        configuration.setExposedHeaders(Arrays.asList(
            "Content-Type", "Authorization", "X-Total-Count"
        ));
        configuration.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", configuration);

        return source;
    }
    */
}
