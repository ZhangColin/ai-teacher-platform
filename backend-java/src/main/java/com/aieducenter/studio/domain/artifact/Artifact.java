package com.platform.domain.artifact;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 成果物实体（占位实现）
 *
 * 对应Python: backend/src/domain/entities/artifact.py
 * 完整实现将在后续Task中完成
 *
 * @author AI Teacher Platform
 */
@Data
public class Artifact {

    private String id;
    private String type; // "html", "svg", "markdown"
    private String content;
    private String language;
    private LocalDateTime timestamp;
}
