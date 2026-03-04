package com.aieducenter.studio.interfaces.rest.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 管理员工具DTO
 *
 * 对应Python: AdminCommonToolListItem
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AdminToolDTO {
    /** 工具ID */
    private String toolId;

    /** 工具名称 */
    private String name;

    /** 工具描述 */
    private String description;

    /** 分类ID */
    private String categoryId;

    /** 分类名称 */
    private String categoryName;

    /** 图标 */
    private String icon;

    /** 类型: built-in, html, media */
    private String type;

    /** 排序 */
    private Integer order;

    /** 是否可见 */
    private Boolean visible;

    /** HTML路径（仅HTML工具） */
    private String htmlPath;

    /** 系统提示词（仅内置工具） */
    private String systemPrompt;

    /** 模型配置（仅内置工具） */
    private String modelConfig;
}
