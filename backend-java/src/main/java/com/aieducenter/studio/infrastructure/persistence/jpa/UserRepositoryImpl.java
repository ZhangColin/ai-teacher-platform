package com.aieducenter.studio.infrastructure.persistence.jpa;

import com.aieducenter.studio.domain.user.User;
import com.aieducenter.studio.domain.user.repository.UserRepository;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Optional;

/**
 * User仓储JPA实现
 *
 * 对应Python: backend/src/services/user_service.py的数据访问部分
 * 实现UserRepository接口，使用JPA进行数据持久化
 *
 * @author AI Teacher Platform
 */
@Component
public class UserRepositoryImpl implements UserRepository {

    private final UserJpaRepository jpaRepository;

    /**
     * 构造函数注入
     *
     * @param jpaRepository Spring Data JPA Repository
     */
    public UserRepositoryImpl(UserJpaRepository jpaRepository) {
        this.jpaRepository = jpaRepository;
    }

    @Override
    public Optional<User> findById(String userId) {
        return jpaRepository.findById(userId)
            .map(this::toDomainEntity);
    }

    @Override
    public Optional<User> findByUsername(String username) {
        return jpaRepository.findByUsername(username)
            .map(this::toDomainEntity);
    }

    @Override
    public Optional<User> findByEmail(String email) {
        return jpaRepository.findByEmail(email)
            .map(this::toDomainEntity);
    }

    @Override
    public User create(User user) {
        UserEntity entity = toJpaEntity(user);
        UserEntity saved = jpaRepository.save(entity);
        return toDomainEntity(saved);
    }

    @Override
    public User update(User user) {
        UserEntity entity = toJpaEntity(user);
        UserEntity updated = jpaRepository.save(entity);
        return toDomainEntity(updated);
    }

    @Override
    public void delete(String userId) {
        jpaRepository.deleteById(userId);
    }

    @Override
    public List<User> listAll(int skip, int limit) {
        return jpaRepository.findAll()
            .stream()
            .skip(skip)
            .limit(limit)
            .map(this::toDomainEntity)
            .toList();
    }

    /**
     * 将领域实体转换为JPA实体
     *
     * @param domain 领域实体
     * @return JPA实体
     */
    private UserEntity toJpaEntity(User domain) {
        UserEntity entity = new UserEntity();
        entity.setUserId(domain.getId());
        entity.setUsername(domain.getUsername());
        entity.setEmail(domain.getEmail());
        entity.setIsAdmin(domain.getIsAdmin());
        entity.setCreatedAt(domain.getCreatedAt());

        // 注意：nickname, phone, passwordHash, avatar等字段在当前User领域实体中不存在
        // 这些字段应该在未来添加到User实体中，或者通过其他方式管理

        return entity;
    }

    /**
     * 将JPA实体转换为领域实体
     *
     * @param entity JPA实体
     * @return 领域实体
     */
    private User toDomainEntity(UserEntity entity) {
        User domain = new User();
        domain.setId(entity.getUserId());
        domain.setUsername(entity.getUsername());
        domain.setEmail(entity.getEmail());
        domain.setIsAdmin(entity.getIsAdmin());
        domain.setCreatedAt(entity.getCreatedAt());

        return domain;
    }
}
