package com.aieducenter.studio.infrastructure.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetails;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Collections;

/**
 * JWT认证过滤器（Spring MVC版本）
 *
 * 对应Python: backend/src/interfaces/auth.py中的get_current_user依赖
 * 从JWT Token中提取用户信息并设置到Spring Security上下文
 *
 * @author AI Teacher Platform
 */
@Component
public class JWTAuthenticationFilter extends OncePerRequestFilter {

    private final JWTProvider jwtProvider;

    public JWTAuthenticationFilter(JWTProvider jwtProvider) {
        this.jwtProvider = jwtProvider;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {

        // 从请求头提取Token
        String token = extractTokenFromRequest(request);

        if (StringUtils.hasText(token)) {
            try {
                // 验证Token并获取用户ID
                String userId = jwtProvider.validateTokenAndGetUserId(token);

                if (userId != null) {
                    // 创建认证对象
                    UserPrincipal userPrincipal = new UserPrincipal(userId);
                    UsernamePasswordAuthenticationToken authentication =
                        new UsernamePasswordAuthenticationToken(
                            userPrincipal,
                            null,
                            Collections.emptyList()
                        );

                    // 设置认证详情
                    authentication.setDetails(
                        new WebAuthenticationDetails(request)
                    );

                    // 设置到Security上下文
                    SecurityContextHolder.getContext().setAuthentication(authentication);
                }
            } catch (Exception e) {
                // Token无效，清除上下文
                SecurityContextHolder.clearContext();
            }
        }

        // 继续过滤器链
        filterChain.doFilter(request, response);
    }

    /**
     * 从请求中提取JWT Token
     * 对应Python的Authorization: Bearer <token>逻辑
     *
     * @param request HttpServletRequest
     * @return JWT Token字符串（不带"Bearer "前缀），如果没有返回null
     */
    private String extractTokenFromRequest(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");

        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7); // 移除"Bearer "前缀
        }

        return null;
    }
}
