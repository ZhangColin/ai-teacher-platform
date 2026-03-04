package com.platform.interfaces.rest.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 成果物DTO
 *
 * 对应Python: Artifact
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Artifact {
    private String artifactId;
    private String messageId;
    private String type;  // "html", "svg", "markdown"
    private String title;
    private String content;
}
