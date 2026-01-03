"""Tool 模型单元测试"""
import pytest
from src.models import Tool


class TestTool:
    """测试 Tool 模型"""
    
    def test_tool_creation_with_all_fields(self):
        """测试创建包含所有字段的 Tool"""
        tool = Tool(
            tool_id="test_tool",
            name="测试工具",
            description="这是一个测试工具",
            system_prompt="你是一个测试助手",
            category="智能体",
            icon="command-line",
            visible=True,
            type="normal",
            welcome_message="欢迎使用测试工具"
        )
        
        assert tool.tool_id == "test_tool"
        assert tool.name == "测试工具"
        assert tool.description == "这是一个测试工具"
        assert tool.system_prompt == "你是一个测试助手"
        assert tool.category == "智能体"
        assert tool.icon == "command-line"
        assert tool.visible is True
        assert tool.type == "normal"
        assert tool.welcome_message == "欢迎使用测试工具"
    
    def test_tool_creation_with_minimal_fields(self):
        """测试创建包含最小必需字段的 Tool"""
        tool = Tool(
            tool_id="minimal_tool",
            name="最小工具",
            system_prompt="最小提示词",
            category="智能体",
            welcome_message="欢迎"
        )
        
        assert tool.tool_id == "minimal_tool"
        assert tool.name == "最小工具"
        assert tool.system_prompt == "最小提示词"
        assert tool.category == "智能体"
        assert tool.welcome_message == "欢迎"
        assert tool.description is None
        assert tool.icon is None
        assert tool.visible is True  # 默认值
        assert tool.type == "normal"  # 默认值
    
    def test_tool_visible_default_value(self):
        """测试 visible 字段的默认值为 True"""
        tool = Tool(
            tool_id="test",
            name="测试",
            system_prompt="提示词",
            category="智能体",
            welcome_message="欢迎"
        )
        assert tool.visible is True
    
    def test_tool_type_default_value(self):
        """测试 type 字段的默认值为 normal"""
        tool = Tool(
            tool_id="test",
            name="测试",
            system_prompt="提示词",
            category="智能体",
            welcome_message="欢迎"
        )
        assert tool.type == "normal"
    
    def test_tool_type_placeholder(self):
        """测试 type 字段可以设置为 placeholder"""
        tool = Tool(
            tool_id="placeholder_tool",
            name="占位工具",
            system_prompt="提示词",
            category="智能体",
            welcome_message="欢迎",
            type="placeholder"
        )
        assert tool.type == "placeholder"
    
    def test_tool_validate_success(self):
        """测试验证成功的 Tool"""
        tool = Tool(
            tool_id="valid_tool",
            name="有效工具",
            system_prompt="有效提示词",
            category="智能体",
            welcome_message="欢迎使用"
        )
        assert tool.validate() is True
    
    def test_tool_validate_missing_tool_id(self):
        """测试缺少 tool_id 的 Tool 验证失败"""
        tool = Tool(
            tool_id="",  # 空字符串
            name="工具",
            system_prompt="提示词",
            category="智能体",
            welcome_message="欢迎"
        )
        assert tool.validate() is False
    
    def test_tool_validate_missing_name(self):
        """测试缺少 name 的 Tool 验证失败"""
        tool = Tool(
            tool_id="test",
            name="",  # 空字符串
            system_prompt="提示词",
            category="智能体",
            welcome_message="欢迎"
        )
        assert tool.validate() is False
    
    def test_tool_validate_missing_system_prompt(self):
        """测试缺少 system_prompt 的 Tool 验证失败"""
        tool = Tool(
            tool_id="test",
            name="工具",
            system_prompt="",  # 空字符串
            category="智能体",
            welcome_message="欢迎"
        )
        assert tool.validate() is False
    
    def test_tool_validate_missing_category(self):
        """测试缺少 category 的 Tool 验证失败"""
        tool = Tool(
            tool_id="test",
            name="工具",
            system_prompt="提示词",
            category="",  # 空字符串
            welcome_message="欢迎"
        )
        assert tool.validate() is False
    
    def test_tool_validate_missing_welcome_message(self):
        """测试缺少 welcome_message 的 Tool 验证失败"""
        tool = Tool(
            tool_id="test",
            name="工具",
            system_prompt="提示词",
            category="智能体",
            welcome_message=""  # 空字符串
        )
        assert tool.validate() is False

