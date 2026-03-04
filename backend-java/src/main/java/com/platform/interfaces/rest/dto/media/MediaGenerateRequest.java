package com.platform.interfaces.rest.dto.media;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 媒体生成请求
 *
 * 对应Python: MediaGenerateRequest
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MediaGenerateRequest {
    private String prompt;
    private String mediaType;  // "image", "video", etc.
}
