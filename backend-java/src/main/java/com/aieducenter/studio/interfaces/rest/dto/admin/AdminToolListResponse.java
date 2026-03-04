package com.platform.interfaces.rest.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 管理员工具列表响应
 *
 * 对应Python: AdminCommonToolListResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AdminToolListResponse {
    /** 工具列表 */
    private List<AdminToolDTO> tools;

    /** 总数 */
    private Integer total;

    /** 当前页 */
    private Integer page;

    /** 每页大小 */
    private Integer pageSize;
}
