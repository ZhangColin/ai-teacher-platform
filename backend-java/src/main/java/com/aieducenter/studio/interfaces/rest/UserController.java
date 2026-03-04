package com.platform.interfaces.rest;

import com.platform.application.service.UserService;
import com.platform.interfaces.rest.dto.user.*;
import com.platform.interfaces.rest.dto.UserInfo;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

/**
 * 用户管理控制器
 *
 * 对应Python: backend/src/interfaces/routers/users/users.py
 *
 * 端点列表：
 * - GET    /api/v1/admin/users - 获取用户列表
 * - POST   /api/v1/admin/users - 创建用户
 * - GET    /api/v1/admin/users/{user_id} - 获取用户详情
 * - PUT    /api/v1/admin/users/{user_id} - 完整更新用户
 * - PATCH  /api/v1/admin/users/{user_id} - 部分更新用户
 * - DELETE /api/v1/admin/users/{user_id} - 删除用户
 * - POST   /api/v1/admin/users/{user_id}/reset-password - 重置密码
 *
 * @author AI Teacher Platform
 */
@RestController
@RequestMapping("/api/v1/admin/users")
public class UserController {

    private static final Logger logger = LoggerFactory.getLogger(UserController.class);

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    /**
     * 管理员权限验证
     */
    private void requireAdmin(UserInfo currentUser) {
        if (currentUser == null || !Boolean.TRUE.equals(currentUser.getIsAdmin())) {
            throw new IllegalArgumentException("需要管理员权限");
        }
    }

    /**
     * 获取用户列表（管理员功能）
     * GET /api/v1/admin/users
     */
    @GetMapping
    public ResponseEntity<UserListResponse> getUserList(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize,
            @RequestParam(required = false) Boolean is_admin,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            // 限制每页最大数量
            if (pageSize > 100) {
                pageSize = 100;
            }

            var result = userService.getAllUsers(page, pageSize, is_admin);

            return ResponseEntity.ok(UserListResponse.builder()
                .users(result.getUsers().stream()
                    .map(this::convertToUserDTO)
                    .toList())
                .total((int) result.getTotal())
                .page(page)
                .pageSize(pageSize)
                .build());
        } catch (Exception e) {
            logger.error("获取用户列表失败: {}", e.getMessage(), e);
            throw new RuntimeException("获取用户列表失败: " + e.getMessage());
        }
    }

    /**
     * 创建新用户（管理员功能）
     * POST /api/v1/admin/users
     */
    @PostMapping
    public ResponseEntity<CreateUserResponse> createUser(
            @Valid @RequestBody CreateUserRequest request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            var user = userService.createUser(
                request.getUsername(),
                request.getNickname(),
                request.getEmail(),
                request.getPassword(),
                request.getPhone(),
                request.getAvatar(),
                request.getIsAdmin()
            );

            return ResponseEntity.status(HttpStatus.CREATED).body(CreateUserResponse.builder()
                .user(convertToUserDTO(user))
                .build());
        } catch (IllegalArgumentException e) {
            if (e.getMessage() != null && e.getMessage().contains("已存在")) {
                throw new IllegalArgumentException(e.getMessage());
            }
            throw e;
        } catch (Exception e) {
            logger.error("创建用户失败: {}", e.getMessage(), e);
            throw new RuntimeException("创建用户失败: " + e.getMessage());
        }
    }

    /**
     * 获取单个用户信息（管理员功能）
     * GET /api/v1/admin/users/{user_id}
     */
    @GetMapping("/{user_id}")
    public ResponseEntity<UpdateUserResponse> getUser(
            @PathVariable("user_id") String userId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            var user = userService.getUserById(userId);
            if (user == null) {
                throw new IllegalArgumentException("用户不存在");
            }

            return ResponseEntity.ok(UpdateUserResponse.builder()
                .user(convertToUserDTO(user))
                .build());
        } catch (IllegalArgumentException e) {
            if ("用户不存在".equals(e.getMessage())) {
                throw new IllegalArgumentException(e.getMessage());
            }
            throw e;
        } catch (Exception e) {
            logger.error("获取用户失败: {}", e.getMessage(), e);
            throw new RuntimeException("获取用户失败: " + e.getMessage());
        }
    }

    /**
     * 更新用户信息（管理员功能）- PUT方法（完整替换）
     * PUT /api/v1/admin/users/{user_id}
     */
    @PutMapping("/{user_id}")
    public ResponseEntity<UpdateUserResponse> updateUserPut(
            @PathVariable("user_id") String userId,
            @RequestBody UpdateUserRequest request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        return updateUserImpl(userId, request, currentUser);
    }

    /**
     * 更新用户信息（管理员功能）- PATCH方法（部分更新）
     * PATCH /api/v1/admin/users/{user_id}
     */
    @PatchMapping("/{user_id}")
    public ResponseEntity<UpdateUserResponse> updateUser(
            @PathVariable("user_id") String userId,
            @RequestBody UpdateUserRequest request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        return updateUserImpl(userId, request, currentUser);
    }

    /**
     * 更新用户的实现逻辑
     */
    private ResponseEntity<UpdateUserResponse> updateUserImpl(
            String userId,
            UpdateUserRequest request,
            UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            var user = userService.updateUser(
                userId,
                request.getUsername(),
                request.getNickname(),
                request.getEmail(),
                request.getPhone(),
                request.getIsAdmin()
            );

            if (user == null) {
                throw new IllegalArgumentException("用户不存在");
            }

            return ResponseEntity.ok(UpdateUserResponse.builder()
                .user(convertToUserDTO(user))
                .build());
        } catch (IllegalArgumentException e) {
            if (e.getMessage() != null) {
                if ("用户不存在".equals(e.getMessage())) {
                    throw new IllegalArgumentException(e.getMessage());
                }
                if (e.getMessage().contains("最后一个管理员")) {
                    throw new IllegalArgumentException(e.getMessage());
                }
                if (e.getMessage().contains("已存在")) {
                    throw new IllegalArgumentException(e.getMessage());
                }
            }
            throw e;
        } catch (Exception e) {
            logger.error("更新用户失败: {}", e.getMessage(), e);
            throw new RuntimeException("更新用户失败: " + e.getMessage());
        }
    }

    /**
     * 删除用户（管理员功能）
     * DELETE /api/v1/admin/users/{user_id}
     */
    @DeleteMapping("/{user_id}")
    public ResponseEntity<Void> deleteUser(
            @PathVariable("user_id") String userId,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            boolean success = userService.deleteUser(userId, currentUser.getUserId());
            if (!success) {
                throw new IllegalArgumentException("用户不存在");
            }

            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            if ("用户不存在".equals(e.getMessage()) ||
                (e.getMessage() != null && (e.getMessage().contains("不能删除自己") ||
                 e.getMessage().contains("最后一个管理员")))) {
                throw new IllegalArgumentException(e.getMessage());
            }
            throw e;
        } catch (Exception e) {
            logger.error("删除用户失败: {}", e.getMessage(), e);
            throw new RuntimeException("删除用户失败: " + e.getMessage());
        }
    }

    /**
     * 重置用户密码（管理员功能）
     * POST /api/v1/admin/users/{user_id}/reset-password
     */
    @PostMapping("/{user_id}/reset-password")
    public ResponseEntity<ResetPasswordResponse> resetUserPassword(
            @PathVariable("user_id") String userId,
            @Valid @RequestBody ResetPasswordRequest request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            requireAdmin(currentUser);

            boolean success = userService.resetPassword(userId, request.getNewPassword());
            if (!success) {
                throw new IllegalArgumentException("用户不存在");
            }

            return ResponseEntity.ok(ResetPasswordResponse.builder()
                .message("密码已重置")
                .newPassword(request.getNewPassword())
                .build());
        } catch (IllegalArgumentException e) {
            if ("用户不存在".equals(e.getMessage())) {
                throw new IllegalArgumentException(e.getMessage());
            }
            throw e;
        } catch (Exception e) {
            logger.error("重置密码失败: {}", e.getMessage(), e);
            throw new RuntimeException("重置密码失败: " + e.getMessage());
        }
    }

    /**
     * 转换为UserDTO
     */
    private UserDTO convertToUserDTO(com.platform.domain.user.User user) {
        return UserDTO.builder()
            .userId(user.getUserId())
            .username(user.getUsername())
            .nickname(user.getNickname())
            .email(user.getEmail())
            .phone(user.getPhone())
            .avatar(user.getAvatar())
            .isAdmin(user.getIsAdmin())
            .createdAt(user.getCreatedAt())
            .build();
    }
}
