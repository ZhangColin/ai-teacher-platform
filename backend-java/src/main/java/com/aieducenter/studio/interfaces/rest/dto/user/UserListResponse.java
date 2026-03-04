package com.aieducenter.studio.interfaces.rest.dto.user;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 用户列表响应
 *
 * 对应Python: UserListResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserListResponse {
    private List<UserDTO> users;
    private Integer total;
    private Integer page;
    private Integer pageSize;
}
