package com.platform.application.service;

import com.platform.infrastructure.persistence.jpa.WorkCategoryEntity;
import com.platform.infrastructure.persistence.jpa.WorkEntity;
import com.platform.infrastructure.persistence.jpa.WorkCategoryJpaRepository;
import com.platform.infrastructure.persistence.jpa.WorkJpaRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

/**
 * WorkService单元测试
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("WorkService单元测试")
class WorkServiceTest {

    @Mock
    private WorkCategoryJpaRepository categoryRepository;

    @Mock
    private WorkJpaRepository workRepository;

    @InjectMocks
    private WorkService workService;

    private WorkCategoryEntity category;
    private WorkEntity work1;
    private WorkEntity work2;

    @BeforeEach
    void setUp() {
        // 准备测试数据
        category = new WorkCategoryEntity();
        category.setId("category-1");
        category.setName("教案分类");
        category.setIcon("📚");
        category.setOrder(1);

        work1 = new WorkEntity();
        work1.setId("work-1");
        work1.setName("教案1");
        work1.setDescription("第一个教案");
        work1.setCategoryId("category-1");
        work1.setIcon("📄");
        work1.setHtmlPath("/works/work1.html");
        work1.setOrder(1);
        work1.setVisible(true);

        work2 = new WorkEntity();
        work2.setId("work-2");
        work2.setName("教案2");
        work2.setDescription("第二个教案");
        work2.setCategoryId("category-1");
        work2.setIcon("📝");
        work2.setHtmlPath("/works/work2.html");
        work2.setOrder(2);
        work2.setVisible(true);
    }

    @Test
    @DisplayName("获取分类和教案 - 成功")
    void getCategoriesWithWorks_Success() {
        // Given
        when(categoryRepository.findAllByOrderByOrderAsc())
            .thenReturn(List.of(category));
        when(workRepository.findByCategoryIdAndVisibleTrueOrderByOrderAsc("category-1"))
            .thenReturn(List.of(work1, work2));

        // When
        var result = workService.getCategoriesWithWorks();

        // Then
        assertThat(result).isNotNull();
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getId()).isEqualTo("category-1");
        assertThat(result.get(0).getName()).isEqualTo("教案分类");
        assertThat(result.get(0).getWorks()).hasSize(2);
        assertThat(result.get(0).getWorks().get(0).getName()).isEqualTo("教案1");
        assertThat(result.get(0).getWorks().get(1).getName()).isEqualTo("教案2");

        verify(categoryRepository).findAllByOrderByOrderAsc();
        verify(workRepository).findByCategoryIdAndVisibleTrueOrderByOrderAsc("category-1");
    }

    @Test
    @DisplayName("分类没有可见教案 - 被过滤掉")
    void getCategoriesWithWorks_NoVisibleWorks_FiltersOut() {
        // Given
        when(categoryRepository.findAllByOrderByOrderAsc())
            .thenReturn(List.of(category));
        when(workRepository.findByCategoryIdAndVisibleTrueOrderByOrderAsc("category-1"))
            .thenReturn(List.of());

        // When
        var result = workService.getCategoriesWithWorks();

        // Then
        assertThat(result).isNotNull();
        assertThat(result).isEmpty();

        verify(categoryRepository).findAllByOrderByOrderAsc();
        verify(workRepository).findByCategoryIdAndVisibleTrueOrderByOrderAsc("category-1");
    }

    @Test
    @DisplayName("多个分类 - 正确分组")
    void getCategoriesWithWorks_MultipleCategories_GroupsCorrectly() {
        // Given
        WorkCategoryEntity category2 = new WorkCategoryEntity();
        category2.setId("category-2");
        category2.setName("教案分类2");
        category2.setIcon("📖");
        category2.setOrder(2);

        WorkEntity work3 = new WorkEntity();
        work3.setId("work-3");
        work3.setName("教案3");
        work3.setCategoryId("category-2");
        work3.setVisible(true);

        when(categoryRepository.findAllByOrderByOrderAsc())
            .thenReturn(List.of(category, category2));
        when(workRepository.findByCategoryIdAndVisibleTrueOrderByOrderAsc("category-1"))
            .thenReturn(List.of(work1));
        when(workRepository.findByCategoryIdAndVisibleTrueOrderByOrderAsc("category-2"))
            .thenReturn(List.of(work3));

        // When
        var result = workService.getCategoriesWithWorks();

        // Then
        assertThat(result).hasSize(2);
        assertThat(result.get(0).getName()).isEqualTo("教案分类");
        assertThat(result.get(1).getName()).isEqualTo("教案分类2");
    }

    @Test
    @DisplayName("获取教案详情 - 成功")
    void getWorkDetail_Success() {
        // Given
        when(workRepository.findById("work-1"))
            .thenReturn(Optional.of(work1));

        // When
        var result = workService.getWorkDetail("work-1");

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getId()).isEqualTo("work-1");
        assertThat(result.getName()).isEqualTo("教案1");

        verify(workRepository).findById("work-1");
    }

    @Test
    @DisplayName("获取不可见的教案详情 - 返回null")
    void getWorkDetail_InvisibleWork_ReturnsNull() {
        // Given
        work1.setVisible(false);
        when(workRepository.findById("work-1"))
            .thenReturn(Optional.of(work1));

        // When
        var result = workService.getWorkDetail("work-1");

        // Then
        assertThat(result).isNull();

        verify(workRepository).findById("work-1");
    }

    @Test
    @DisplayName("获取不存在的教案详情 - 返回null")
    void getWorkDetail_NotFound_ReturnsNull() {
        // Given
        when(workRepository.findById("nonexistent"))
            .thenReturn(Optional.empty());

        // When
        var result = workService.getWorkDetail("nonexistent");

        // Then
        assertThat(result).isNull();

        verify(workRepository).findById("nonexistent");
    }

    @Test
    @DisplayName("创建教案 - 成功")
    void createWork_Success() {
        // Given
        when(workRepository.save(any(WorkEntity.class)))
            .thenReturn(work1);

        // When
        var result = workService.createWork(
            "新教案",
            "教案描述",
            "category-1",
            "📄",
            "/works/new.html",
            1
        );

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getName()).isEqualTo("新教案");
        assertThat(result.getCategoryId()).isEqualTo("category-1");
        assertThat(result.getVisible()).isTrue();

        verify(workRepository).save(any(WorkEntity.class));
    }

    @Test
    @DisplayName("创建教案时order为null - 使用默认值0")
    void createWork_OrderNull_UsesDefaultZero() {
        // Given
        when(workRepository.save(any(WorkEntity.class)))
            .thenReturn(work1);

        // When
        var result = workService.createWork(
            "新教案",
            "教案描述",
            "category-1",
            "📄",
            "/works/new.html",
            null
        );

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getOrder()).isEqualTo(0);

        verify(workRepository).save(any(WorkEntity.class));
    }

    @Test
    @DisplayName("创建教案 - 自动生成ID")
    void createWork_GeneratesId() {
        // Given
        when(workRepository.save(any(WorkEntity.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));

        // When
        var result = workService.createWork(
            "新教案",
            "教案描述",
            "category-1",
            "📄",
            "/works/new.html",
            1
        );

        // Then
        assertThat(result.getId()).isNotNull();
        assertThat(result.getId()).isNotEmpty();
    }

    @Test
    @DisplayName("教案按order排序 - 正确排序")
    void getCategoriesWithWorks_SortsByOrder() {
        // Given - 反序的教案
        when(categoryRepository.findAllByOrderByOrderAsc())
            .thenReturn(List.of(category));
        when(workRepository.findByCategoryIdAndVisibleTrueOrderByOrderAsc("category-1"))
            .thenReturn(List.of(work2, work1)); // 存储时反序

        // When
        var result = workService.getCategoriesWithWorks();

        // Then
        assertThat(result.get(0).getWorks().get(0).getName()).isEqualTo("教案2");
        assertThat(result.get(0).getWorks().get(1).getName()).isEqualTo("教案1");
    }
}
