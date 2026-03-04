package com.aieducenter.studio.interfaces.rest.dto.user;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 更新用户响应
 *
 * 对应Python: UpdateUserResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UpdateUserResponse {
    private UserDTO user;
}
