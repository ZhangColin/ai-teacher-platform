package com.aieducenter.studio.application.service;

import com.aieducenter.studio.domain.user.User;
import com.aieducenter.studio.infrastructure.security.JWTProvider;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * 认证服务
 *
 * 对应Python: backend/src/services/auth_service.py
 * 负责JWT Token生成和验证
 *
 * @author AI Teacher Platform
 */
@Service
public class AuthService {

    private static final Logger logger = LoggerFactory.getLogger(AuthService.class);

    private final JWTProvider jwtProvider;
    private final UserService userService;

    public AuthService(JWTProvider jwtProvider, UserService userService) {
        this.jwtProvider = jwtProvider;
        this.userService = userService;
    }

    /**
     * 用户登录
     *
     * @param account 账号（用户名/邮箱/手机号）
     * @param password 密码
     * @param rememberMe 是否记住我
     * @return JWT Token，失败返回null
     */
    public String login(String account, String password, boolean rememberMe) {
        // 判断账号类型：手机号 > 邮箱 > 用户名（优先级）
        User user = null;

        // 手机号正则
        if (account.matches("^1[3-9]\\d{9}$")) {
            user = userService.getUserByPhone(account);
        }
        // 邮箱正则
        else if (account.matches("^[^@]+@[^@]+\\.[^@]+$")) {
            user = userService.getUserByEmail(account);
        }
        // 用户名（默认）
        else {
            user = userService.getUserByUsername(account);
        }

        if (user == null) {
            logger.warn("登录失败：用户不存在 - {}", account);
            return null;
        }

        // 验证密码
        if (!userService.verifyPassword(user.getId(), password)) {
            logger.warn("登录失败：密码错误 - {}", account);
            return null;
        }

        // 生成Token
        String token = jwtProvider.generateToken(user.getId(), rememberMe);
        logger.info("登录成功：userId={}, username={}", user.getId(), user.getUsername());

        return token;
    }

    /**
     * 验证Token并获取用户ID
     *
     * @param token JWT Token
     * @return 用户ID，无效返回null
     */
    public String validateToken(String token) {
        try {
            return jwtProvider.validateTokenAndGetUserId(token);
        } catch (Exception e) {
            logger.warn("Token验证失败：{}", e.getMessage());
            return null;
        }
    }

    /**
     * 获取当前用户信息
     *
     * @param userId 用户ID
     * @return 用户信息
     */
    public User getCurrentUser(String userId) {
        return userService.getUserById(userId);
    }
}
