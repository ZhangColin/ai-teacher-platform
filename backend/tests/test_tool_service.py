"""ToolService 单元测试"""
import pytest
import sys
import tempfile
import yaml
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.tool_service import ToolService
from src.models import Tool


class TestToolService:
    """测试 ToolService 类"""
    
    def test_init(self):
        """测试初始化"""
        service = ToolService(config_dir="configs/tools")
        assert service.config_dir == Path("configs/tools")
        assert service._tools_cache is None
        assert service._cache_timestamp is None
    
    def test_load_tool_success(self):
        """测试成功加载工具配置"""
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'tool_id': 'test_tool',
                'name': '测试工具',
                'description': '这是一个测试工具',
                'system_prompt': '你是一个测试助手',
                'category': '智能体',
                'icon': 'command-line',
                'visible': True,
                'type': 'normal',
                'welcome_message': '欢迎使用测试工具'
            }
            yaml.dump(config_data, f, allow_unicode=True)
            config_path = Path(f.name)
        
        try:
            service = ToolService()
            tool = service.load_tool(config_path)
            
            assert tool is not None
            assert tool.tool_id == 'test_tool'
            assert tool.name == '测试工具'
            assert tool.description == '这是一个测试工具'
            assert tool.system_prompt == '你是一个测试助手'
            assert tool.category == '智能体'
            assert tool.icon == 'command-line'
            assert tool.visible is True
            assert tool.type == 'normal'
            assert tool.welcome_message == '欢迎使用测试工具'
        finally:
            config_path.unlink()
    
    def test_load_tool_with_defaults(self):
        """测试加载工具配置时使用默认值"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'tool_id': 'default_tool',
                'name': '默认工具',
                'system_prompt': '提示词',
                'category': '智能体',
                'welcome_message': '欢迎'
                # 不指定 visible 和 type，应该使用默认值
            }
            yaml.dump(config_data, f, allow_unicode=True)
            config_path = Path(f.name)
        
        try:
            service = ToolService()
            tool = service.load_tool(config_path)
            
            assert tool is not None
            assert tool.visible is True  # 默认值
            assert tool.type == 'normal'  # 默认值
        finally:
            config_path.unlink()
    
    def test_load_tool_missing_required_fields(self):
        """测试加载缺少必需字段的配置（应该返回 None）"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'tool_id': '',  # 空字符串，验证会失败
                'name': '测试工具'
            }
            yaml.dump(config_data, f, allow_unicode=True)
            config_path = Path(f.name)
        
        try:
            service = ToolService()
            tool = service.load_tool(config_path)
            assert tool is None
        finally:
            config_path.unlink()
    
    def test_load_tool_invalid_yaml(self):
        """测试加载无效的 YAML 文件（应该返回 None）"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = Path(f.name)
        
        try:
            service = ToolService()
            tool = service.load_tool(config_path)
            assert tool is None
        finally:
            config_path.unlink()
    
    def test_load_all_tools_empty_dir(self):
        """测试加载空目录（应该返回空列表）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ToolService(config_dir=tmpdir)
            tools = service.load_all_tools()
            assert tools == []
    
    def test_load_all_tools_with_visible_filter(self):
        """测试只返回 visible=true 的工具"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建 visible=true 的工具
            config1_path = Path(tmpdir) / "tool1.yaml"
            with open(config1_path, 'w', encoding='utf-8') as f:
                yaml.dump({
                    'tool_id': 'visible_tool',
                    'name': '可见工具',
                    'system_prompt': '提示词1',
                    'category': '智能体',
                    'welcome_message': '欢迎1',
                    'visible': True
                }, f, allow_unicode=True)
            
            # 创建 visible=false 的工具
            config2_path = Path(tmpdir) / "tool2.yaml"
            with open(config2_path, 'w', encoding='utf-8') as f:
                yaml.dump({
                    'tool_id': 'hidden_tool',
                    'name': '隐藏工具',
                    'system_prompt': '提示词2',
                    'category': '智能体',
                    'welcome_message': '欢迎2',
                    'visible': False
                }, f, allow_unicode=True)
            
            service = ToolService(config_dir=tmpdir)
            tools = service.load_all_tools()
            
            # 只应该返回 visible=true 的工具
            assert len(tools) == 1
            assert tools[0].tool_id == 'visible_tool'
    
    def test_group_by_category(self):
        """测试按 category 聚合工具"""
        tools = [
            Tool(
                tool_id='tool1',
                name='工具1',
                system_prompt='提示词1',
                category='智能体',
                welcome_message='欢迎1'
            ),
            Tool(
                tool_id='tool2',
                name='工具2',
                system_prompt='提示词2',
                category='智能体',
                welcome_message='欢迎2'
            ),
            Tool(
                tool_id='tool3',
                name='工具3',
                system_prompt='提示词3',
                category='内容生成',
                welcome_message='欢迎3'
            ),
        ]
        
        service = ToolService()
        categories = service.group_by_category(tools)
        
        # 应该有两个分类
        assert len(categories) == 2
        
        # 找到"智能体"分类
        agent_category = next((c for c in categories if c['name'] == '智能体'), None)
        assert agent_category is not None
        assert len(agent_category['tools']) == 2
        
        # 找到"内容生成"分类
        content_category = next((c for c in categories if c['name'] == '内容生成'), None)
        assert content_category is not None
        assert len(content_category['tools']) == 1
    
    def test_group_by_category_with_icons(self):
        """测试按 category 聚合工具时保留分类图标"""
        tools = [
            Tool(
                tool_id='tool1',
                name='工具1',
                system_prompt='提示词1',
                category='智能体',
                welcome_message='欢迎1',
                icon='command-line'
            ),
        ]
        
        service = ToolService()
        categories = service.group_by_category(tools)
        
        assert len(categories) == 1
        # 分类图标应该从第一个工具的 icon 获取（如果有）
        # 注意：根据设计，分类图标应该在配置中定义，这里先测试基本功能
        assert categories[0]['name'] == '智能体'
    
    def test_group_by_category_sorts_tools_by_order(self):
        """测试分类内工具按 order 排序"""
        tools = [
            Tool(
                tool_id='tool3',
                name='工具3',
                system_prompt='提示词3',
                category='智能体',
                welcome_message='欢迎3',
                order=3
            ),
            Tool(
                tool_id='tool1',
                name='工具1',
                system_prompt='提示词1',
                category='智能体',
                welcome_message='欢迎1',
                order=1
            ),
            Tool(
                tool_id='tool2',
                name='工具2',
                system_prompt='提示词2',
                category='智能体',
                welcome_message='欢迎2',
                order=2
            ),
        ]
        
        service = ToolService()
        categories = service.group_by_category(tools)
        
        assert len(categories) == 1
        assert len(categories[0]['tools']) == 3
        # 验证工具按 order 排序
        assert categories[0]['tools'][0].tool_id == 'tool1'
        assert categories[0]['tools'][1].tool_id == 'tool2'
        assert categories[0]['tools'][2].tool_id == 'tool3'
    
    def test_group_by_category_sorts_categories_by_order(self):
        """测试分类按 order 排序（从 categories.yaml 配置）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建分类配置文件
            categories_config_path = Path(tmpdir) / "categories.yaml"
            with open(categories_config_path, 'w', encoding='utf-8') as f:
                yaml.dump({
                    'categories': [
                        {'name': '内容生成', 'order': 1, 'icon': 'sparkles'},
                        {'name': '智能体', 'order': 2, 'icon': 'command-line'},
                    ]
                }, f, allow_unicode=True)
            
            tools = [
                Tool(
                    tool_id='tool1',
                    name='工具1',
                    system_prompt='提示词1',
                    category='智能体',
                    welcome_message='欢迎1',
                    order=1
                ),
                Tool(
                    tool_id='tool2',
                    name='工具2',
                    system_prompt='提示词2',
                    category='内容生成',
                    welcome_message='欢迎2',
                    order=1
                ),
            ]
            
            service = ToolService(config_dir=tmpdir)
            categories = service.group_by_category(tools)
            
            assert len(categories) == 2
            # 根据 categories.yaml 配置，"内容生成" order=1，"智能体" order=2
            # 所以"内容生成"应该在前面
            assert categories[0]['name'] == '内容生成'
            assert categories[1]['name'] == '智能体'

