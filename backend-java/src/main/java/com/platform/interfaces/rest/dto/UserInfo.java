package com.platform.interfaces.rest.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 用户信息DTO
 *
 * 对应Python: backend/src/models.py中的UserInfo
 *
 * @author AI Teacher Platform
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserInfo {

    /**
     * 用户ID
     * 对应Python: user_id: str
     */
    private String userId;

    /**
     * 用户名
     * 对应Python: username: str
     */
    private String username;

    /**
     * 昵称
     * 对应Python: nickname: Optional[str]
     */
    private String nickname;

    /**
     * 邮箱
     * 对应Python: email: Optional[str]
     */
    private String email;

    /**
     * 手机号
     * 对应Python: phone: Optional[str]
     */
    private String phone;

    /**
     * 头像URL
     * 对应Python: avatar: Optional[str]
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
}
