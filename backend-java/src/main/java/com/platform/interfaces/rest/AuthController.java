package com.platform.interfaces.rest;

import com.platform.application.service.AuthService;
import com.platform.application.service.UserService;
import com.platform.interfaces.rest.dto.UserInfo;
import lombok.AllArgsConstructor;
import lombok.Data;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.regex.Pattern;

/**
 * 认证控制器
 *
 * 对应Python: backend/src/interfaces/routers/auth/auth.py
 *
 * @author AI Teacher Platform
 */
@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final AuthService authService;
    private final UserService userService;

    public AuthController(AuthService authService, UserService userService) {
        this.authService = authService;
        this.userService = userService;
    }

    /**
     * 用户登录
     *
     * 对应Python: @router.post("/login")
     */
    @PostMapping("/login")
    public LoginResponse login(@RequestBody LoginRequest request) {
        String token = authService.login(
            request.getAccount(),
            request.getPassword(),
            request.isRememberMe()
        );

        if (token == null) {
            throw new RuntimeException("账号或密码错误");
        }

        String userId = authService.validateToken(token);
        var user = userService.getUserById(userId);

        long expiresIn = request.isRememberMe() ? 604800L : 86400L;

        return new LoginResponse(
            token,
            UserInfo.builder()
                .userId(user.getId())
                .username(user.getUsername())
                .isAdmin(user.getIsAdmin())
                .build(),
            expiresIn
        );
    }

    /**
     * 获取当前用户信息
     *
     * 对应Python: @router.get("/me")
     */
    @GetMapping("/me")
    public UserInfoResponse getMe() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        String userId = auth.getName();

        var user = userService.getUserById(userId);
        return new UserInfoResponse(
            UserInfo.builder()
                .userId(user.getId())
                .username(user.getUsername())
                .isAdmin(user.getIsAdmin())
                .build()
        );
    }

    @Data
    public static class LoginRequest {
        private String account;
        private String password;
        private boolean rememberMe = false;
    }

    @Data
    @AllArgsConstructor
    public static class LoginResponse {
        private String token;
        private UserInfo user;
        private long expiresIn;
    }

    @Data
    @AllArgsConstructor
    public static class UserInfoResponse {
        private UserInfo user;
    }
}
