package com.aieducenter.studio.infrastructure.persistence.jpa;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * User JPA Repository
 *
 * Spring Data JPA自动生成实现
 * 对应Python: SQLAlchemy的Session和Model操作
 *
 * @author AI Teacher Platform
 */
@Repository
public interface UserJpaRepository extends JpaRepository<UserEntity, String> {

    /**
     * 根据用户名查询
     * 对应Python: db.query(UserModel).filter(UserModel.username == username).first()
     *
     * @param username 用户名
     * @return 用户实体（可能为空）
     */
    Optional<UserEntity> findByUsername(String username);

    /**
     * 根据邮箱查询
     * 对应Python: db.query(UserModel).filter(UserModel.email == email).first()
     *
     * @param email 邮箱
     * @return 用户实体（可能为空）
     */
    Optional<UserEntity> findByEmail(String email);

    /**
     * 根据手机号查询
     *
     * @param phone 手机号
     * @return 用户实体（可能为空）
     */
    Optional<UserEntity> findByPhone(String phone);

    /**
     * 检查用户名是否存在
     *
     * @param username 用户名
     * @return true-存在，false-不存在
     */
    boolean existsByUsername(String username);

    /**
     * 检查邮箱是否存在
     *
     * @param email 邮箱
     * @return true-存在，false-不存在
     */
    boolean existsByEmail(String email);

    /**
     * 检查手机号是否存在
     *
     * @param phone 手机号
     * @return true-存在，false-不存在
     */
    boolean existsByPhone(String phone);

    /**
     * 根据管理员状态分页查询用户
     *
     * @param isAdmin 是否为管理员
     * @param pageable 分页参数
     * @return 用户分页结果
     */
    Page<UserEntity> findAllByIsAdmin(Boolean isAdmin, Pageable pageable);

    /**
     * 统计管理员数量
     *
     * @return 管理员总数
     */
    long countByIsAdminTrue();
}
