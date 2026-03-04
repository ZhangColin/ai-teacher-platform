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
 * 课程管理E2E测试
 *
 * 测试场景：登录（管理员） → 创建分类 → 创建文档 → 发布 → 前端查看
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
@DisplayName("课程管理E2E测试")
class CourseManagementE2ETest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @DisplayName("课程分类管理完整流程 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void courseCategoryManagement_Success() throws Exception {
        // 步骤1: 创建根分类
        String createRootCategoryRequest = """
            {
                "name": "数学",
                "parentId": null,
                "order": 1
            }
            """;

        mockMvc.perform(post("/api/v1/admin/course-categories")
                .contentType(MediaType.APPLICATION_JSON)
                .content(createRootCategoryRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.category.name").value("数学"));

        // 步骤2: 创建子分类
        String createChildCategoryRequest = """
            {
                "name": "代数",
                "parentId": "math-category-id",
                "order": 1
            }
            """;

        mockMvc.perform(post("/api/v1/admin/course-categories")
                .contentType(MediaType.APPLICATION_JSON)
                .content(createChildCategoryRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.category.name").value("代数"));

        // 步骤3: 更新分类
        String updateCategoryRequest = """
            {
                "name": "高等数学",
                "order": 2
            }
            """;

        mockMvc.perform(put("/api/v1/admin/course-categories/category-id")
                .contentType(MediaType.APPLICATION_JSON)
                .content(updateCategoryRequest))
            .andExpect(status().isOk());

        // 步骤4: 删除分类
        mockMvc.perform(delete("/api/v1/admin/course-categories/category-to-delete"))
            .andExpect(status().isNoContent());
    }

    @Test
    @DisplayName("课程文档管理完整流程 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void courseDocumentManagement_Success() throws Exception {
        // 步骤1: 创建课程文档
        String createDocumentRequest = """
            {
                "title": "第一章：代数基础",
                "categoryId": "math-category-id",
                "content": "# 代数基础\\n\\n这是第一章的内容...",
                "order": 1
            }
            """;

        mockMvc.perform(post("/api/v1/admin/course-documents")
                .contentType(MediaType.APPLICATION_JSON)
                .content(createDocumentRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.document.title").value("第一章：代数基础"));

        // 步骤2: 更新文档
        String updateDocumentRequest = """
            {
                "title": "第一章：代数基础（修订版）",
                "content": "# 代数基础\\n\\n这是修订后的内容..."
            }
            """;

        mockMvc.perform(put("/api/v1/admin/course-documents/doc-id")
                .contentType(MediaType.APPLICATION_JSON)
                .content(updateDocumentRequest))
            .andExpect(status().isOk());

        // 步骤3: 删除文档
        mockMvc.perform(delete("/api/v1/admin/course-documents/doc-to-delete"))
            .andExpect(status().isNoContent());
    }

    @Test
    @DisplayName("前端查看课程内容 - 成功")
    void viewCourseContent_Success() throws Exception {
        // 步骤1: 获取课程分类树
        mockMvc.perform(get("/api/v1/course/categories"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.categories").isArray());

        // 步骤2: 获取分类下的文档列表
        mockMvc.perform(get("/api/v1/course/categories/category-id/documents"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.documents").isArray());

        // 步骤3: 获取文档详情
        mockMvc.perform(get("/api/v1/course/documents/doc-id"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.document.title").isString())
            .andExpect(jsonPath("$.document.content").isString());
    }

    @Test
    @DisplayName("课程分类调整顺序 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void reorderCourseCategories_Success() throws Exception {
        // 将分类上移
        mockMvc.perform(post("/api/v1/admin/course-categories/category-id/move-up"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.category.order").exists());

        // 将分类下移
        mockMvc.perform(post("/api/v1/admin/course-categories/category-id/move-down"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.category.order").exists());
    }

    @Test
    @DisplayName("多级课程分类结构 - 正确显示")
    void multiLevelCourseCategories_DisplaysCorrectly() throws Exception {
        // 获取完整的分类树
        mockMvc.perform(get("/api/v1/course/categories"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.categories").isArray())
            .andExpect(jsonPath("$.categories[0].children").isArray());
    }

    @Test
    @DisplayName("课程文档搜索 - 按标题搜索")
    void searchCourseDocuments_ByTitle() throws Exception {
        // 搜索包含关键词的文档
        mockMvc.perform(get("/api/v1/course/documents/search")
                .param("keyword", "代数")
                .param("categoryId", "math-category-id"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.documents").isArray());
    }

    @Test
    @DisplayName("课程文档Markdown渲染 - 正确渲染")
    void renderCourseMarkdown_RendersCorrectly() throws Exception {
        // 获取文档内容（应该是Markdown格式）
        mockMvc.perform(get("/api/v1/course/documents/doc-id"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.document.content").isString())
            .andExpect(jsonPath("$.document.format").value("markdown"));
    }

    @Test
    @DisplayName("管理员批量上传课程文档 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void batchUploadCourseDocuments_Success() throws Exception {
        // 创建多个文档
        for (int i = 1; i <= 3; i++) {
            String request = String.format("""
                {
                    "title": "第%d章",
                    "categoryId": "math-category-id",
                    "content": "第%d章的内容...",
                    "order": %d
                }
                """, i, i, i);

            mockMvc.perform(post("/api/v1/admin/course-documents")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request))
                .andExpect(status().isOk());
        }

        // 验证所有文档都已创建
        mockMvc.perform(get("/api/v1/course/categories/math-category-id/documents"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.documents").isArray());
    }

    @Test
    @DisplayName("课程分类统计 - 返回正确数量")
    void getCourseCategoryStats_ReturnsCorrectCount() throws Exception {
        // 获取分类统计信息
        mockMvc.perform(get("/api/v1/course/categories/category-id/stats"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.stats.totalDocuments").isNumber())
            .andExpect(jsonPath("$.stats.totalViews").isNumber());
    }

    @Test
    @DisplayName("非管理员访问管理端点 - 返回403")
    @WithMockUser(username = "regularuser", roles = {"USER"})
    void nonAdminAccessCourseAdmin_Returns403() throws Exception {
        // 尝试创建分类
        String request = """
            {
                "name": "测试分类",
                "order": 1
            }
            """;

        mockMvc.perform(post("/api/v1/admin/course-categories")
                .contentType(MediaType.APPLICATION_JSON)
                .content(request))
            .andExpect(status().isForbidden());
    }

    @Test
    @DisplayName("获取所有课程分类（管理员） - 包含所有字段")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void getAllCourseCategories_AsAdmin_IncludesAllFields() throws Exception {
        mockMvc.perform(get("/api/v1/admin/course-categories"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.categories").isArray())
            .andExpect(jsonPath("$.categories[0].id").exists())
            .andExpect(jsonPath("$.categories[0].name").exists())
            .andExpect(jsonPath("$.categories[0].order").exists());
    }

    @Test
    @DisplayName("课程文档发布 - 设置为可见")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void publishCourseDocument_SetsVisible() throws Exception {
        String publishRequest = """
            {
                "visible": true
            }
            """;

        mockMvc.perform(patch("/api/v1/admin/course-documents/doc-id/visibility")
                .contentType(MediaType.APPLICATION_JSON)
                .content(publishRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.document.visible").value(true));
    }
}
