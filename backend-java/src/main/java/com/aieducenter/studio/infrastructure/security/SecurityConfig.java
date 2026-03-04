package com.aieducenter.studio.infrastructure.security;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.Collections;

/**
 * Spring Security配置（Spring MVC版本）
 *
 * 对应Python: backend/src/interfaces/auth.py的认证逻辑
 *
 * @author AI Teacher Platform
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {

    private final JWTAuthenticationFilter jwtAuthenticationFilter;

    public SecurityConfig(JWTAuthenticationFilter jwtAuthenticationFilter) {
        this.jwtAuthenticationFilter = jwtAuthenticationFilter;
    }

    /**
     * 配置安全过滤链（Spring MVC）
     *
     * @param http HttpSecurity构建器
     * @return SecurityFilterChain
     */
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            // 禁用CSRF（使用JWT时不需要）
            .csrf(csrf -> csrf.disable())

            // 禁用表单登录
            .formLogin(form -> form.disable())

            // 禁用HTTP Basic
            .httpBasic(basic -> basic.disable())

            // 配置会话管理（无状态）
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )

            // 配置CORS
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))

            // 配置授权规则
            .authorizeHttpRequests(auth -> auth
                // 公开端点
                .requestMatchers("/api/v1/auth/login").permitAll()
                .requestMatchers("/api/v1/navigation").permitAll()
                .requestMatchers("/api/v1/common-tools/categories").permitAll()
                .requestMatchers("/api/v1/common-tools/**").permitAll()
                .requestMatchers("/api/v1/works/categories").permitAll()
                .requestMatchers("/api/v1/works/**").permitAll()
                .requestMatchers("/api/v1/documents/categories").permitAll()
                .requestMatchers("/api/v1/documents/**").permitAll()
                .requestMatchers("/api/v1/tools").permitAll()
                .requestMatchers("/api/v1/toolsets/**").permitAll()
                .requestMatchers("/api/v1/convert/**").permitAll()
                .requestMatchers("/api/v1/tasks/**").permitAll()

                // 静态资源
                .requestMatchers("/static/**").permitAll()
                .requestMatchers("/health").permitAll()

                // 其他所有请求需要认证
                .anyRequest().authenticated()
            );

        // 添加JWT认证过滤器
        http.addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    /**
     * CORS配置
     *
     * @return CorsConfigurationSource
     */
    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOrigins(Arrays.asList("http://localhost:5173", "http://localhost:5174"));
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(Collections.singletonList("*"));
        configuration.setAllowCredentials(true);
        configuration.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }

    /**
     * 密码编码器（BCrypt）
     * 对应Python: backend/src/services/auth_service.py中的密码哈希逻辑
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
