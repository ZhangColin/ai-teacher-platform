package com.platform.interfaces.rest.dto.admin;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 创建工具分类请求
 *
 * 对应Python: CreateToolCategoryRequest
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CreateToolCategoryRequest {
    @NotBlank(message = "分类名称不能为空")
    private String name;

    private Integer order;
}
