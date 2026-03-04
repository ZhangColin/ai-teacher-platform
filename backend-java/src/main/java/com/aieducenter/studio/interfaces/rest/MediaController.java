package com.platform.interfaces.rest;

import com.platform.interfaces.rest.dto.UserInfo;
import com.platform.interfaces.rest.dto.media.MediaGenerateRequest;
import com.platform.interfaces.rest.dto.media.MediaGenerateResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

/**
 * 媒体生成控制器
 *
 * 对应Python: backend/src/interfaces/routers/tools/media.py
 *
 * 端点列表：
 * - POST /api/v1/tools/{tool_id}/generate-media - 生成多模态内容
 *
 * @author AI Teacher Platform
 */
@RestController
@RequestMapping("/api/v1/tools")
public class MediaController {

    private static final Logger logger = LoggerFactory.getLogger(MediaController.class);

    /**
     * 生成多模态内容
     * POST /api/v1/tools/{tool_id}/generate-media
     */
    @PostMapping("/{tool_id}/generate-media")
    public ResponseEntity<MediaGenerateResponse> generateMedia(
            @PathVariable("tool_id") String toolId,
            @RequestBody MediaGenerateRequest request,
            @AuthenticationPrincipal UserInfo currentUser
    ) {
        try {
            // TODO: 实现媒体生成逻辑
            // 1. 调用AI服务生成图片/视频
            // 2. 保存媒体文件
            // 3. 返回媒体URL

            logger.info("生成媒体请求 - 工具ID: {}, 提示词: {}", toolId, request.getPrompt());

            // 临时实现：返回模拟响应
            return ResponseEntity.ok(MediaGenerateResponse.builder()
                .mediaId("mock-media-id")
                .mediaType(request.getMediaType())
                .url("https://example.com/media/mock.jpg")
                .status("completed")
                .build());
        } catch (Exception e) {
            logger.error("生成媒体失败: {}", e.getMessage(), e);
            throw new RuntimeException("生成媒体失败: " + e.getMessage());
        }
    }
}
