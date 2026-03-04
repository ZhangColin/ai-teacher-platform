package com.platform.infrastructure.security;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

import java.util.Collection;
import java.util.Collections;

/**
 * 用户认证主体
 *
 * 对应Python: backend/src/models.py中的User模型
 * 表示Spring Security中的已认证用户
 *
 * @author AI Teacher Platform
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserPrincipal {

    /**
     * 构造函数（仅用户ID）
     */
    public UserPrincipal(String userId) {
        this.userId = userId;
    }

    /**
     * 用户ID
     * 对应Python: user.user_id
     */
    private String userId;

    /**
     * 用户名
     * 对应Python: user.username
     */
    private String username;

    /**
     * 邮箱
     * 对应Python: user.email
     */
    private String email;

    /**
     * 是否为管理员
     * 对应Python: user.is_admin
     */
    private Boolean isAdmin;

    /**
     * 获取权限
     *
     * @return 权限集合
     */
    public Collection<SimpleGrantedAuthority> getAuthorities() {
        if (Boolean.TRUE.equals(isAdmin)) {
            return Collections.singletonList(new SimpleGrantedAuthority("ROLE_ADMIN"));
        }
        return Collections.singletonList(new SimpleGrantedAuthority("ROLE_USER"));
    }
}
