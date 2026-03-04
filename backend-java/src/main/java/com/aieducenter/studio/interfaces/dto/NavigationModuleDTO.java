package com.aieducenter.studio.interfaces.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 导航模块配置DTO
 *
 * 对应Python: backend/src/models.py NavigationModule
 * 对应配置: configs/navigation.yaml
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NavigationModuleDTO {

    /**
     * 模块显示名称
     * 对应Python: name: str
     */
    private String name;

    /**
     * 模块类型：toolset=工具集模块，page=独立页面
     * 对应Python: type: Literal["toolset", "page"]
     */
    private String type;

    /**
     * 配置来源（type=toolset时使用，工具集配置目录路径）
     * 对应Python: config_source: Optional[str]
     * 示例: "tools/ai_tools"
     */
    private String configSource;

    /**
     * 页面路径（type=page时使用，前端路由路径）
     * 对应Python: page_path: Optional[str]
     * 示例: "/common-tools"
     */
    private String pagePath;

    /**
     * 图标标识（可选）
     * 对应Python: icon: Optional[str]
     */
    private String icon;

    /**
     * 排序顺序（数字越小越靠前）
     * 对应Python: order: int
     */
    private Integer order;

    /**
     * 验证导航模块配置是否有效
     * 对应Python: validate() -> bool
     */
    public boolean validate() {
        if (name == null || name.isBlank()) {
            return false;
        }
        if (type == null || type.isBlank()) {
            return false;
        }
        // toolset 类型必须有 config_source
        if ("toolset".equals(type) && (configSource == null || configSource.isBlank())) {
            return false;
        }
        // page 类型必须有 page_path
        if ("page".equals(type) && (pagePath == null || pagePath.isBlank())) {
            return false;
        }
        return true;
    }
}
