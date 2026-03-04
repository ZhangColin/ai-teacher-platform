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
 * MediaController集成测试
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
@DisplayName("MediaController集成测试")
class MediaControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("生成多模态内容 - 成功")
    @WithMockUser(username = "testuser")
    void generateMedia_Success() throws Exception {
        String requestJson = """
            {
                "prompt": "生成一张测试图片",
                "mediaType": "image"
            }
            """;

        mockMvc.perform(post("/api/v1/tools/test-tool-id/generate-media")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.mediaId").isString())
            .andExpect(jsonPath("$.url").isString());
    }

    @Test
    @DisplayName("生成图片 - 返回completed状态")
    @WithMockUser(username = "testuser")
    void generateImage_ReturnsCompletedStatus() throws Exception {
        String requestJson = """
            {
                "prompt": "生成一张猫的图片",
                "mediaType": "image"
            }
            """;

        mockMvc.perform(post("/api/v1/tools/test-tool-id/generate-media")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("completed"));
    }
}
