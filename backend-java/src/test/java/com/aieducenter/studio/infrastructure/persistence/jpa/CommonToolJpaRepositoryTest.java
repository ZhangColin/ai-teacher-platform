package com.aieducenter.studio.infrastructure.persistence.jpa;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * CommonToolJpaRepository集成测试
 */
@DataJpaTest
@ActiveProfiles("test")
@DisplayName("CommonToolJpaRepository集成测试")
class CommonToolJpaRepositoryTest {

    @Autowired
    private CommonToolJpaRepository repository;

    @Autowired
    private TestEntityManager entityManager;

    private CommonToolEntity tool1;
    private CommonToolEntity tool2;
    private String categoryId;

    @BeforeEach
    void setUp() {
        categoryId = "category-123";

        // 创建测试数据
        tool1 = new CommonToolEntity();
        tool1.setId("tool-1");
        tool1.setName("工具1");
        tool1.setCategoryId(categoryId);
        tool1.setVisible(true);
        tool1.setOrder(1);

        tool2 = new CommonToolEntity();
        tool2.setId("tool-2");
        tool2.setName("工具2");
        tool2.setCategoryId(categoryId);
        tool2.setVisible(true);
        tool2.setOrder(2);

        // 保存到数据库
        entityManager.persist(tool1);
        entityManager.persist(tool2);
        entityManager.flush();
    }

    @Test
    @DisplayName("根据分类ID查询可见工具 - 按order排序")
    void findByCategoryIdAndVisibleTrueOrderByOrderAsc_ReturnsOrderedTools() {
        // When
        List<CommonToolEntity> result = repository.findByCategoryIdAndVisibleTrueOrderByOrderAsc(categoryId);

        // Then
        assertThat(result).hasSize(2);
        assertThat(result.get(0).getId()).isEqualTo("tool-1"); // order=1
        assertThat(result.get(1).getId()).isEqualTo("tool-2"); // order=2
    }

    @Test
    @DisplayName("查询可见工具 - 过滤不可见工具")
    void findByCategoryIdAndVisibleTrueOrderByOrderAsc_FiltersInvisibleTools() {
        // Given - 创建不可见工具
        CommonToolEntity tool3 = new CommonToolEntity();
        tool3.setId("tool-3");
        tool3.setName("工具3");
        tool3.setCategoryId(categoryId);
        tool3.setVisible(false);
        tool3.setOrder(3);

        entityManager.persist(tool3);
        entityManager.flush();

        // When
        List<CommonToolEntity> result = repository.findByCategoryIdAndVisibleTrueOrderByOrderAsc(categoryId);

        // Then
        assertThat(result).hasSize(2);
        assertThat(result).noneMatch(tool -> tool.getId().equals("tool-3"));
    }

    @Test
    @DisplayName("根据ID查询可见工具")
    void findByIdAndVisibleTrue_ExistingVisibleTool_ReturnsTool() {
        // When
        List<CommonToolEntity> result = repository.findByIdAndVisibleTrue("tool-1");

        // Then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getId()).isEqualTo("tool-1");
        assertThat(result.get(0).getVisible()).isTrue();
    }

    @Test
    @DisplayName("根据ID查询可见工具 - 不可见工具返回空")
    void findByIdAndVisibleTrue_InvisibleTool_ReturnsEmpty() {
        // Given
        tool1.setVisible(false);
        repository.save(tool1);
        entityManager.flush();

        // When
        List<CommonToolEntity> result = repository.findByIdAndVisibleTrue("tool-1");

        // Then
        assertThat(result).isEmpty();
    }

    @Test
    @DisplayName("查询不存在的分类 - 返回空列表")
    void findByCategoryIdAndVisibleTrueOrderByOrderAsc_NoCategory_ReturnsEmpty() {
        // When
        List<CommonToolEntity> result = repository.findByCategoryIdAndVisibleTrueOrderByOrderAsc("nonexistent-category");

        // Then
        assertThat(result).isEmpty();
    }

    @Test
    @DisplayName("根据ID查询工具 - 使用继承的findById")
    void findById_ExistingTool_ReturnsTool() {
        // When
        var result = repository.findById("tool-1");

        // Then
        assertThat(result).isPresent();
        assertThat(result.get().getId()).isEqualTo("tool-1");
        assertThat(result.get().getName()).isEqualTo("工具1");
    }

    @Test
    @DisplayName("保存新工具 - 使用继承的save")
    void save_NewTool_PersistsTool() {
        // Given
        CommonToolEntity newTool = new CommonToolEntity();
        newTool.setId("new-tool");
        newTool.setName("新工具");
        newTool.setCategoryId(categoryId);
        newTool.setVisible(true);
        newTool.setOrder(3);

        // When
        CommonToolEntity saved = repository.save(newTool);

        // Then
        assertThat(saved.getId()).isEqualTo("new-tool");
        assertThat(repository.findById("new-tool")).isPresent();
    }

    @Test
    @DisplayName("删除工具 - 使用继承的deleteById")
    void deleteById_ExistingTool_RemovesTool() {
        // When
        repository.deleteById("tool-1");

        // Then
        assertThat(repository.findById("tool-1")).isEmpty();
    }

    @Test
    @DisplayName("更新工具 - 修改名称")
    void update_ExistingTool_ModifiesTool() {
        // Given
        tool1.setName("更新后的工具名");

        // When
        repository.save(tool1);
        entityManager.flush();
        entityManager.clear();

        // Then
        var updated = repository.findById("tool-1");
        assertThat(updated).isPresent();
        assertThat(updated.get().getName()).isEqualTo("更新后的工具名");
    }

    @Test
    @DisplayName("切换工具可见性")
    void toggleVisibility_ExistingTool_TogglesVisibility() {
        // Given
        assertThat(tool1.getVisible()).isTrue();

        // When
        tool1.setVisible(false);
        repository.save(tool1);
        entityManager.flush();
        entityManager.clear();

        // Then
        var updated = repository.findById("tool-1");
        assertThat(updated).isPresent();
        assertThat(updated.get().getVisible()).isFalse();
    }

    @Test
    @DisplayName("调整工具顺序")
    void reorderTools_ChangesOrder() {
        // Given
        tool1.setOrder(10);
        tool2.setOrder(20);

        // When
        repository.saveAll(List.of(tool1, tool2));
        entityManager.flush();
        entityManager.clear();

        // Then
        List<CommonToolEntity> result = repository.findByCategoryIdAndVisibleTrueOrderByOrderAsc(categoryId);
        assertThat(result.get(0).getId()).isEqualTo("tool-1"); // order=10
        assertThat(result.get(1).getId()).isEqualTo("tool-2"); // order=20
    }

    @Test
    @DisplayName("统计工具数量 - 使用继承的count")
    void count_ReturnsToolCount() {
        // When
        long count = repository.count();

        // Then
        assertThat(count).isGreaterThanOrEqualTo(2);
    }

    @Test
    @DisplayName("查询所有工具 - 使用继承的findAll")
    void findAll_ReturnsAllTools() {
        // When
        List<CommonToolEntity> result = repository.findAll();

        // Then
        assertThat(result).hasSizeGreaterThanOrEqualTo(2);
    }
}
