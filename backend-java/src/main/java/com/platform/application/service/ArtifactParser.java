package com.platform.application.service;

import com.platform.domain.artifact.Artifact;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 成果物解析器（占位符）
 *
 * 对应Python: backend/src/services/artifact_parser.py
 * TODO: 完整实现
 *
 * @author AI Teacher Platform
 */
@Service
public class ArtifactParser {

    /**
     * 从Markdown中解析成果物
     *
     * @param markdown Markdown文本
     * @return 成果物列表
     */
    public List<Artifact> parseFromMarkdown(String markdown) {
        // TODO: 实现成果物解析逻辑
        return List.of();
    }
}
