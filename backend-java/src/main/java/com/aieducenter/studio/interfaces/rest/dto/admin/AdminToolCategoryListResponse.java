package com.aieducenter.studio.interfaces.rest.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 管理员工具分类列表响应
 *
 * 对应Python: AdminToolCategoryListResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AdminToolCategoryListResponse {
    /** 分类列表 */
    private List<AdminToolCategoryDTO> categories;

    /** 总数 */
    private Integer total;
}
