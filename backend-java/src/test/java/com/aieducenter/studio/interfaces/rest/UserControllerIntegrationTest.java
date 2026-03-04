package com.aieducenter.studio.interfaces.rest;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * UserController集成测试
 *
 * 对应Python: backend/tests/integration/test_users.py
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
@DisplayName("UserController集成测试")
class UserControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("获取用户列表（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void getUserList_Success() throws Exception {
        mockMvc.perform(get("/api/v1/admin/users")
                .param("page", "1")
                .param("pageSize", "20"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.users").isArray())
            .andExpect(jsonPath("$.total").isNumber());
    }

    @Test
    @DisplayName("创建用户（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void createUser_Success() throws Exception {
        String userJson = """
            {
                "username": "testuser",
                "nickname": "测试用户",
                "email": "test@example.com",
                "password": "password123",
                "isAdmin": false
            }
            """;

        mockMvc.perform(post("/api/v1/admin/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(userJson))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.user.username").value("testuser"));
    }

    @Test
    @DisplayName("获取用户详情（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void getUser_Success() throws Exception {
        mockMvc.perform(get("/api/v1/admin/users/test-user-id"))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("更新用户（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void updateUser_Success() throws Exception {
        String updateJson = """
            {
                "nickname": "更新后的昵称"
            }
            """;

        mockMvc.perform(patch("/api/v1/admin/users/test-user-id")
                .contentType(MediaType.APPLICATION_JSON)
                .content(updateJson))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("删除用户（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void deleteUser_Success() throws Exception {
        mockMvc.perform(delete("/api/v1/admin/users/test-user-id"))
            .andExpect(status().isNoContent());
    }

    @Test
    @DisplayName("重置用户密码（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void resetUserPassword_Success() throws Exception {
        String requestJson = """
            {
                "newPassword": "newPassword123"
            }
            """;

        mockMvc.perform(post("/api/v1/admin/users/test-user-id/reset-password")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").value("密码已重置"));
    }

    @Test
    @DisplayName("非管理员访问 - 返回403")
    @WithMockUser(username = "user", roles = {"USER"})
    void getUserList_Forbidden_Returns403() throws Exception {
        mockMvc.perform(get("/api/v1/admin/users"))
            .andExpect(status().isForbidden());
    }
}
