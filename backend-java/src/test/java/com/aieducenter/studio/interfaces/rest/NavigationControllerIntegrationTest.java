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
 * NavigationController集成测试
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
@DisplayName("NavigationController集成测试")
class NavigationControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("获取导航配置 - 成功")
    void getNavigation_Success() throws Exception {
        mockMvc.perform(get("/api/v1/navigation"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.modules").isArray());
    }

    @Test
    @DisplayName("获取所有工具 - 成功")
    void getAllTools_Success() throws Exception {
        mockMvc.perform(get("/api/v1/tools"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.tools").isArray());
    }

    @Test
    @DisplayName("按工具集获取工具 - 成功")
    void getToolsByToolset_Success() throws Exception {
        mockMvc.perform(get("/api/v1/toolsets/test-toolset/tools"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.tools").isArray());
    }
}
