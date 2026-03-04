package com.platform.interfaces.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 分类工具聚合DTO
 *
 * 对应Python: backend/src/services/tool_service.py group_by_category()
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CategoryDTO {

    /**
     * 分类名称
     */
    private String name;

    /**
     * 分类图标
     */
    private String icon;

    /**
     * 排序顺序
     */
    private Integer order;

    /**
     * 该分类下的工具列表（已排序）
     */
    private List<ToolDTO> tools;
}
