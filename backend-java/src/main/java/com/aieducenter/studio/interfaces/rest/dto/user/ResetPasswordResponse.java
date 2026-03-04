package com.aieducenter.studio.interfaces.rest.dto.user;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 重置密码响应
 *
 * 对应Python: ResetPasswordResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ResetPasswordResponse {
    private String message;
    private String newPassword;
}
