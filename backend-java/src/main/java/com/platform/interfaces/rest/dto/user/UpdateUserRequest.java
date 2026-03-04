package com.platform.interfaces.rest.dto.user;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 更新用户请求
 *
 * 对应Python: UpdateUserRequest
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UpdateUserRequest {
    private String username;
    private String nickname;
    private String email;
    private String phone;
    private Boolean isAdmin;
}
