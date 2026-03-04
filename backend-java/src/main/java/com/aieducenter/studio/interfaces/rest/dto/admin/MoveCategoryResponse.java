package com.platform.interfaces.rest.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 移动分类响应
 *
 * 对应Python: MoveCategoryResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MoveCategoryResponse {
    private String message;
    private AdminToolCategoryDTO category;
}
