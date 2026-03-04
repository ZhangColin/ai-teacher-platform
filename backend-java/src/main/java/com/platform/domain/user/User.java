package com.platform.domain.user;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * 用户领域实体
 *
 * 对应Python: backend/src/domain/entities/user.py
 *
 * 业务规则：
 * - 管理员可以访问所有工具
 * - 普通用户的访问权限待实现
 *
 * @author AI Teacher Platform
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class User {

    /**
     * 用户唯一标识（UUID字符串）
     * 对应Python: user_id: str
     */
    private String userId;

    /**
     * 设置用户ID
     */
    public void setId(String userId) {
        this.userId = userId;
    }

    /**
     * 获取用户ID（兼容方法）
     */
    public String getId() {
        return userId;
    }

    /**
     * 用户名
     * 对应Python: username: str
     */
    private String username;

    /**
     * 邮箱地址
     * 对应Python: email: str
     */
    private String email;

    /**
     * 昵称
     * 对应Python: nickname: str
     */
    private String nickname;

    /**
     * 手机号
     * 对应Python: phone: str
     */
    private String phone;

    /**
     * 密码哈希
     * 对应Python: password_hash: str
     */
    private String passwordHash;

    /**
     * 头像URL
     * 对应Python: avatar: str
     */
    private String avatar;

    /**
     * 是否为管理员
     * 对应Python: is_admin: bool
     */
    private Boolean isAdmin;

    /**
     * 创建时间
     * 对应Python: created_at: datetime
     */
    private LocalDateTime createdAt;

    /**
     * 检查用户是否可以访问指定工具
     * 对应Python: can_access_tool(tool_id: str) -> bool
     *
     * 业务规则：
     * - 管理员可以访问所有工具
     * - 普通用户当前可以访问所有工具（临时实现）
     *   TODO: 后续需要实现基于用户角色和工具可见性的权限控制
     *
     * @param toolId 工具ID
     * @return true-可以访问，false-不可以访问
     */
    public boolean canAccessTool(String toolId) {
        // 管理员可以访问所有工具
        if (Boolean.TRUE.equals(isAdmin)) {
            return true;
        }

        // TODO: 实现基于用户角色的权限控制
        // 当前临时实现：所有普通用户可以访问所有工具
        return true;
    }

    /**
     * 检查是否为付费用户
     * 对应Python: is_premium_user() -> bool
     *
     * @return true-付费用户，false-免费用户
     */
    public boolean isPremiumUser() {
        // TODO: 实现付费用户逻辑
        return false;
    }

    /**
     * 创建新用户（工厂方法）
     * 对应Python: @classmethod create_new(cls, username, email, created_at) -> User
     *
     * @param username 用户名
     * @param email 邮箱
     * @param createdAt 创建时间（可选，默认使用当前时间）
     * @return 新用户实例
     */
    public static User createNew(String username, String email, LocalDateTime createdAt) {
        User user = new User();
        user.userId = "0"; // 数据库生成UUID
        user.username = username;
        user.email = email;
        user.isAdmin = false;
        user.createdAt = createdAt != null ? createdAt : LocalDateTime.now();
        return user;
    }

    /**
     * 生成用户ID（UUID）
     *
     * @return UUID字符串
     */
    public static String generateUserId() {
        return UUID.randomUUID().toString();
    }
}
