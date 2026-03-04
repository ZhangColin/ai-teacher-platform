package com.platform.interfaces.rest;

import com.platform.application.service.CommonToolService;
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
import static org.hamcrest.Matchers.*;

/**
 * AdminController集成测试
 *
 * 对应Python: backend/tests/integration/test_admin_tools.py
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
@DisplayName("AdminController集成测试")
class AdminControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    // ==================== Common Tool管理接口测试 ====================

    @Test
    @DisplayName("获取工具列表（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void getAdminTools_Success() throws Exception {
        mockMvc.perform(get("/api/v1/admin/common-tools")
                .param("page", "1")
                .param("pageSize", "20"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.tools").isArray())
            .andExpect(jsonPath("$.total").isNumber());
    }

    @Test
    @DisplayName("创建内置工具（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void createBuiltInTool_Success() throws Exception {
        String toolJson = """
            {
                "name": "测试工具",
                "description": "测试描述",
                "categoryId": "test-category-id",
                "icon": "test-icon",
                "order": 1,
                "visible": true,
                "systemPrompt": "你是一个测试助手",
                "modelConfig": "{}"
            }
            """;

        mockMvc.perform(post("/api/v1/admin/common-tools/built-in")
                .contentType(MediaType.APPLICATION_JSON)
                .content(toolJson))
            .andExpect(status().isCreated());
    }

    @Test
    @DisplayName("更新工具信息（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void updateTool_Success() throws Exception {
        String updateJson = """
            {
                "name": "更新后的工具名",
                "description": "更新后的描述"
            }
            """;

        mockMvc.perform(patch("/api/v1/admin/common-tools/test-tool-id")
                .contentType(MediaType.APPLICATION_JSON)
                .content(updateJson))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("删除工具（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void deleteTool_Success() throws Exception {
        mockMvc.perform(delete("/api/v1/admin/common-tools/test-tool-id"))
            .andExpect(status().isNoContent());
    }

    @Test
    @DisplayName("上移工具（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void moveToolUp_Success() throws Exception {
        mockMvc.perform(post("/api/v1/admin/common-tools/test-tool-id/move-up"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").value("工具已上移"));
    }

    @Test
    @DisplayName("下移工具（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void moveToolDown_Success() throws Exception {
        mockMvc.perform(post("/api/v1/admin/common-tools/test-tool-id/move-down"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").value("工具已下移"));
    }

    @Test
    @DisplayName("切换工具可见性（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void toggleToolVisibility_Success() throws Exception {
        mockMvc.perform(post("/api/v1/admin/common-tools/test-tool-id/toggle-visibility"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").isString());
    }

    // ==================== 工具分类管理接口测试 ====================

    @Test
    @DisplayName("获取工具分类列表（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void getAdminToolCategories_Success() throws Exception {
        mockMvc.perform(get("/api/v1/admin/tool-categories"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.categories").isArray());
    }

    @Test
    @DisplayName("创建工具分类（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void createToolCategory_Success() throws Exception {
        String categoryJson = """
            {
                "name": "测试分类",
                "order": 1
            }
            """;

        mockMvc.perform(post("/api/v1/admin/tool-categories")
                .contentType(MediaType.APPLICATION_JSON)
                .content(categoryJson))
            .andExpect(status().isCreated());
    }

    @Test
    @DisplayName("更新工具分类（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void updateToolCategory_Success() throws Exception {
        String updateJson = """
            {
                "name": "更新后的分类名"
            }
            """;

        mockMvc.perform(patch("/api/v1/admin/tool-categories/test-category-id")
                .contentType(MediaType.APPLICATION_JSON)
                .content(updateJson))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("删除工具分类（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void deleteToolCategory_Success() throws Exception {
        mockMvc.perform(delete("/api/v1/admin/tool-categories/test-category-id"))
            .andExpect(status().isNoContent());
    }

    @Test
    @DisplayName("上移分类（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void moveCategoryUp_Success() throws Exception {
        mockMvc.perform(post("/api/v1/admin/tool-categories/test-category-id/move-up"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").value("分类已上移"));
    }

    @Test
    @DisplayName("下移分类（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void moveCategoryDown_Success() throws Exception {
        mockMvc.perform(post("/api/v1/admin/tool-categories/test-category-id/move-down"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").value("分类已下移"));
    }

    // ==================== 权限验证测试 ====================

    @Test
    @DisplayName("非管理员用户访问 - 返回403")
    @WithMockUser(username = "user", roles = {"USER"})
    void getAdminTools_Forbidden_Returns403() throws Exception {
        mockMvc.perform(get("/api/v1/admin/common-tools"))
            .andExpect(status().isForbidden());
    }
}
