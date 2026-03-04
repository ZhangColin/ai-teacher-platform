package com.platform.interfaces.rest.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 创建工具分类响应
 *
 * 对应Python: CreateToolCategoryResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CreateToolCategoryResponse {
    private AdminToolCategoryDTO category;
}
