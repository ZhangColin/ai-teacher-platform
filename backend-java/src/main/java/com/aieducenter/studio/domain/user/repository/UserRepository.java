package com.aieducenter.studio.domain.user.repository;

import com.aieducenter.studio.domain.user.User;

import java.util.List;
import java.util.Optional;

/**
 * 用户仓储接口
 *
 * 对应Python: backend/src/domain/repositories/user.py
 * 对应数据库表: users
 *
 * @author AI Teacher Platform
 */
public interface UserRepository {

    /**
     * 根据用户ID获取用户
     * 对应Python: get_by_id(user_id: str) -> Optional[User]
     *
     * @param userId 用户ID
     * @return 用户（可能为空）
     */
    Optional<User> findById(String userId);

    /**
     * 根据用户名获取用户
     * 对应Python: get_by_username(username: str) -> Optional[User]
     *
     * @param username 用户名
     * @return 用户（可能为空）
     */
    Optional<User> findByUsername(String username);

    /**
     * 根据邮箱获取用户
     * 对应Python: get_by_email(email: str) -> Optional[User]
     *
     * @param email 邮箱
     * @return 用户（可能为空）
     */
    Optional<User> findByEmail(String email);

    /**
     * 创建用户
     * 对应Python: create(user: User) -> User
     *
     * @param user 用户实体
     * @return 创建后的用户
     */
    User create(User user);

    /**
     * 更新用户
     * 对应Python: update(user: User) -> User
     *
     * @param user 用户实体
     * @return 更新后的用户
     */
    User update(User user);

    /**
     * 删除用户
     * 对应Python: delete(user_id: str) -> None
     *
     * @param userId 用户ID
     */
    void delete(String userId);

    /**
     * 获取用户列表（分页）
     * 对应Python: list_all(skip: int, limit: int) -> list[User]
     *
     * @param skip 跳过条数
     * @param limit 限制条数
     * @return 用户列表
     */
    List<User> listAll(int skip, int limit);
}
