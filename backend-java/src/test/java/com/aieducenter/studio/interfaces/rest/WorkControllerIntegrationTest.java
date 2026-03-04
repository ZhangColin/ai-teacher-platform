package com.aieducenter.studio.interfaces.rest;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * WorkController集成测试
 *
 * 对应Python: backend/tests/integration/test_works.py
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
@DisplayName("WorkController集成测试")
class WorkControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("获取作品分类 - 成功")
    void getCategories_Success() throws Exception {
        mockMvc.perform(get("/api/v1/works/categories"))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("获取作品详情 - 成功")
    void getWorkDetail_Success() throws Exception {
        mockMvc.perform(get("/api/v1/works/test-work-id"))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("获取教案列表（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void getAdminWorks_Success() throws Exception {
        mockMvc.perform(get("/api/v1/admin/works")
                .param("page", "1")
                .param("pageSize", "20"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.works").isArray());
    }

    @Test
    @DisplayName("创建教案（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void createWork_Success() throws Exception {
        String workJson = """
            {
                "title": "测试教案",
                "content": "教案内容",
                "categoryId": "test-category-id"
            }
            """;

        mockMvc.perform(post("/api/v1/admin/works")
                .contentType("application/json")
                .content(workJson))
            .andExpect(status().isCreated());
    }

    @Test
    @DisplayName("更新教案（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void updateWork_Success() throws Exception {
        String updateJson = """
            {
                "title": "更新后的教案标题"
            }
            """;

        mockMvc.perform(patch("/api/v1/admin/works/test-work-id")
                .contentType("application/json")
                .content(updateJson))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("删除教案（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void deleteWork_Success() throws Exception {
        mockMvc.perform(delete("/api/v1/admin/works/test-work-id"))
            .andExpect(status().isNoContent());
    }

    @Test
    @DisplayName("切换教案可见性（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void toggleWorkVisibility_Success() throws Exception {
        mockMvc.perform(post("/api/v1/admin/works/test-work-id/toggle-visibility"))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("获取教案分类列表（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void getAdminWorkCategories_Success() throws Exception {
        mockMvc.perform(get("/api/v1/admin/work-categories"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.categories").isArray());
    }

    @Test
    @DisplayName("创建教案分类（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void createWorkCategory_Success() throws Exception {
        String categoryJson = """
            {
                "name": "测试教案分类",
                "order": 1
            }
            """;

        mockMvc.perform(post("/api/v1/admin/work-categories")
                .contentType("application/json")
                .content(categoryJson))
            .andExpect(status().isCreated());
    }

    @Test
    @DisplayName("更新教案分类（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void updateWorkCategory_Success() throws Exception {
        String updateJson = """
            {
                "name": "更新后的教案分类名"
            }
            """;

        mockMvc.perform(patch("/api/v1/admin/work-categories/test-category-id")
                .contentType("application/json")
                .content(updateJson))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("删除教案分类（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void deleteWorkCategory_Success() throws Exception {
        mockMvc.perform(delete("/api/v1/admin/work-categories/test-category-id"))
            .andExpect(status().isNoContent());
    }

    @Test
    @DisplayName("非管理员访问管理接口 - 返回403")
    @WithMockUser(username = "user", roles = {"USER"})
    void getAdminWorks_Forbidden_Returns403() throws Exception {
        mockMvc.perform(get("/api/v1/admin/works"))
            .andExpect(status().isForbidden());
    }
}
