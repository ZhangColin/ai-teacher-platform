package com.platform.application.service;

import com.platform.domain.artifact.Artifact;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * ArtifactParser单元测试
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("ArtifactParser单元测试")
class ArtifactParserTest {

    @InjectMocks
    private ArtifactParser artifactParser;

    @Test
    @DisplayName("检测HTML内容 - 识别为HTML")
    void detectLanguageByContent_HtmlTags_ReturnsHtml() {
        // Given
        String htmlContent = "<html><body><div>Hello</div></body></html>";

        // When
        String result = artifactParser.detectLanguageByContent(htmlContent);

        // Then
        assertThat(result).isEqualTo("html");
    }

    @Test
    @DisplayName("检测SVG内容 - 识别为SVG")
    void detectLanguageByContent_SvgTags_ReturnsSvg() {
        // Given
        String svgContent = "<svg xmlns=\"http://www.w3.org/2000/svg\"><circle cx=\"50\" cy=\"50\" r=\"40\"/></svg>";

        // When
        String result = artifactParser.detectLanguageByContent(svgContent);

        // Then
        assertThat(result).isEqualTo("svg");
    }

    @Test
    @DisplayName("检测Markdown内容 - 标题语法")
    void detectLanguageByContent_MarkdownHeaders_ReturnsMarkdown() {
        // Given
        String markdownContent = "# 标题\n\n这是内容";

        // When
        String result = artifactParser.detectLanguageByContent(markdownContent);

        // Then
        assertThat(result).isEqualTo("markdown");
    }

    @Test
    @DisplayName("检测Markdown内容 - 列表语法")
    void detectLanguageByContent_MarkdownLists_ReturnsMarkdown() {
        // Given
        String markdownContent = "- 项目1\n- 项目2\n- 项目3";

        // When
        String result = artifactParser.detectLanguageByContent(markdownContent);

        // Then
        assertThat(result).isEqualTo("markdown");
    }

    @Test
    @DisplayName("检测Markdown内容 - 加粗语法")
    void detectLanguageByContent_MarkdownBold_ReturnsMarkdown() {
        // Given
        String markdownContent = "这是**加粗**文本和__斜体__文本";

        // When
        String result = artifactParser.detectLanguageByContent(markdownContent);

        // Then
        assertThat(result).isEqualTo("markdown");
    }

    @Test
    @DisplayName("检测Markdown内容 - 链接语法")
    void detectLanguageByContent_MarkdownLinks_ReturnsMarkdown() {
        // Given
        String markdownContent = "查看[链接](https://example.com)";

        // When
        String result = artifactParser.detectLanguageByContent(markdownContent);

        // Then
        assertThat(result).isEqualTo("markdown");
    }

    @Test
    @DisplayName("检测Markdown内容 - 代码块语法")
    void detectLanguageByContent_MarkdownCodeBlocks_ReturnsMarkdown() {
        // Given
        String markdownContent = "这是`inline code`和```\ncode block\n```";

        // When
        String result = artifactParser.detectLanguageByContent(markdownContent);

        // Then
        assertThat(result).isEqualTo("markdown");
    }

    @Test
    @DisplayName("检测纯文本 - 返回text")
    void detectLanguageByContent_PlainText_ReturnsText() {
        // Given
        String plainText = "这只是一段普通的纯文本，没有任何特殊标记。";

        // When
        String result = artifactParser.detectLanguageByContent(plainText);

        // Then
        assertThat(result).isEqualTo("text");
    }

    @Test
    @DisplayName("解析Markdown代码块 - HTML")
    void parseFromMarkdown_HtmlCodeBlock_ReturnsHtmlArtifact() {
        // Given
        String markdown = "```html\n<html><body>Hello</body></html>\n```";

        // When
        List<Artifact> result = artifactParser.parseFromMarkdown(markdown);

        // Then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getType()).isEqualTo("html");
        assertThat(result.get(0).getContent()).contains("<html>");
        assertThat(result.get(0).getLanguage()).isEqualTo("html");
    }

    @Test
    @DisplayName("解析Markdown代码块 - SVG")
    void parseFromMarkdown_SvgCodeBlock_ReturnsSvgArtifact() {
        // Given
        String markdown = "```svg\n<svg><circle/></svg>\n```";

        // When
        List<Artifact> result = artifactParser.parseFromMarkdown(markdown);

        // Then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getType()).isEqualTo("svg");
        assertThat(result.get(0).getContent()).contains("<svg>");
    }

    @Test
    @DisplayName("解析Markdown代码块 - Markdown")
    void parseFromMarkdown_MarkdownCodeBlock_ReturnsMarkdownArtifact() {
        // Given
        String markdown = "```markdown\n# 标题\n内容\n```";

        // When
        List<Artifact> result = artifactParser.parseFromMarkdown(markdown);

        // Then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getType()).isEqualTo("markdown");
        assertThat(result.get(0).getContent()).contains("# 标题");
    }

    @Test
    @DisplayName("解析多个代码块 - 正确提取")
    void parseFromMarkdown_MultipleCodeBlocks_ExtractsAll() {
        // Given
        String markdown = """
            ```html
            <div>HTML</div>
            ```

            ```svg
            <svg><circle/></svg>
            ```

            ```markdown
            # Markdown
            ```
            """;

        // When
        List<Artifact> result = artifactParser.parseFromMarkdown(markdown);

        // Then
        assertThat(result).hasSize(3);
        assertThat(result.get(0).getType()).isEqualTo("html");
        assertThat(result.get(1).getType()).isEqualTo("svg");
        assertThat(result.get(2).getType()).isEqualTo("markdown");
    }

    @Test
    @DisplayName("解析无语言标识的代码块 - 智能识别HTML")
    void parseFromMarkdown_NoLanguage_Html_ReturnsHtml() {
        // Given
        String markdown = "```\n<html><body>Hello</body></html>\n```";

        // When
        List<Artifact> result = artifactParser.parseFromMarkdown(markdown);

        // Then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getType()).isEqualTo("html");
    }

    @Test
    @DisplayName("解析无语言标识的代码块 - 智能识别SVG")
    void parseFromMarkdown_NoLanguage_Svg_ReturnsSvg() {
        // Given
        String markdown = "```\n<svg><circle/></svg>\n```";

        // When
        List<Artifact> result = artifactParser.parseFromMarkdown(markdown);

        // Then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getType()).isEqualTo("svg");
    }

    @Test
    @DisplayName("解析XML标识但内容为SVG - 识别为SVG")
    void parseFromMarkdown_XmlLanguage_SvgContent_ReturnsSvg() {
        // Given
        String markdown = "```xml\n<svg xmlns=\"http://www.w3.org/2000/svg\"><circle/></svg>\n```";

        // When
        List<Artifact> result = artifactParser.parseFromMarkdown(markdown);

        // Then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getType()).isEqualTo("svg");
    }

    @Test
    @DisplayName("解析无代码块的文本 - 返回空列表")
    void parseFromMarkdown_NoCodeBlocks_ReturnsEmptyList() {
        // Given
        String markdown = "这是一段普通的文本，没有代码块。";

        // When
        List<Artifact> result = artifactParser.parseFromMarkdown(markdown);

        // Then
        assertThat(result).isEmpty();
    }

    @Test
    @DisplayName("解析空内容 - 返回空列表")
    void parseFromMarkdown_EmptyContent_ReturnsEmptyList() {
        // When
        List<Artifact> result = artifactParser.parseFromMarkdown("");

        // Then
        assertThat(result).isEmpty();
    }

    @Test
    @DisplayName("检测HTML - button标签")
    void detectLanguageByContent_ButtonTag_ReturnsHtml() {
        // Given
        String content = "<button>点击</button>";

        // When
        String result = artifactParser.detectLanguageByContent(content);

        // Then
        assertThat(result).isEqualTo("html");
    }

    @Test
    @DisplayName("检测HTML - input标签")
    void detectLanguageByContent_InputTag_ReturnsHtml() {
        // Given
        String content = "<input type=\"text\" />";

        // When
        String result = artifactParser.detectLanguageByContent(content);

        // Then
        assertThat(result).isEqualTo("html");
    }

    @Test
    @DisplayName("检测SVG - polygon标签")
    void detectLanguageByContent_PolygonTag_ReturnsSvg() {
        // Given
        String content = "<polygon points=\"100,10 40,198 190,78\" />";

        // When
        String result = artifactParser.detectLanguageByContent(content);

        // Then
        assertThat(result).isEqualTo("svg");
    }

    @Test
    @DisplayName("解析代码块 - 去除前后空格")
    void parseFromMarkdown_TrimsWhitespace() {
        // Given
        String markdown = "```html\n   <html>\n   </html>   \n```";

        // When
        List<Artifact> result = artifactParser.parseFromMarkdown(markdown);

        // Then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getContent()).doesNotStartWith("   ");
    }
}
