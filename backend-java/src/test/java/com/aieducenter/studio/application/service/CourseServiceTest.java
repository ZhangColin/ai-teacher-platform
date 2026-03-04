package com.aieducenter.studio.application.service;

import com.aieducenter.studio.infrastructure.persistence.jpa.CourseCategoryEntity;
import com.aieducenter.studio.infrastructure.persistence.jpa.CourseCategoryJpaRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

/**
 * CourseService单元测试
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("CourseService单元测试")
class CourseServiceTest {

    @Mock
    private CourseCategoryJpaRepository categoryRepository;

    @InjectMocks
    private CourseService courseService;

    private CourseCategoryEntity rootCategory;
    private CourseCategoryEntity childCategory1;
    private CourseCategoryEntity childCategory2;

    @BeforeEach
    void setUp() {
        // 准备测试数据
        rootCategory = new CourseCategoryEntity();
        rootCategory.setId("root-1");
        rootCategory.setName("根分类");
        rootCategory.setParentId(null);
        rootCategory.setOrder(1);
        rootCategory.setChildren(new ArrayList<>());

        childCategory1 = new CourseCategoryEntity();
        childCategory1.setId("child-1");
        childCategory1.setName("子分类1");
        childCategory1.setParentId("root-1");
        childCategory1.setOrder(1);
        childCategory1.setChildren(new ArrayList<>());

        childCategory2 = new CourseCategoryEntity();
        childCategory2.setId("child-2");
        childCategory2.setName("子分类2");
        childCategory2.setParentId("root-1");
        childCategory2.setOrder(2);
        childCategory2.setChildren(new ArrayList<>());

        rootCategory.getChildren().add(childCategory1);
        rootCategory.getChildren().add(childCategory2);
    }

    @Test
    @DisplayName("获取分类树 - 成功")
    void getCategoryTree_Success() {
        // Given
        when(categoryRepository.findByParentIdIsNullOrderByOrderAsc())
            .thenReturn(List.of(rootCategory));

        // When
        var result = courseService.getCategoryTree();

        // Then
        assertThat(result).isNotNull();
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getId()).isEqualTo("root-1");
        assertThat(result.get(0).getName()).isEqualTo("根分类");
        assertThat(result.get(0).getChildren()).hasSize(2);
        assertThat(result.get(0).getChildren().get(0).getName()).isEqualTo("子分类1");
        assertThat(result.get(0).getChildren().get(1).getName()).isEqualTo("子分类2");

        verify(categoryRepository).findByParentIdIsNullOrderByOrderAsc();
    }

    @Test
    @DisplayName("获取空分类树 - 返回空列表")
    void getCategoryTree_Empty_ReturnsEmptyList() {
        // Given
        when(categoryRepository.findByParentIdIsNullOrderByOrderAsc())
            .thenReturn(List.of());

        // When
        var result = courseService.getCategoryTree();

        // Then
        assertThat(result).isNotNull();
        assertThat(result).isEmpty();

        verify(categoryRepository).findByParentIdIsNullOrderByOrderAsc();
    }

    @Test
    @DisplayName("创建根分类 - 成功")
    void createRootCategory_Success() {
        // Given
        when(categoryRepository.save(any(CourseCategoryEntity.class)))
            .thenReturn(rootCategory);

        // When
        var result = courseService.createCategory("新根分类", null, 1);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getName()).isEqualTo("新根分类");
        assertThat(result.getParentId()).isNull();
        assertThat(result.getOrder()).isEqualTo(1);

        verify(categoryRepository).save(any(CourseCategoryEntity.class));
    }

    @Test
    @DisplayName("创建子分类 - 成功")
    void createChildCategory_Success() {
        // Given
        when(categoryRepository.save(any(CourseCategoryEntity.class)))
            .thenReturn(childCategory1);

        // When
        var result = courseService.createCategory("新子分类", "root-1", 1);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getName()).isEqualTo("新子分类");
        assertThat(result.getParentId()).isEqualTo("root-1");
        assertThat(result.getOrder()).isEqualTo(1);

        verify(categoryRepository).save(any(CourseCategoryEntity.class));
    }

    @Test
    @DisplayName("创建分类时order为null - 使用默认值0")
    void createCategory_OrderNull_UsesDefaultZero() {
        // Given
        when(categoryRepository.save(any(CourseCategoryEntity.class)))
            .thenReturn(rootCategory);

        // When
        var result = courseService.createCategory("测试分类", null, null);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getOrder()).isEqualTo(0);

        verify(categoryRepository).save(any(CourseCategoryEntity.class));
    }

    @Test
    @DisplayName("创建文档 - 成功")
    void createDocument_Success() {
        // When
        var result = courseService.createDocument(
            "测试文档",
            "category-1",
            "文档内容",
            1
        );

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getTitle()).isEqualTo("测试文档");
        assertThat(result.getCategoryId()).isEqualTo("category-1");
        assertThat(result.getContent()).isEqualTo("文档内容");
        assertThat(result.getOrder()).isEqualTo(1);
        assertThat(result.getId()).isNotNull();
    }

    @Test
    @DisplayName("创建文档时order为null - 使用默认值0")
    void createDocument_OrderNull_UsesDefaultZero() {
        // When
        var result = courseService.createDocument(
            "测试文档",
            "category-1",
            "文档内容",
            null
        );

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getOrder()).isEqualTo(0);
    }

    @Test
    @DisplayName("多层嵌套分类树 - 正确构建")
    void getCategoryTree_MultipleLevels_BuildsCorrectly() {
        // Given - 创建三级分类
        CourseCategoryEntity grandChild = new CourseCategoryEntity();
        grandChild.setId("grandchild-1");
        grandChild.setName("孙分类");
        grandChild.setParentId("child-1");
        grandChild.setOrder(1);
        grandChild.setChildren(new ArrayList<>());

        childCategory1.getChildren().add(grandChild);

        when(categoryRepository.findByParentIdIsNullOrderByOrderAsc())
            .thenReturn(List.of(rootCategory));

        // When
        var result = courseService.getCategoryTree();

        // Then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getChildren()).hasSize(2);
        assertThat(result.get(0).getChildren().get(0).getChildren()).hasSize(1);
        assertThat(result.get(0).getChildren().get(0).getChildren().get(0).getName())
            .isEqualTo("孙分类");
    }

    @Test
    @DisplayName("多个根分类 - 正确构建")
    void getCategoryTree_MultipleRoots_BuildsCorrectly() {
        // Given
        CourseCategoryEntity root2 = new CourseCategoryEntity();
        root2.setId("root-2");
        root2.setName("根分类2");
        root2.setParentId(null);
        root2.setOrder(2);
        root2.setChildren(new ArrayList<>());

        when(categoryRepository.findByParentIdIsNullOrderByOrderAsc())
            .thenReturn(List.of(rootCategory, root2));

        // When
        var result = courseService.getCategoryTree();

        // Then
        assertThat(result).hasSize(2);
        assertThat(result.get(0).getName()).isEqualTo("根分类");
        assertThat(result.get(1).getName()).isEqualTo("根分类2");
    }
}
