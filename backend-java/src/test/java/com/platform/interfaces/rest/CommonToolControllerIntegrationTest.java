package com.platform.interfaces.rest;

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
 * CommonToolController集成测试
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
@DisplayName("CommonToolController集成测试")
class CommonToolControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("获取工具分类 - 成功")
    void getCategories_Success() throws Exception {
        mockMvc.perform(get("/api/v1/common-tools/categories"))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("获取工具详情 - 成功")
    void getToolDetail_Success() throws Exception {
        mockMvc.perform(get("/api/v1/common-tools/test-tool-id"))
            .andExpect(status().isOk());
    }

    @Test
    @DisplayName("Markdown转Word - 成功")
    void convertMarkdownToWord_Success() throws Exception {
        String request = """
            {
                "markdown": "# 测试Markdown\\n\\n这是测试内容"
            }
            """;

        mockMvc.perform(post("/api/v1/convert/markdown-to-word")
                .contentType(MediaType.APPLICATION_JSON)
                .content(request))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.task_id").isString());
    }

    @Test
    @DisplayName("查询任务状态 - 成功")
    void getTaskStatus_Success() throws Exception {
        mockMvc.perform(get("/api/v1/tasks/test-task-id"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.task_id").value("test-task-id"))
            .andExpect(jsonPath("$.status").isString());
    }
}
