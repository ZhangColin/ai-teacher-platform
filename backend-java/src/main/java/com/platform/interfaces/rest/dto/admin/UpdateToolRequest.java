package com.platform.interfaces.rest.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 更新工具请求
 *
 * 对应Python: UpdateToolRequest
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UpdateToolRequest {
    private String name;
    private String description;
    private String categoryId;
    private String icon;
    private Integer order;
    private Boolean visible;
    private String systemPrompt;
    private String modelConfig;
}
