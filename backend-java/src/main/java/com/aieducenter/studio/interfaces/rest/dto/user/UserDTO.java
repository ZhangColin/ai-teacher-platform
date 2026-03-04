package com.aieducenter.studio.interfaces.rest.dto.user;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 用户DTO
 *
 * 对应Python: UserListItem
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserDTO {
    private String userId;
    private String username;
    private String nickname;
    private String email;
    private String phone;
    private String avatar;
    private Boolean isAdmin;
    private LocalDateTime createdAt;
}
