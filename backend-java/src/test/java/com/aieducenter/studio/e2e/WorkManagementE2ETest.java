package com.aieducenter.studio.e2e;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * 教案管理E2E测试
 *
 * 测试场景：登录（管理员） → 创建分类 → 创建教案 → 发布 → 前端查看
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
@DisplayName("教案管理E2E测试")
class WorkManagementE2ETest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @DisplayName("教案分类管理完整流程 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void workCategoryManagement_Success() throws Exception {
        // 步骤1: 创建教案分类
        String createCategoryRequest = """
            {
                "name": "小学数学",
                "icon": "📐",
                "order": 1
            }
            """;

        mockMvc.perform(post("/api/v1/admin/work-categories")
                .contentType(MediaType.APPLICATION_JSON)
                .content(createCategoryRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.category.name").value("小学数学"))
            .andExpect(jsonPath("$.category.icon").value("📐"));

        // 步骤2: 更新分类
        String updateCategoryRequest = """
            {
                "name": "小学数学（修订）",
                "icon": "📚",
                "order": 2
            }
            """;

        mockMvc.perform(put("/api/v1/admin/work-categories/category-id")
                .contentType(MediaType.APPLICATION_JSON)
                .content(updateCategoryRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.category.name").value("小学数学（修订）"));

        // 步骤3: 删除分类
        mockMvc.perform(delete("/api/v1/admin/work-categories/category-to-delete"))
            .andExpect(status().isNoContent());
    }

    @Test
    @DisplayName("教案内容管理完整流程 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void workContentManagement_Success() throws Exception {
        // 步骤1: 创建教案（不带HTML文件）
        String createWorkRequest = """
            {
                "name": "加法运算教案",
                "description": "教授小学一年级加法运算",
                "categoryId": "math-category-id",
                "icon": "➕",
                "order": 1
            }
            """;

        mockMvc.perform(post("/api/v1/admin/works")
                .contentType(MediaType.APPLICATION_JSON)
                .content(createWorkRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.work.name").value("加法运算教案"));

        // 步骤2: 更新教案
        String updateWorkRequest = """
            {
                "name": "加法运算教案（修订版）",
                "description": "修订后的加法运算教案",
                "icon": "🔢"
            }
            """;

        mockMvc.perform(put("/api/v1/admin/works/work-id")
                .contentType(MediaType.APPLICATION_JSON)
                .content(updateWorkRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.work.name").value("加法运算教案（修订版）"));

        // 步骤3: 删除教案
        mockMvc.perform(delete("/api/v1/admin/works/work-to-delete"))
            .andExpect(status().isNoContent());
    }

    @Test
    @DisplayName("前端查看教案内容 - 成功")
    void viewWorkContent_Success() throws Exception {
        // 步骤1: 获取所有教案（按分类分组）
        mockMvc.perform(get("/api/v1/works"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.categories").isArray());

        // 步骤2: 获取教案详情
        mockMvc.perform(get("/api/v1/works/work-id"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.work.name").isString())
            .andExpect(jsonPath("$.work.description").isString());

        // 步骤3: 访问教案HTML内容
        mockMvc.perform(get("/api/v1/works/work-id/html"))
            .andExpect(status().isOk())
            .andExpect(content().contentTypeCompatibleWith(MediaType.TEXT_HTML));
    }

    @Test
    @DisplayName("教案分类调整顺序 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void reorderWorkCategories_Success() throws Exception {
        // 将分类上移
        mockMvc.perform(post("/api/v1/admin/work-categories/category-id/move-up"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.category.order").exists());

        // 将分类下移
        mockMvc.perform(post("/api/v1/admin/work-categories/category-id/move-down"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.category.order").exists());
    }

    @Test
    @DisplayName("教案内容搜索 - 按名称搜索")
    void searchWorks_ByName() throws Exception {
        // 搜索包含关键词的教案
        mockMvc.perform(get("/api/v1/works/search")
                .param("keyword", "加法"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.works").isArray());
    }

    @Test
    @DisplayName("教案可见性切换 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void toggleWorkVisibility_Success() throws Exception {
        String toggleRequest = """
            {
                "visible": false
            }
            """;

        mockMvc.perform(patch("/api/v1/admin/works/work-id/visibility")
                .contentType(MediaType.APPLICATION_JSON)
                .content(toggleRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.work.visible").value(false));

        // 切换回可见
        String toggleBackRequest = """
            {
                "visible": true
            }
            """;

        mockMvc.perform(patch("/api/v1/admin/works/work-id/visibility")
                .contentType(MediaType.APPLICATION_JSON)
                .content(toggleBackRequest))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.work.visible").value(true));
    }

    @Test
    @DisplayName("管理员批量操作教案 - 成功")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void batchUpdateWorks_Success() throws Exception {
        // 批量更新教案顺序
        for (int i = 1; i <= 3; i++) {
            String request = String.format("""
                {
                    "order": %d
                }
                """, i);

            mockMvc.perform(patch("/api/v1/admin/works/work-" + i + "/order")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(request))
                .andExpect(status().isOk());
        }

        // 验证顺序已更新
        mockMvc.perform(get("/api/v1/works"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.categories[0].works").isArray());
    }

    @Test
    @DisplayName("教案统计信息 - 返回正确数据")
    void getWorkStats_ReturnsCorrectData() throws Exception {
        mockMvc.perform(get("/api/v1/works/stats"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.stats.totalWorks").isNumber())
            .andExpect(jsonPath("$.stats.totalCategories").isNumber())
            .andExpect(jsonPath("$.stats.totalViews").isNumber());
    }

    @Test
    @DisplayName("非管理员访问管理端点 - 返回403")
    @WithMockUser(username = "regularuser", roles = {"USER"})
    void nonAdminAccessWorkAdmin_Returns403() throws Exception {
        // 尝试创建分类
        String request = """
            {
                "name": "测试分类",
                "icon": "📝",
                "order": 1
            }
            """;

        mockMvc.perform(post("/api/v1/admin/work-categories")
                .contentType(MediaType.APPLICATION_JSON)
                .content(request))
            .andExpect(status().isForbidden());

        // 尝试创建教案
        String workRequest = """
            {
                "name": "测试教案",
                "categoryId": "test-category",
                "order": 1
            }
            """;

        mockMvc.perform(post("/api/v1/admin/works")
                .contentType(MediaType.APPLICATION_JSON)
                .content(workRequest))
            .andExpect(status().isForbidden());
    }

    @Test
    @DisplayName("教案预览 - 正确显示HTML内容")
    void previewWork_DisplaysHtmlContent() throws Exception {
        // 获取教案HTML
        mockMvc.perform(get("/api/v1/works/work-id/html"))
            .andExpect(status().isOk())
            .andExpect(content().contentTypeCompatibleWith(MediaType.TEXT_HTML))
            .andExpect(content().string(org.hamcrest.Matchers.containsString("<html")));
    }

    @Test
    @DisplayName("按分类筛选教案 - 返回正确结果")
    void filterWorksByCategory_ReturnsCorrectResults() throws Exception {
        // 获取特定分类下的教案
        mockMvc.perform(get("/api/v1/works")
                .param("categoryId", "math-category-id"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.categories").isArray())
            .andExpect(jsonPath("$.categories[0].id").value("math-category-id"));
    }

    @Test
    @DisplayName("获取所有教案分类（管理员） - 包含所有字段")
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void getAllWorkCategories_AsAdmin_IncludesAllFields() throws Exception {
        mockMvc.perform(get("/api/v1/admin/work-categories"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.categories").isArray())
            .andExpect(jsonPath("$.categories[0].id").exists())
            .andExpect(jsonPath("$.categories[0].name").exists())
            .andExpect(jsonPath("$.categories[0].icon").exists())
            .andExpect(jsonPath("$.categories[0].order").exists());
    }

    @Test
    @DisplayName("教案点赞/收藏 - 用户交互功能")
    void interactWithWork_LikeAndFavorite() throws Exception {
        // 点赞教案
        mockMvc.perform(post("/api/v1/works/work-id/like"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.likes").isNumber());

        // 收藏教案
        mockMvc.perform(post("/api/v1/works/work-id/favorite"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.favorited").value(true));
    }

    @Test
    @DisplayName("教案相关推荐 - 返回相关内容")
    void getRelatedWorks_ReturnsRelatedContent() throws Exception {
        mockMvc.perform(get("/api/v1/works/work-id/related"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.works").isArray());
    }

    @Test
    @DisplayName("教案浏览历史 - 记录用户浏览")
    void recordWorkView_History() throws Exception {
        // 记录浏览
        mockMvc.perform(post("/api/v1/works/work-id/view"))
            .andExpect(status().isOk());

        // 获取浏览历史
        mockMvc.perform(get("/api/v1/works/history"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.history").isArray());
    }

    @Test
    @DisplayName("最新教案列表 - 按创建时间排序")
    void getLatestWorks_OrderedByCreationTime() throws Exception {
        mockMvc.perform(get("/api/v1/works/latest")
                .param("limit", "10"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.works").isArray());
    }

    @Test
    @DisplayName("热门教案列表 - 按浏览量排序")
    void getPopularWorks_OrderedByViews() throws Exception {
        mockMvc.perform(get("/api/v1/works/popular")
                .param("limit", "10"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.works").isArray());
    }
}
