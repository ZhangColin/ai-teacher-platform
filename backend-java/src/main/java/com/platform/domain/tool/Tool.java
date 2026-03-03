package com.platform.domain.tool;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 工具领域实体
 *
 * 对应Python: backend/src/models.py中的Tool
 *
 * @author AI Teacher Platform
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Tool {

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
     * 工具类型（normal/placeholder）
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
     */
    private String model;

    /**
     * 内容类型（text/multimodal）
     * 对应Python: content_type: Literal["text", "multimodal"]
     */
    private String contentType;

    /**
     * 媒体类型（image/audio/video）
     * 对应Python: media_type: Optional[Literal["image", "audio", "video"]]
     */
    private String mediaType;

    /**
     * 验证工具配置是否完整有效
     *
     * 对应Python: def validate() -> bool
     *
     * @return true-有效，false-无效
     */
    public boolean validate() {
        if (toolId == null || toolId.trim().isEmpty()) {
            return false;
        }
        if (name == null || name.trim().isEmpty()) {
            return false;
        }
        if (category == null || category.trim().isEmpty()) {
            return false;
        }
        if (welcomeMessage == null || welcomeMessage.trim().isEmpty()) {
            return false;
        }
        // system_prompt 和 system_prompt_file 至少有一个
        if ((systemPrompt == null || systemPrompt.trim().isEmpty()) &&
            (systemPromptFile == null || systemPromptFile.trim().isEmpty())) {
            return false;
        }
        // 如果是多模态工具，必须指定media_type
        if ("multimodal".equals(contentType) && (mediaType == null || mediaType.trim().isEmpty())) {
            return false;
        }
        return true;
    }
}
