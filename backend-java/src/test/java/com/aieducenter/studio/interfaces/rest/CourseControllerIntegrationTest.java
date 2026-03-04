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
 * CourseController集成测试
 *
 * 对应Python: backend/tests/integration/test_courses.py
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
@DisplayName("CourseController集成测试")
class CourseControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("获取课程分类树 - 成功")
    void getCategoryTree_Success() throws Exception {
        mockMvc.perform(get("/api/v1/documents/categories"))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("获取分类下的文档 - 成功")
    void getDocumentsByCategory_Success() throws Exception {
        mockMvc.perform(get("/api/v1/documents/category/test-category-id/documents"))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("获取文档详情 - 成功")
    void getDocumentDetail_Success() throws Exception {
        mockMvc.perform(get("/api/v1/documents/test-doc-id"))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("获取课程分类列表（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void getAdminCategories_Success() throws Exception {
        mockMvc.perform(get("/api/v1/admin/course-categories"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.categories").isArray());
    }

    @Test
    @DisplayName("创建课程分类（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void createCategory_Success() throws Exception {
        String categoryJson = """
            {
                "name": "测试分类",
                "order": 1
            }
            """;

        mockMvc.perform(post("/api/v1/admin/course-categories")
                .contentType("application/json")
                .content(categoryJson))
            .andExpect(status().isCreated());
    }

    @Test
    @DisplayName("更新课程分类（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void updateCategory_Success() throws Exception {
        String updateJson = """
            {
                "name": "更新后的分类名"
            }
            """;

        mockMvc.perform(patch("/api/v1/admin/course-categories/test-category-id")
                .contentType("application/json")
                .content(updateJson))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("删除课程分类（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void deleteCategory_Success() throws Exception {
        mockMvc.perform(delete("/api/v1/admin/course-categories/test-category-id"))
            .andExpect(status().isNoContent());
    }

    @Test
    @DisplayName("获取课程文档列表（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void getAdminDocuments_Success() throws Exception {
        mockMvc.perform(get("/api/v1/admin/course-documents"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.documents").isArray());
    }

    @Test
    @DisplayName("创建课程文档（管理后台）- 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void createDocument_Success() throws Exception {
        String docJson = """
            {
                "title": "测试文档",
                "content": "文档内容",
                "categoryId": "test-category-id"
            }
            """;

        mockMvc.perform(post("/api/v1/admin/course-documents")
                .contentType("application/json")
                .content(docJson))
            .andExpect(status().isCreated());
    }
}
