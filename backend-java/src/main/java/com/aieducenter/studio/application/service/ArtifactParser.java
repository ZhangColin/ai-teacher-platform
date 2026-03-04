package com.aieducenter.studio.application.service;

import com.aieducenter.studio.domain.artifact.Artifact;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 成果物解析服务
 *
 * 对应Python: backend/src/services/artifact_parser.py
 * 从Markdown中提取代码块生成成果物
 *
 * @author AI Teacher Platform
 */
@Service
public class ArtifactParser {

    private static final Logger logger = LoggerFactory.getLogger(ArtifactParser.class);

    /**
     * Markdown代码块正则表达式
     * 对应Python: CODE_BLOCK_PATTERN
     */
    private static final Pattern CODE_BLOCK_PATTERN = Pattern.compile(
        "```(\\w+)?\\n([\\s\\S]*?)```",
        Pattern.DOTALL
    );

    /**
     * 根据内容特征智能识别代码块类型
     *
     * 对应Python: def detect_language_by_content(...)
     */
    public String detectLanguageByContent(String content) {
        String contentLower = content.toLowerCase().strip();

        // HTML特征检测
        String[] htmlTags = {"<html", "<div", "<script", "<style", "<body", "<head",
                            "<title", "<meta", "<link", "<button", "<input", "<form"};
        for (String tag : htmlTags) {
            if (contentLower.contains(tag)) {
                return "html";
            }
        }

        // SVG特征检测
        String[] svgTags = {"<svg", "<path", "<circle", "<rect", "<line", "<polygon",
                            "<polyline", "<ellipse", "<text", "<g ", "<defs", "<use"};
        for (String tag : svgTags) {
            if (contentLower.contains(tag)) {
                return "svg";
            }
        }

        // Markdown特征检测
        if (Pattern.compile("^#+\\s+", Pattern.MULTILINE).matcher(content).find()) {
            return "markdown";
        }

        if (Pattern.compile("^\\s*[-*+]\\s+", Pattern.MULTILINE).matcher(content).find()) {
            return "markdown";
        }

        if (Pattern.compile("\\*\\*.*?\\*\\*|__.*?__|\\*.*?\\*|_.*?_").matcher(content).find()) {
            return "markdown";
        }

        if (Pattern.compile("\\[.*?\\]\\(.*?\\)").matcher(content).find()) {
            return "markdown";
        }

        if (content.contains("`") || content.contains("```")) {
            return "markdown";
        }

        return "text";
    }

    /**
     * 从Markdown文本中提取代码块
     *
     * 对应Python: def parse_from_markdown(...)
     *
     * @param content Markdown文本内容
     * @return 成果物列表
     */
    public List<Artifact> parseFromMarkdown(String content) {
        List<Artifact> artifacts = new ArrayList<>();
        Matcher matcher = CODE_BLOCK_PATTERN.matcher(content);

        while (matcher.find()) {
            String language = matcher.group(1);
            String codeContent = matcher.group(2).strip();

            // 处理语言标识
            if (language != null && !language.trim().isEmpty()) {
                language = language.trim();
                // 如果声明的是xml但内容是SVG，应该识别为svg
                if ("xml".equalsIgnoreCase(language)) {
                    String detected = detectLanguageByContent(codeContent);
                    if ("svg".equals(detected)) {
                        language = "svg";
                    }
                }
            } else {
                // 没有显式声明，使用智能识别
                language = detectLanguageByContent(codeContent);
            }

            // 创建Artifact对象
            Artifact artifact = new Artifact();
            artifact.setType(language);
            artifact.setContent(codeContent);
            artifact.setLanguage(language);
            artifact.setTimestamp(LocalDateTime.now());

            artifacts.add(artifact);
        }

        logger.debug("解析成果物完成，提取到 {} 个代码块", artifacts.size());
        return artifacts;
    }
}
