package com.platform.interfaces.rest.dto.media;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 媒体生成响应
 *
 * 对应Python: MediaGenerateResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MediaGenerateResponse {
    private String mediaId;
    private String mediaType;
    private String url;
    private String status;
}
