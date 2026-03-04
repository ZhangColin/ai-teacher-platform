package com.platform.interfaces.rest.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 管理员工具分类DTO
 *
 * 对应Python: AdminToolCategoryListItem
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AdminToolCategoryDTO {
    /** 分类ID */
    private String categoryId;

    /** 分类名称 */
    private String name;

    /** 排序 */
    private Integer order;

    /** 该分类下的工具数量 */
    private Integer toolCount;
}
