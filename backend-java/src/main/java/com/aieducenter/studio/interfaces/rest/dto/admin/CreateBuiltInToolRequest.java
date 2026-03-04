package com.platform.interfaces.rest.dto.admin;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 创建内置工具请求
 *
 * 对应Python: CreateBuiltInToolRequest
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CreateBuiltInToolRequest {
    @NotBlank(message = "工具名称不能为空")
    private String name;

    @NotBlank(message = "工具描述不能为空")
    private String description;

    @NotBlank(message = "分类ID不能为空")
    private String categoryId;

    private String icon;

    private Integer order;

    private Boolean visible;

    private String systemPrompt;

    private String modelConfig;
}
