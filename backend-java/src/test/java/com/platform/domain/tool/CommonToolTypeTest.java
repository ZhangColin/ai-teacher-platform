package com.platform.domain.tool;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * CommonToolType枚举单元测试
 */
@DisplayName("CommonToolType枚举单元测试")
class CommonToolTypeTest {

    @Test
    @DisplayName("枚举 - 包含2个值")
    void enum_ContainsTwoValues() {
        // When
        CommonToolType[] values = CommonToolType.values();

        // Then
        assertThat(values).hasSize(2);
        assertThat(values).containsExactly(CommonToolType.BUILT_IN, CommonToolType.HTML);
    }

    @Test
    @DisplayName("BUILT_IN - 内置工具类型")
    void builtIn_ToolType() {
        // When
        CommonToolType type = CommonToolType.BUILT_IN;

        // Then
        assertThat(type).isNotNull();
        assertThat(type).isEqualTo(CommonToolType.BUILT_IN);
    }

    @Test
    @DisplayName("HTML - HTML工具类型")
    void html_ToolType() {
        // When
        CommonToolType type = CommonToolType.HTML;

        // Then
        assertThat(type).isNotNull();
        assertThat(type).isEqualTo(CommonToolType.HTML);
    }

    @Test
    @DisplayName("枚举valueOf - BUILT_IN正常工作")
    void enumValueOf_BUILT_IN_Works() {
        // When
        CommonToolType type = CommonToolType.valueOf("BUILT_IN");

        // Then
        assertThat(type).isEqualTo(CommonToolType.BUILT_IN);
    }

    @Test
    @DisplayName("枚举valueOf - HTML正常工作")
    void enumValueOf_HTML_Works() {
        // When
        CommonToolType type = CommonToolType.valueOf("HTML");

        // Then
        assertThat(type).isEqualTo(CommonToolType.HTML);
    }

    @Test
    @DisplayName("枚举 - 两个值不相等")
    void enum_ValuesNotEqual() {
        // When
        CommonToolType builtIn = CommonToolType.BUILT_IN;
        CommonToolType html = CommonToolType.HTML;

        // Then
        assertThat(builtIn).isNotEqualTo(html);
        assertThat(html).isNotEqualTo(builtIn);
    }

    @Test
    @DisplayName("枚举name - BUILT_IN")
    void enumName_BUILT_IN() {
        // When
        String name = CommonToolType.BUILT_IN.name();

        // Then
        assertThat(name).isEqualTo("BUILT_IN");
    }

    @Test
    @DisplayName("枚举name - HTML")
    void enumName_HTML() {
        // When
        String name = CommonToolType.HTML.name();

        // Then
        assertThat(name).isEqualTo("HTML");
    }

    @Test
    @DisplayName("枚举ordinal - BUILT_IN为0")
    void enumOrdinal_BUILT_IN_IsZero() {
        // When
        int ordinal = CommonToolType.BUILT_IN.ordinal();

        // Then
        assertThat(ordinal).isEqualTo(0);
    }

    @Test
    @DisplayName("枚举ordinal - HTML为1")
    void enumOrdinal_HTML_IsOne() {
        // When
        int ordinal = CommonToolType.HTML.ordinal();

        // Then
        assertThat(ordinal).isEqualTo(1);
    }

    @Test
    @DisplayName("枚举 - 可用于switch语句")
    void enum_CanBeUsedInSwitch() {
        // Given
        CommonToolType type = CommonToolType.HTML;
        String result = "";

        // When
        switch (type) {
            case BUILT_IN:
                result = "built-in";
                break;
            case HTML:
                result = "html";
                break;
        }

        // Then
        assertThat(result).isEqualTo("html");
    }

    @Test
    @DisplayName("枚举values - 按声明顺序返回")
    void enumValues_ReturnedInDeclarationOrder() {
        // When
        CommonToolType[] values = CommonToolType.values();

        // Then
        assertThat(values[0]).isEqualTo(CommonToolType.BUILT_IN);
        assertThat(values[1]).isEqualTo(CommonToolType.HTML);
    }

    @Test
    @DisplayName("枚举 - 可用于集合比较")
    void enum_CanBeUsedInCollections() {
        // Given
        java.util.List<CommonToolType> types = java.util.Arrays.asList(CommonToolType.values());

        // When & Then
        assertThat(types).contains(CommonToolType.BUILT_IN);
        assertThat(types).contains(CommonToolType.HTML);
        assertThat(types).doesNotContain(null);
    }

    @Test
    @DisplayName("枚举 - 可以赋值为null")
    void enum_CanBeNull() {
        // Given
        CommonToolType type = null;

        // Then
        assertThat(type).isNull();
    }
}
