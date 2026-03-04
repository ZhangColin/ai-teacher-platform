package com.aieducenter.studio.infrastructure.persistence.jpa;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.test.context.ActiveProfiles;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * UserEntity JPA测试
 *
 * 对应Python: backend/tests/中的用户相关测试
 *
 * @author AI Teacher Platform
 */
@DataJpaTest
@ActiveProfiles("test")
@DisplayName("UserEntity JPA测试")
class UserJpaRepositoryTest {

    @Autowired
    private UserJpaRepository jpaRepository;

    @Test
    @DisplayName("保存用户 - 成功")
    void save_Success() {
        // Given
        UserEntity entity = new UserEntity();
        entity.setUserId("test-uid-001");
        entity.setUsername("testuser");
        entity.setEmail("test@example.com");
        entity.setPasswordHash("hashed_password_here");
        entity.setIsAdmin(false);

        // When
        UserEntity saved = jpaRepository.save(entity);

        // Then
        assertThat(saved).isNotNull();
        assertThat(saved.getUserId()).isEqualTo("test-uid-001");
        assertThat(saved.getUsername()).isEqualTo("testuser");
        assertThat(saved.getEmail()).isEqualTo("test@example.com");
        assertThat(saved.getIsAdmin()).isFalse();
        assertThat(saved.getCreatedAt()).isNotNull();
    }

    @Test
    @DisplayName("根据用户名查询 - 找到返回用户")
    void findByUsername_Found_ReturnsUser() {
        // Given
        UserEntity entity = new UserEntity();
        entity.setUserId("test-uid-002");
        entity.setUsername("alice");
        entity.setEmail("alice@example.com");
        entity.setPasswordHash("hashed");
        entity.setIsAdmin(false);
        jpaRepository.save(entity);

        // When
        Optional<UserEntity> found = jpaRepository.findByUsername("alice");

        // Then
        assertThat(found).isPresent();
        assertThat(found.get().getUsername()).isEqualTo("alice");
        assertThat(found.get().getEmail()).isEqualTo("alice@example.com");
    }

    @Test
    @DisplayName("根据用户名查询 - 未找到返回空")
    void findByUsername_NotFound_ReturnsEmpty() {
        // When
        Optional<UserEntity> found = jpaRepository.findByUsername("nonexistent");

        // Then
        assertThat(found).isEmpty();
    }

    @Test
    @DisplayName("检查用户名是否存在 - 存在返回true")
    void existsByUsername_Exists_ReturnsTrue() {
        // Given
        UserEntity entity = new UserEntity();
        entity.setUserId("test-uid-003");
        entity.setUsername("bob");
        entity.setEmail("bob@example.com");
        entity.setPasswordHash("hashed");
        entity.setIsAdmin(false);
        jpaRepository.save(entity);

        // When
        boolean exists = jpaRepository.existsByUsername("bob");

        // Then
        assertThat(exists).isTrue();
    }

    @Test
    @DisplayName("检查用户名是否存在 - 不存在返回false")
    void existsByUsername_NotExists_ReturnsFalse() {
        // When
        boolean exists = jpaRepository.existsByUsername("charlie");

        // Then
        assertThat(exists).isFalse();
    }

    @Test
    @DisplayName("根据邮箱查询 - 找到返回用户")
    void findByEmail_Found_ReturnsUser() {
        // Given
        UserEntity entity = new UserEntity();
        entity.setUserId("test-uid-004");
        entity.setUsername("david");
        entity.setEmail("david@example.com");
        entity.setPasswordHash("hashed");
        entity.setIsAdmin(false);
        jpaRepository.save(entity);

        // When
        Optional<UserEntity> found = jpaRepository.findByEmail("david@example.com");

        // Then
        assertThat(found).isPresent();
        assertThat(found.get().getUsername()).isEqualTo("david");
    }
}
