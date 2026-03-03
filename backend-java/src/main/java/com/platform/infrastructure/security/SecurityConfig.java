package com.platform.infrastructure.security;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

/**
 * Spring Security配置
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
     * 配置安全过滤链
     *
     * @param http HttpSecurity构建器
     * @return SecurityFilterChain
     * @throws Exception 配置异常
     */
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            // 禁用CSRF（使用JWT时不需要）
            .csrf(csrf -> csrf.disable())

            // 配置会话管理（无状态，使用JWT）
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )

            // 配置授权规则
            .authorizeHttpRequests(auth -> auth
                // 公开端点
                .requestMatchers("/api/v1/auth/login").permitAll()
                .requestMatchers("/api/v1/navigation").permitAll()
                .requestMatchers("/api/v1/common-tools/categories").permitAll()
                .requestMatchers("/api/v1/works/categories").permitAll()
                .requestMatchers("/api/v1/documents/categories").permitAll()

                // 静态资源
                .requestMatchers("/static/**").permitAll()
                .requestMatchers("/health").permitAll()

                // 其他所有请求需要认证
                .anyRequest().authenticated()
            )

            // 添加JWT认证过滤器
            .addFilterBefore(jwtAuthenticationFilter,
                org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter.class);

        return http.build();
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
