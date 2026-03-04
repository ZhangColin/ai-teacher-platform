package com.aieducenter.studio.interfaces.rest.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 更新工具分类响应
 *
 * 对应Python: UpdateToolCategoryResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UpdateToolCategoryResponse {
    private AdminToolCategoryDTO category;
}
