package com.aieducenter.studio.domain.artifact;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Artifact领域实体单元测试
 */
@DisplayName("Artifact领域实体单元测试")
class ArtifactTest {

    @Test
    @DisplayName("Lombok @Data注解 - Getter和Setter工作正常")
    void lombokData_GettersAndSetters_Work() {
        // Given
        Artifact artifact = new Artifact();
        LocalDateTime now = LocalDateTime.now();

        // When
        artifact.setId("artifact-123");
        artifact.setType("html");
        artifact.setContent("<html>...</html>");
        artifact.setLanguage("html");
        artifact.setTimestamp(now);

        // Then
        assertThat(artifact.getId()).isEqualTo("artifact-123");
        assertThat(artifact.getType()).isEqualTo("html");
        assertThat(artifact.getContent()).isEqualTo("<html>...</html>");
        assertThat(artifact.getLanguage()).isEqualTo("html");
        assertThat(artifact.getTimestamp()).isEqualTo(now);
    }

    @Test
    @DisplayName("创建HTML类型成果物")
    void artifact_HtmlType() {
        // Given
        Artifact artifact = new Artifact();

        // When
        artifact.setType("html");
        artifact.setContent("<html><body>Hello</body></html>");
        artifact.setLanguage("html");

        // Then
        assertThat(artifact.getType()).isEqualTo("html");
        assertThat(artifact.getLanguage()).isEqualTo("html");
        assertThat(artifact.getContent()).contains("<html>");
    }

    @Test
    @DisplayName("创建SVG类型成果物")
    void artifact_SvgType() {
        // Given
        Artifact artifact = new Artifact();

        // When
        artifact.setType("svg");
        artifact.setContent("<svg><circle/></svg>");
        artifact.setLanguage("svg");

        // Then
        assertThat(artifact.getType()).isEqualTo("svg");
        assertThat(artifact.getLanguage()).isEqualTo("svg");
        assertThat(artifact.getContent()).contains("<svg>");
    }

    @Test
    @DisplayName("创建Markdown类型成果物")
    void artifact_MarkdownType() {
        // Given
        Artifact artifact = new Artifact();

        // When
        artifact.setType("markdown");
        artifact.setContent("# 标题\n内容");
        artifact.setLanguage("markdown");

        // Then
        assertThat(artifact.getType()).isEqualTo("markdown");
        assertThat(artifact.getLanguage()).isEqualTo("markdown");
        assertThat(artifact.getContent()).contains("# 标题");
    }

    @Test
    @DisplayName("创建文本类型成果物")
    void artifact_TextType() {
        // Given
        Artifact artifact = new Artifact();

        // When
        artifact.setType("text");
        artifact.setContent("纯文本内容");
        artifact.setLanguage("text");

        // Then
        assertThat(artifact.getType()).isEqualTo("text");
        assertThat(artifact.getLanguage()).isEqualTo("text");
        assertThat(artifact.getContent()).isEqualTo("纯文本内容");
    }

    @Test
    @DisplayName("字段可为null")
    void artifact_FieldsCanBeNull() {
        // Given
        Artifact artifact = new Artifact();

        // When - 不设置任何字段

        // Then
        assertThat(artifact.getId()).isNull();
        assertThat(artifact.getType()).isNull();
        assertThat(artifact.getContent()).isNull();
        assertThat(artifact.getLanguage()).isNull();
        assertThat(artifact.getTimestamp()).isNull();
    }

    @Test
    @DisplayName("时间戳 - 可设置当前时间")
    void timestamp_CanBeSetToNow() {
        // Given
        Artifact artifact = new Artifact();
        LocalDateTime now = LocalDateTime.now();

        // When
        artifact.setTimestamp(now);

        // Then
        assertThat(artifact.getTimestamp()).isEqualTo(now);
    }

    @Test
    @DisplayName("内容 - 可为长文本")
    void content_LongText() {
        // Given
        Artifact artifact = new Artifact();
        String longContent = "这是一个非常长的内容".repeat(100);

        // When
        artifact.setContent(longContent);

        // Then
        assertThat(artifact.getContent()).isEqualTo(longContent);
        assertThat(artifact.getContent().length()).isGreaterThan(1000);
    }

    @Test
    @DisplayName("内容 - 可包含特殊字符")
    void content_SpecialCharacters() {
        // Given
        Artifact artifact = new Artifact();
        String specialContent = "内容包含：特殊字符 <>&\"' \n\t 换行和制表符";

        // When
        artifact.setContent(specialContent);

        // Then
        assertThat(artifact.getContent()).isEqualTo(specialContent);
        assertThat(artifact.getContent()).contains("<>&\"'");
        assertThat(artifact.getContent()).contains("\n\t");
    }

    @Test
    @DisplayName("Lombok toString - 包含所有字段")
    void lombokToString_ContainsAllFields() {
        // Given
        Artifact artifact = new Artifact();
        artifact.setId("artifact-123");
        artifact.setType("html");
        artifact.setContent("内容");

        // When
        String str = artifact.toString();

        // Then
        assertThat(str).contains("artifact-123");
        assertThat(str).contains("html");
        assertThat(str).contains("内容");
    }

    @Test
    @DisplayName("Lombok equals - 相同字段的对象相等")
    void lombokEquals_SameFields_AreEqual() {
        // Given
        LocalDateTime now = LocalDateTime.now();

        Artifact artifact1 = new Artifact();
        artifact1.setId("artifact-123");
        artifact1.setType("html");
        artifact1.setContent("内容");
        artifact1.setLanguage("html");
        artifact1.setTimestamp(now);

        Artifact artifact2 = new Artifact();
        artifact2.setId("artifact-123");
        artifact2.setType("html");
        artifact2.setContent("内容");
        artifact2.setLanguage("html");
        artifact2.setTimestamp(now);

        // Then
        assertThat(artifact1).isEqualTo(artifact2);
    }

    @Test
    @DisplayName("Lombok hashCode - 相同字段的对象hashCode相同")
    void lombokHashCode_SameFields_SameHashCode() {
        // Given
        LocalDateTime now = LocalDateTime.now();

        Artifact artifact1 = new Artifact();
        artifact1.setId("artifact-123");
        artifact1.setType("html");
        artifact1.setContent("内容");
        artifact1.setLanguage("html");
        artifact1.setTimestamp(now);

        Artifact artifact2 = new Artifact();
        artifact2.setId("artifact-123");
        artifact2.setType("html");
        artifact2.setContent("内容");
        artifact2.setLanguage("html");
        artifact2.setTimestamp(now);

        // Then
        assertThat(artifact1.hashCode()).isEqualTo(artifact2.hashCode());
    }

    @Test
    @DisplayName("ID - 可为UUID格式")
    void id_CanBeUUIDFormat() {
        // Given
        Artifact artifact = new Artifact();
        String uuid = "550e8400-e29b-41d4-a716-446655440000";

        // When
        artifact.setId(uuid);

        // Then
        assertThat(artifact.getId()).isEqualTo(uuid);
    }

    @Test
    @DisplayName("空内容 - 可设置")
    void content_EmptyString() {
        // Given
        Artifact artifact = new Artifact();

        // When
        artifact.setContent("");

        // Then
        assertThat(artifact.getContent()).isEqualTo("");
        assertThat(artifact.getContent().length()).isEqualTo(0);
    }
}
