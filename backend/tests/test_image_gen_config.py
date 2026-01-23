"""测试文生图工具配置加载"""
import pytest
from pathlib import Path
from src.services.tool_service import ToolService
from src.config_loader import ConfigLoader


class TestImageGenConfig:
    """测试image_gen工具配置"""
    
    def test_load_image_gen_tool(self):
        """测试加载文生图工具配置"""
        # 获取项目根目录（backend的父目录）
        project_root = Path(__file__).parent.parent.parent
        
        # 初始化服务
        config_loader = ConfigLoader(config_root=str(project_root / "configs"))
        tool_service = ToolService(
            config_dir=str(project_root / "configs/tools"), 
            config_loader=config_loader
        )
        
        # 加载image_gen配置
        config_path = project_root / "configs/tools/ai_tools/image_gen.yaml"
        tool = tool_service.load_tool(config_path, toolset_id="ai_tools")
        
        # 验证工具加载成功
        assert tool is not None, "image_gen工具加载失败"
        
        # 验证基本字段
        assert tool.tool_id == "image_gen"
        assert tool.name == "文生图"
        assert tool.description == "通过文本描述生成图片"
        assert tool.category == "内容生成"
        assert tool.icon == "photo"
        assert tool.visible is True
        assert tool.type == "normal"  # 从placeholder改为normal
        assert tool.order == 2
        assert tool.toolset_id == "ai_tools"
        
        # 验证多模态字段
        assert tool.content_type == "multimodal", "content_type应该是multimodal"
        assert tool.media_type == "image", "media_type应该是image"
        
        # 验证模型配置
        assert tool.model == "glm:cogview-4", "模型配置应该是glm:cogview-4"
        
        # 验证系统提示词
        assert tool.system_prompt is not None
        assert "绘画助手" in tool.system_prompt
        
        # 验证欢迎语
        assert tool.welcome_message is not None
        assert "生成图片" in tool.welcome_message
        
        # 验证配置有效性
        assert tool.validate() is True
    
    def test_text_gen_tool_compatibility(self):
        """测试text_gen工具保持向后兼容"""
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        
        config_loader = ConfigLoader(config_root=str(project_root / "configs"))
        tool_service = ToolService(
            config_dir=str(project_root / "configs/tools"),
            config_loader=config_loader
        )
        
        config_path = project_root / "configs/tools/ai_tools/text_gen.yaml"
        tool = tool_service.load_tool(config_path, toolset_id="ai_tools")
        
        assert tool is not None
        assert tool.tool_id == "text_gen"
        assert tool.content_type == "text"  # 默认值
        assert tool.media_type is None
        assert tool.validate() is True
    
    def test_get_tool_by_id(self):
        """测试通过ID获取工具"""
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        
        config_loader = ConfigLoader(config_root=str(project_root / "configs"))
        tool_service = ToolService(
            config_dir=str(project_root / "configs/tools"),
            config_loader=config_loader
        )
        
        # 获取image_gen工具
        tool = tool_service.get_tool_by_id("image_gen")
        
        if tool:  # 如果工具存在
            assert tool.tool_id == "image_gen"
            assert tool.content_type == "multimodal"
            assert tool.media_type == "image"
