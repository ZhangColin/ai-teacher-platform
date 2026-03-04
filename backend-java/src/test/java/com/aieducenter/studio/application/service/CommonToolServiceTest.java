package com.platform.application.service;

import com.platform.domain.tool.CommonToolType;
import com.platform.infrastructure.persistence.jpa.CommonToolEntity;
import com.platform.infrastructure.persistence.jpa.CommonToolJpaRepository;
import com.platform.infrastructure.persistence.jpa.ToolCategoryEntity;
import com.platform.infrastructure.persistence.jpa.ToolCategoryJpaRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

/**
 * CommonToolService单元测试
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("CommonToolService单元测试")
class CommonToolServiceTest {

    @Mock
    private ToolCategoryJpaRepository categoryRepository;

    @Mock
    private CommonToolJpaRepository toolRepository;

    @InjectMocks
    private CommonToolService commonToolService;

    @Test
    @DisplayName("获取分类和工具 - 成功")
    void getCategoriesWithTools_Success() {
        // Given
        ToolCategoryEntity category = new ToolCategoryEntity();
        category.setId("cat-1");
        category.setName("测试分类");
        category.setOrder(1);

        CommonToolEntity tool = new CommonToolEntity();
        tool.setId("tool-1");
        tool.setName("测试工具");
        tool.setCategoryId("cat-1");
        tool.setType(CommonToolType.BUILT_IN);
        tool.setVisible(true);
        tool.setOrder(1);

        when(categoryRepository.findAllByOrderByOrderAsc()).thenReturn(List.of(category));
        when(toolRepository.findByCategoryIdAndVisibleTrueOrderByOrderAsc("cat-1"))
            .thenReturn(List.of(tool));

        // When
        var result = commonToolService.getCategoriesWithTools();

        // Then
        assertEquals(1, result.size());
        assertEquals("测试分类", result.get(0).getName());
        assertEquals(1, result.get(0).getTools().size());
    }
}
