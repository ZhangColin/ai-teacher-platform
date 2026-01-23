"""测试多模态数据模型"""
import pytest
import json
from datetime import datetime
from src.models import (
    Message,
    MultiModalContent,
    Tool,
    MediaGenerateRequest,
    MediaGenerateResponse,
    TaskStatusResponse
)


class TestMultiModalContent:
    """测试MultiModalContent模型"""
    
    def test_create_image_content(self):
        """测试创建图片内容"""
        content = MultiModalContent(
            content_type="image",
            media_urls=["https://example.com/image1.png", "https://example.com/image2.png"],
            metadata={
                "size": "1024x1024",
                "count": 2,
                "style": "auto"
            }
        )
        
        assert content.content_type == "image"
        assert len(content.media_urls) == 2
        assert content.metadata["size"] == "1024x1024"
        assert content.metadata["count"] == 2
    
    def test_create_audio_content(self):
        """测试创建音频内容"""
        content = MultiModalContent(
            content_type="audio",
            media_urls=["https://example.com/audio.mp3"],
            metadata={
                "duration": 30,
                "format": "mp3"
            }
        )
        
        assert content.content_type == "audio"
        assert content.media_urls[0].endswith(".mp3")
    
    def test_create_video_content(self):
        """测试创建视频内容"""
        content = MultiModalContent(
            content_type="video",
            media_urls=["https://example.com/video.mp4"],
            metadata={
                "duration": 60,
                "resolution": "1080p"
            }
        )
        
        assert content.content_type == "video"
        assert "duration" in content.metadata


class TestMessage:
    """测试Message模型的多模态支持"""
    
    def test_text_message(self):
        """测试普通文本消息（保持向后兼容）"""
        message = Message(
            role="user",
            content="这是一条文本消息"
        )
        
        assert message.content == "这是一条文本消息"
        assert message.media_content is None
        assert message.parsed_media_content is None
    
    def test_multimodal_message_with_json_string(self):
        """测试带多模态内容的消息（JSON字符串）"""
        media_json = json.dumps({
            "content_type": "image",
            "media_urls": ["https://example.com/image.png"],
            "metadata": {"size": "1024x1024"}
        }, ensure_ascii=False)
        
        message = Message(
            role="assistant",
            content="生成的图片",
            media_content=media_json
        )
        
        assert message.media_content is not None
        parsed = message.parsed_media_content
        assert parsed is not None
        assert parsed.content_type == "image"
        assert len(parsed.media_urls) == 1
        assert parsed.metadata["size"] == "1024x1024"
    
    def test_set_media_content(self):
        """测试设置多模态内容"""
        message = Message(
            role="assistant",
            content="生成的图片"
        )
        
        media = MultiModalContent(
            content_type="image",
            media_urls=["https://example.com/image1.png", "https://example.com/image2.png"],
            metadata={"count": 2}
        )
        
        message.set_media_content(media)
        
        assert message.media_content is not None
        parsed = message.parsed_media_content
        assert parsed is not None
        assert parsed.content_type == "image"
        assert len(parsed.media_urls) == 2
    
    def test_invalid_media_content_json(self):
        """测试无效的JSON字符串（应该优雅降级）"""
        message = Message(
            role="assistant",
            content="测试",
            media_content="invalid json"
        )
        
        # 应该返回None而不是抛出异常
        assert message.parsed_media_content is None


class TestTool:
    """测试Tool模型的多模态支持"""
    
    def test_text_tool_validation(self):
        """测试文本工具验证（默认）"""
        tool = Tool(
            tool_id="text_gen",
            name="文字对话",
            category="内容生成",
            welcome_message="你好！",
            system_prompt="你是一个助手"
        )
        
        assert tool.content_type == "text"
        assert tool.media_type is None
        assert tool.validate() is True
    
    def test_multimodal_image_tool_validation(self):
        """测试多模态图片工具验证"""
        tool = Tool(
            tool_id="image_gen",
            name="文生图",
            category="内容生成",
            welcome_message="你好！",
            system_prompt="你是一个图片生成助手",
            content_type="multimodal",
            media_type="image",
            model="glm:cogview-4"
        )
        
        assert tool.content_type == "multimodal"
        assert tool.media_type == "image"
        assert tool.validate() is True
    
    def test_multimodal_tool_without_media_type_fails_validation(self):
        """测试多模态工具缺少media_type应该验证失败"""
        tool = Tool(
            tool_id="invalid_tool",
            name="无效工具",
            category="测试",
            welcome_message="你好！",
            system_prompt="测试",
            content_type="multimodal"
            # 缺少 media_type
        )
        
        assert tool.validate() is False


class TestMediaGenerateRequest:
    """测试多模态生成请求"""
    
    def test_create_request_with_defaults(self):
        """测试使用默认参数创建请求"""
        request = MediaGenerateRequest(
            message="生成一张猫的图片"
        )
        
        assert request.message == "生成一张猫的图片"
        assert request.session_id is None
        assert request.size == "1024x1024"
        assert request.count == 1
        assert request.style == "auto"
    
    def test_create_request_with_custom_params(self):
        """测试使用自定义参数创建请求"""
        request = MediaGenerateRequest(
            message="生成四张风景图",
            session_id="session_123",
            size="1024x1792",
            count=4,
            style="realistic"
        )
        
        assert request.count == 4
        assert request.size == "1024x1792"
        assert request.style == "realistic"
    
    def test_count_validation(self):
        """测试数量验证（1-4）"""
        # 有效值
        request = MediaGenerateRequest(message="test", count=1)
        assert request.count == 1
        
        request = MediaGenerateRequest(message="test", count=4)
        assert request.count == 4
        
        # 无效值应该被Pydantic拒绝
        with pytest.raises(Exception):
            MediaGenerateRequest(message="test", count=0)
        
        with pytest.raises(Exception):
            MediaGenerateRequest(message="test", count=5)


class TestMediaGenerateResponse:
    """测试多模态生成响应"""
    
    def test_create_response(self):
        """测试创建响应"""
        response = MediaGenerateResponse(
            session_id="session_123",
            message_id="msg_456",
            task_id="task_789",
            status="pending"
        )
        
        assert response.session_id == "session_123"
        assert response.message_id == "msg_456"
        assert response.task_id == "task_789"
        assert response.status in ["pending", "processing"]


class TestTaskStatusResponse:
    """测试任务状态响应"""
    
    def test_pending_status(self):
        """测试等待状态"""
        response = TaskStatusResponse(
            task_id="task_123",
            status="pending"
        )
        
        assert response.status == "pending"
        assert response.progress is None
        assert response.media_urls is None
    
    def test_processing_status(self):
        """测试处理中状态"""
        response = TaskStatusResponse(
            task_id="task_123",
            status="processing",
            progress=50
        )
        
        assert response.status == "processing"
        assert response.progress == 50
    
    def test_completed_status(self):
        """测试完成状态"""
        response = TaskStatusResponse(
            task_id="task_123",
            status="completed",
            content_type="image",
            media_urls=["https://example.com/image1.png", "https://example.com/image2.png"],
            metadata={"size": "1024x1024", "count": 2}
        )
        
        assert response.status == "completed"
        assert response.content_type == "image"
        assert len(response.media_urls) == 2
        assert response.metadata["count"] == 2
    
    def test_failed_status(self):
        """测试失败状态"""
        response = TaskStatusResponse(
            task_id="task_123",
            status="failed",
            error_message="生成失败：内容违规"
        )
        
        assert response.status == "failed"
        assert response.error_message == "生成失败：内容违规"
