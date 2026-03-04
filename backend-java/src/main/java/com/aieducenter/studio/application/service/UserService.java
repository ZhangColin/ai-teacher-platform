package com.platform.application.service;

import com.platform.domain.user.User;
import com.platform.infrastructure.persistence.jpa.UserEntity;
import com.platform.infrastructure.persistence.jpa.UserJpaRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * 用户服务
 *
 * 对应Python: backend/src/services/user_service.py
 * 负责用户的CRUD操作
 *
 * @author AI Teacher Platform
 */
@Service
public class UserService {

    private static final Logger logger = LoggerFactory.getLogger(UserService.class);

    private final UserJpaRepository userJpaRepository;
    private final PasswordEncoder passwordEncoder;

    public UserService(
            UserJpaRepository userJpaRepository,
            PasswordEncoder passwordEncoder
    ) {
        this.userJpaRepository = userJpaRepository;
        this.passwordEncoder = passwordEncoder;
    }

    /**
     * 创建新用户
     *
     * 对应Python: def create_user(...)
     *
     * @param username 用户名
     * @param password 密码
     * @param nickname 昵称
     * @param email 邮箱
     * @param phone 手机号
     * @param avatar 头像
     * @param isAdmin 是否为管理员
     * @return 创建的用户
     * @throws IllegalArgumentException 用户名/邮箱/手机号已存在
     */
    @Transactional
    public User createUser(
            String username,
            String password,
            String nickname,
            String email,
            String phone,
            String avatar,
            Boolean isAdmin
    ) {
        // 检查用户名是否已存在
        if (userJpaRepository.existsByUsername(username)) {
            throw new IllegalArgumentException("用户名已存在: " + username);
        }

        // 检查邮箱是否已存在
        if (email != null && !email.trim().isEmpty() && userJpaRepository.existsByEmail(email)) {
            throw new IllegalArgumentException("邮箱已存在: " + email);
        }

        // 检查手机号是否已存在
        if (phone != null && !phone.trim().isEmpty() && userJpaRepository.existsByPhone(phone)) {
            throw new IllegalArgumentException("手机号已存在: " + phone);
        }

        // 创建用户实体
        UserEntity entity = new UserEntity();
        entity.setUserId(UUID.randomUUID().toString());
        entity.setUsername(username);
        entity.setPasswordHash(passwordEncoder.encode(password));
        entity.setNickname(nickname);
        entity.setEmail(email);
        entity.setPhone(phone);
        entity.setAvatar(avatar);
        entity.setIsAdmin(isAdmin != null ? isAdmin : false);

        UserEntity saved = userJpaRepository.save(entity);
        logger.info("创建用户成功: userId={}, username={}", saved.getUserId(), username);

        return toDomainModel(saved);
    }

    /**
     * 根据邮箱获取用户
     *
     * 对应Python: def get_user_by_email(...)
     *
     * @param email 邮箱
     * @return 用户，不存在返回null
     */
    public User getUserByEmail(String email) {
        return userJpaRepository.findByEmail(email)
            .map(this::toDomainModel)
            .orElse(null);
    }

    /**
     * 根据手机号获取用户
     *
     * 对应Python: def get_user_by_phone(...)
     *
     * @param phone 手机号
     * @return 用户，不存在返回null
     */
    public User getUserByPhone(String phone) {
        return userJpaRepository.findByPhone(phone)
            .map(this::toDomainModel)
            .orElse(null);
    }

    /**
     * 根据用户名获取用户
     *
     * 对应Python: def get_user_by_username(...)
     *
     * @param username 用户名
     * @return 用户，不存在返回null
     */
    public User getUserByUsername(String username) {
        return userJpaRepository.findByUsername(username)
            .map(this::toDomainModel)
            .orElse(null);
    }

    /**
     * 根据用户ID获取用户
     *
     * 对应Python: def get_user_by_id(...)
     *
     * @param userId 用户ID
     * @return 用户，不存在返回null
     */
    public User getUserById(String userId) {
        return userJpaRepository.findById(userId)
            .map(this::toDomainModel)
            .orElse(null);
    }

    /**
     * 获取所有用户（分页）
     *
     * 对应Python: def get_all_users(...)
     *
     * @param page 页码（从1开始）
     * @param pageSize 每页数量
     * @param isAdmin 管理员筛选（可选）
     * @return 用户列表和总数
     */
    public UserListResult getAllUsers(int page, int pageSize, Boolean isAdmin) {
        // 限制每页最大数量
        if (pageSize > 100) {
            pageSize = 100;
        }

        // 创建分页和排序
        Pageable pageable = PageRequest.of(
            page - 1,  // Spring Data JPA页码从0开始
            pageSize,
            Sort.by(Sort.Direction.DESC, "createdAt")
        );

        Page<UserEntity> result;
        if (isAdmin != null) {
            result = userJpaRepository.findAllByIsAdmin(isAdmin, pageable);
        } else {
            result = userJpaRepository.findAll(pageable);
        }

        List<User> users = result.getContent().stream()
            .map(this::toDomainModel)
            .collect(Collectors.toList());

        return new UserListResult(users, result.getTotalElements());
    }

    /**
     * 更新用户信息
     *
     * 对应Python: def update_user(...)
     *
     * @param userId 用户ID
     * @param username 新用户名
     * @param nickname 新昵称
     * @param email 新邮箱
     * @param phone 新手机号
     * @param isAdmin 是否为管理员
     * @return 更新后的用户，失败返回null
     */
    @Transactional
    public User updateUser(
            String userId,
            String username,
            String nickname,
            String email,
            String phone,
            Boolean isAdmin
    ) {
        return userJpaRepository.findById(userId)
            .map(entity -> {
                // 检查用户名是否与其他用户冲突
                if (username != null && !username.equals(entity.getUsername())) {
                    if (userJpaRepository.existsByUsername(username)) {
                        throw new IllegalArgumentException("用户名已存在: " + username);
                    }
                    entity.setUsername(username);
                }

                // 检查邮箱是否与其他用户冲突
                if (email != null && !email.equals(entity.getEmail())) {
                    if (userJpaRepository.existsByEmail(email)) {
                        throw new IllegalArgumentException("邮箱已存在: " + email);
                    }
                    entity.setEmail(email);
                }

                // 检查手机号是否与其他用户冲突
                if (phone != null && !phone.equals(entity.getPhone())) {
                    if (userJpaRepository.existsByPhone(phone)) {
                        throw new IllegalArgumentException("手机号已存在: " + phone);
                    }
                    entity.setPhone(phone);
                }

                // 更新其他字段
                if (nickname != null) {
                    entity.setNickname(nickname);
                }
                if (isAdmin != null) {
                    // 防止取消最后一个管理员
                    if (!isAdmin && entity.getIsAdmin() && isLastAdmin(userId)) {
                        throw new IllegalArgumentException("不能取消最后一个管理员的管理员权限");
                    }
                    entity.setIsAdmin(isAdmin);
                }

                UserEntity saved = userJpaRepository.save(entity);
                logger.info("更新用户成功: userId={}", userId);

                return toDomainModel(saved);
            })
            .orElse(null);
    }

    /**
     * 删除用户
     *
     * 对应Python: def delete_user(...)
     *
     * @param userId 用户ID
     * @param currentUserId 当前用户ID
     * @return 是否删除成功
     */
    @Transactional
    public boolean deleteUser(String userId, String currentUserId) {
        // 不能删除自己
        if (userId.equals(currentUserId)) {
            throw new IllegalArgumentException("不能删除自己的账号");
        }

        return userJpaRepository.findById(userId)
            .map(entity -> {
                // 防止删除最后一个管理员
                if (entity.getIsAdmin() && isLastAdmin(userId)) {
                    throw new IllegalArgumentException("不能删除最后一个管理员");
                }

                userJpaRepository.delete(entity);
                logger.info("删除用户成功: userId={}", userId);
                return true;
            })
            .orElse(false);
    }

    /**
     * 重置用户密码
     *
     * 对应Python: def reset_password(...)
     *
     * @param userId 用户ID
     * @param newPassword 新密码
     * @return 是否重置成功
     */
    @Transactional
    public boolean resetPassword(String userId, String newPassword) {
        return userJpaRepository.findById(userId)
            .map(entity -> {
                entity.setPasswordHash(passwordEncoder.encode(newPassword));
                userJpaRepository.save(entity);
                logger.info("重置用户密码成功: userId={}", userId);
                return true;
            })
            .orElse(false);
    }

    /**
     * 验证密码
     *
     * @param userId 用户ID
     * @param password 密码
     * @return 是否正确
     */
    public boolean verifyPassword(String userId, String password) {
        return userJpaRepository.findById(userId)
            .map(entity -> passwordEncoder.matches(password, entity.getPasswordHash()))
            .orElse(false);
    }

    /**
     * 检查是否是最后一个管理员
     */
    private boolean isLastAdmin(String userId) {
        long adminCount = userJpaRepository.countByIsAdminTrue();
        if (adminCount <= 1) {
            return true;
        }

        // 如果还有其他管理员，检查当前用户是否是管理员
        return userJpaRepository.findById(userId)
            .map(UserEntity::getIsAdmin)
            .orElse(false);
    }

    /**
     * 将JPA实体转换为领域模型
     */
    private User toDomainModel(UserEntity entity) {
        User user = new User();
        user.setId(entity.getUserId());
        user.setUsername(entity.getUsername());
        user.setEmail(entity.getEmail());
        user.setIsAdmin(entity.getIsAdmin());
        user.setCreatedAt(entity.getCreatedAt());
        // nickname, phone, avatar, updatedAt 等字段在User领域模型中可能不存在
        // 这里根据实际的User领域模型进行调整
        return user;
    }

    /**
     * 用户列表结果（包含列表和总数）
     */
    public static class UserListResult {
        private final List<User> users;
        private final long total;

        public UserListResult(List<User> users, long total) {
            this.users = users;
            this.total = total;
        }

        public List<User> getUsers() {
            return users;
        }

        public long getTotal() {
            return total;
        }
    }
}
