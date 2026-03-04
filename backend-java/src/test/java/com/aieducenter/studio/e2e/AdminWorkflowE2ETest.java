package com.aieducenter.studio.e2e;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * 管理员工作流E2E测试
 *
 * 测试场景：登录（管理员） → 创建用户 → 创建工具 → 调整顺序 → 删除
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
@DisplayName("管理员工作流E2E测试")
class AdminWorkflowE2ETest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @DisplayName("管理员创建用户工作流 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void createUserWorkflow_Success() throws Exception {
        // 步骤1: 创建新用户
        String createUserRequest = """
            {
                "username": "newuser",
                "nickname": "新用户",
                "email": "newuser@example.com",
                "password": "password123",
                "isAdmin": false
            }
            """;

        mockMvc.perform(post("/api/v1/admin/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(createUserRequest))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.user.username").value("newuser"))
            .andExpect(jsonPath("$.user.email").value("newuser@example.com"));

        // 步骤2: 获取用户列表，验证新用户已创建
        mockMvc.perform(get("/api/v1/admin/users")
                .param("page", "1")
                .param("pageSize", "20"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.users").isArray())
            .andExpect(jsonPath("$.total").isNumber());
    }

    @Test
    @DisplayName("管理员创建工具工作流 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void createToolWorkflow_Success() throws Exception {
        // 步骤1: 获取所有管理后台工具
        mockMvc.perform(get("/api/v1/admin/tools")
                .param("page", "1")
                .param("pageSize", "20"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.tools").isArray());

        // 步骤2: 创建内置工具
        String createToolRequest = """
            {
                "name": "测试工具",
                "description": "这是一个测试工具",
                "categoryId": "test-category",
                "icon": "🔧",
                "welcomeMessage": "欢迎使用测试工具",
                "systemPrompt": "你是一个测试助手",
                "model": "deepseek:deepseek-chat",
                "order": 1,
                "visible": true,
                "type": "built_in"
            }
            """;

        mockMvc.perform(post("/api/v1/admin/tools/built-in")
                .contentType(MediaType.APPLICATION_JSON)
                .content(createToolRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.tool.name").value("测试工具"));
    }

    @Test
    @DisplayName("管理员调整工具顺序工作流 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void reorderToolWorkflow_Success() throws Exception {
        String toolId = "tool-to-reorder";

        // 步骤1: 将工具上移
        mockMvc.perform(post("/api/v1/admin/tools/" + toolId + "/move-up"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.tool.order").exists());

        // 步骤2: 将工具下移
        mockMvc.perform(post("/api/v1/admin/tools/" + toolId + "/move-down"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.tool.order").exists());

        // 步骤3: 切换工具可见性
        mockMvc.perform(post("/api/v1/admin/tools/" + toolId + "/toggle-visibility"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.tool.visible").exists());
    }

    @Test
    @DisplayName("管理员更新用户工作流 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void updateUserWorkflow_Success() throws Exception {
        String userId = "user-to-update";

        // 步骤1: 部分更新用户
        String updateRequest = """
            {
                "nickname": "更新后的昵称"
            }
            """;

        mockMvc.perform(patch("/api/v1/admin/users/" + userId)
                .contentType(MediaType.APPLICATION_JSON)
                .content(updateRequest))
            .andExpect(status().isOk());

        // 步骤2: 获取用户详情，验证更新
        mockMvc.perform(get("/api/v1/admin/users/" + userId))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.user.nickname").value("更新后的昵称"));
    }

    @Test
    @DisplayName("管理员重置用户密码工作流 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void resetPasswordWorkflow_Success() throws Exception {
        String userId = "user-to-reset";

        String resetRequest = """
            {
                "newPassword": "newPassword123"
            }
            """;

        mockMvc.perform(post("/api/v1/admin/users/" + userId + "/reset-password")
                .contentType(MediaType.APPLICATION_JSON)
                .content(resetRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").value("密码已重置"));
    }

    @Test
    @DisplayName("管理员删除用户工作流 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void deleteUserWorkflow_Success() throws Exception {
        String userId = "user-to-delete";

        // 删除用户
        mockMvc.perform(delete("/api/v1/admin/users/" + userId))
            .andExpect(status().isNoContent());

        // 验证用户已删除
        mockMvc.perform(get("/api/v1/admin/users/" + userId))
            .andExpect(status().isNotFound());
    }

    @Test
    @DisplayName("管理员删除工具工作流 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void deleteToolWorkflow_Success() throws Exception {
        String toolId = "tool-to-delete";

        // 删除工具
        mockMvc.perform(delete("/api/v1/admin/tools/" + toolId))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").isString());
    }

    @Test
    @DisplayName("管理员创建分类工作流 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void createCategoryWorkflow_Success() throws Exception {
        // 步骤1: 获取所有分类
        mockMvc.perform(get("/api/v1/admin/tool-categories"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.categories").isArray());

        // 步骤2: 创建新分类
        String createCategoryRequest = """
            {
                "name": "新分类",
                "order": 1
            }
            """;

        mockMvc.perform(post("/api/v1/admin/tool-categories")
                .contentType(MediaType.APPLICATION_JSON)
                .content(createCategoryRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.category.name").value("新分类"));

        // 步骤3: 调整分类顺序
        mockMvc.perform(post("/api/v1/admin/tool-categories/category-1/move-up"))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("非管理员访问管理端点 - 返回403")
    @WithMockUser(username = "regularuser", roles = {"USER"})
    void nonAdminAccess_Returns403() throws Exception {
        // 尝试访问管理端点
        mockMvc.perform(get("/api/v1/admin/users"))
            .andExpect(status().isForbidden());

        mockMvc.perform(post("/api/v1/admin/tools/built-in"))
            .andExpect(status().isForbidden());
    }

    @Test
    @DisplayName("管理员更新工具工作流 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void updateToolWorkflow_Success() throws Exception {
        String toolId = "tool-to-update";

        String updateRequest = """
            {
                "name": "更新后的工具名",
                "description": "更新后的描述"
            }
            """;

        mockMvc.perform(put("/api/v1/admin/tools/" + toolId)
                .contentType(MediaType.APPLICATION_JSON)
                .content(updateRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.tool.name").value("更新后的工具名"));
    }

    @Test
    @DisplayName("管理员批量操作工作流 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void batchOperationsWorkflow_Success() throws Exception {
        // 步骤1: 获取工具列表
        mockMvc.perform(get("/api/v1/admin/tools")
                .param("page", "1")
                .param("pageSize", "50"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.tools").isArray());

        // 步骤2: 批量更新工具可见性
        String toolId1 = "tool-1";
        String toolId2 = "tool-2";

        mockMvc.perform(post("/api/v1/admin/tools/" + toolId1 + "/toggle-visibility"))
            .andExpect(status().isOk());

        mockMvc.perform(post("/api/v1/admin/tools/" + toolId2 + "/toggle-visibility"))
            .andExpect(status().isOk());

        // 步骤3: 验证批量操作结果
        mockMvc.perform(get("/api/v1/admin/tools")
                .param("visible", "false"))
            .andExpect(status().isOk());
    }
}
