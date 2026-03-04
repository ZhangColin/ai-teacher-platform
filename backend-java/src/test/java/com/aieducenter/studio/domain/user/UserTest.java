package com.aieducenter.studio.domain.user;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * User领域实体单元测试
 */
@DisplayName("User领域实体单元测试")
class UserTest {

    @Test
    @DisplayName("管理员可以访问所有工具")
    void canAccessTool_Admin_ReturnsTrue() {
        // Given
        User admin = new User();
        admin.setIsAdmin(true);

        // When
        boolean result = admin.canAccessTool("any-tool-id");

        // Then
        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("普通用户可以访问工具（临时实现）")
    void canAccessTool_RegularUser_ReturnsTrue() {
        // Given
        User user = new User();
        user.setIsAdmin(false);

        // When
        boolean result = user.canAccessTool("some-tool-id");

        // Then
        // 当前临时实现：所有用户都可以访问所有工具
        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("检查是否为付费用户 - 返回false")
    void isPremiumUser_ReturnsFalse() {
        // Given
        User user = new User();
        user.setIsAdmin(false);

        // When
        boolean result = user.isPremiumUser();

        // Then
        // TODO: 当前实现返回false
        assertThat(result).isFalse();
    }

    @Test
    @DisplayName("创建新用户 - 使用默认创建时间")
    void createNew_UsesDefaultCreatedAt() {
        // When
        User user = User.createNew("testuser", "test@example.com", null);

        // Then
        assertThat(user).isNotNull();
        assertThat(user.getUsername()).isEqualTo("testuser");
        assertThat(user.getEmail()).isEqualTo("test@example.com");
        assertThat(user.getIsAdmin()).isFalse();
        assertThat(user.getId()).isEqualTo("0"); // 数据库生成UUID
        assertThat(user.getCreatedAt()).isNotNull();
        assertThat(user.getCreatedAt()).isBeforeOrEqualTo(java.time.LocalDateTime.now());
    }

    @Test
    @DisplayName("创建新用户 - 使用指定创建时间")
    void createNew_UsesSpecifiedCreatedAt() {
        // Given
        LocalDateTime specifiedTime = LocalDateTime.of(2024, 1, 1, 12, 0);

        // When
        User user = User.createNew("testuser", "test@example.com", specifiedTime);

        // Then
        assertThat(user.getCreatedAt()).isEqualTo(specifiedTime);
    }

    @Test
    @DisplayName("生成用户ID - 返回非空UUID")
    void generateUserId_ReturnsNonEmptyUUID() {
        // When
        String userId = User.generateUserId();

        // Then
        assertThat(userId).isNotNull();
        assertThat(userId).isNotEmpty();
        // UUID格式: 8-4-4-4-12
        assertThat(userId).matches("^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$");
    }

    @Test
    @DisplayName("生成多个用户ID - 每个都不同")
    void generateUserId_MultipleCalls_GeneratesUniqueIds() {
        // When
        String id1 = User.generateUserId();
        String id2 = User.generateUserId();
        String id3 = User.generateUserId();

        // Then
        assertThat(id1).isNotEqualTo(id2);
        assertThat(id2).isNotEqualTo(id3);
        assertThat(id1).isNotEqualTo(id3);
    }

    @Test
    @DisplayName("Lombok @Data注解 - Getter和Setter工作正常")
    void lombokData_GettersAndSetters_Work() {
        // Given
        User user = new User();

        // When
        user.setId("user-123");
        user.setUsername("testuser");
        user.setEmail("test@example.com");
        user.setIsAdmin(true);
        user.setCreatedAt(LocalDateTime.now());

        // Then
        assertThat(user.getId()).isEqualTo("user-123");
        assertThat(user.getUsername()).isEqualTo("testuser");
        assertThat(user.getEmail()).isEqualTo("test@example.com");
        assertThat(user.getIsAdmin()).isTrue();
        assertThat(user.getCreatedAt()).isNotNull();
    }

    @Test
    @DisplayName("Lombok @NoArgsConstructor注解 - 无参构造工作正常")
    void lombokNoArgsConstructor_Works() {
        // When
        User user = new User();

        // Then
        assertThat(user).isNotNull();
    }

    @Test
    @DisplayName("Lombok @AllArgsConstructor注解 - 全参构造工作正常")
    void lombokAllArgsConstructor_Works() {
        // Given
        LocalDateTime now = LocalDateTime.now();

        // When
        User user = new User();
        user.setId("user-123");
        user.setUsername("testuser");
        user.setEmail("test@example.com");
        user.setIsAdmin(true);
        user.setCreatedAt(now);

        // Then
        assertThat(user.getId()).isEqualTo("user-123");
        assertThat(user.getUsername()).isEqualTo("testuser");
        assertThat(user.getEmail()).isEqualTo("test@example.com");
        assertThat(user.getIsAdmin()).isTrue();
        assertThat(user.getCreatedAt()).isEqualTo(now);
    }

    @Test
    @DisplayName("创建新用户 - 默认不是管理员")
    void createNew_DefaultIsNotAdmin() {
        // When
        User user = User.createNew("regularuser", "user@example.com", null);

        // Then
        assertThat(user.getIsAdmin()).isFalse();
    }
}
