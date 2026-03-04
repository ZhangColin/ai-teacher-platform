package com.platform.interfaces.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 工具配置DTO
 *
 * 对应Python: backend/src/models.py Tool
 * 对应配置: configs/tools/{toolset_id}/*.yaml
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ToolDTO {

    /**
     * 工具唯一标识符
     * 对应Python: tool_id: str
     */
    private String toolId;

    /**
     * 工具名称
     * 对应Python: name: str
     */
    private String name;

    /**
     * 工具描述
     * 对应Python: description: Optional[str]
     */
    private String description;

    /**
     * 系统提示词
     * 对应Python: system_prompt: Optional[str]
     */
    private String systemPrompt;

    /**
     * 分类名称
     * 对应Python: category: str
     */
    private String category;

    /**
     * 图标标识
     * 对应Python: icon: Optional[str]
     */
    private String icon;

    /**
     * 是否在工具选择器中显示
     * 对应Python: visible: bool
     */
    private Boolean visible;

    /**
     * 工具类型：normal 或 placeholder
     * 对应Python: type: Literal["normal", "placeholder"]
     */
    private String type;

    /**
     * 欢迎语
     * 对应Python: welcome_message: str
     */
    private String welcomeMessage;

    /**
     * 排序顺序（数字越小越靠前）
     * 对应Python: order: int
     */
    private Integer order;

    /**
     * 所属工具集ID
     * 对应Python: toolset_id: str
     */
    private String toolsetId;

    /**
     * 系统提示词文件路径
     * 对应Python: system_prompt_file: Optional[str]
     */
    private String systemPromptFile;

    /**
     * 使用的AI模型（格式：provider:model_name）
     * 对应Python: model: Optional[str]
     * 示例: "deepseek:deepseek-chat"
     */
    private String model;

    /**
     * 内容类型：text 或 multimodal
     * 对应Python: content_type: Literal["text", "multimodal"]
     */
    private String contentType;

    /**
     * 媒体类型（仅当content_type=multimodal时有效）
     * 对应Python: media_type: Optional[Literal["image", "audio", "video"]]
     */
    private String mediaType;

    /**
     * 验证工具配置是否完整有效
     * 对应Python: validate() -> bool
     */
    public boolean validate() {
        if (toolId == null || toolId.isBlank()) {
            return false;
        }
        if (name == null || name.isBlank()) {
            return false;
        }
        if (category == null || category.isBlank()) {
            return false;
        }
        if (welcomeMessage == null || welcomeMessage.isBlank()) {
            return false;
        }
        // system_prompt 和 system_prompt_file 至少有一个
        if ((systemPrompt == null || systemPrompt.isBlank()) &&
            (systemPromptFile == null || systemPromptFile.isBlank())) {
            return false;
        }
        // 如果是多模态工具，必须指定media_type
        if ("multimodal".equals(contentType) && (mediaType == null || mediaType.isBlank())) {
            return false;
        }
        return true;
    }
}
