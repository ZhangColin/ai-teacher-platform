"""AgentService 单元测试"""
import pytest
import sys
import tempfile
import yaml
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.agent_service import AgentService
from src.models import Agent, UIConfig


class TestAgentService:
    """测试 AgentService 类"""
    
    def test_init(self):
        """测试初始化"""
        service = AgentService(config_dir="configs/agents")
        assert service.config_dir == Path("configs/agents")
        assert service._agents_cache is None
        assert service._cache_timestamp is None
    
    def test_load_agent_success(self):
        """测试成功加载 Agent 配置"""
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'agent_id': 'test_agent',
                'name': '测试 Agent',
                'description': '这是一个测试 Agent',
                'system_prompt': '你是一个测试助手',
                'ui_config': {
                    'show_preview': True,
                    'preview_types': ['markdown']
                },
                'capabilities': ['export_text']
            }
            yaml.dump(config_data, f, allow_unicode=True)
            config_path = Path(f.name)
        
        try:
            service = AgentService()
            agent = service.load_agent(config_path)
            
            assert agent is not None
            assert agent.agent_id == 'test_agent'
            assert agent.name == '测试 Agent'
            assert agent.description == '这是一个测试 Agent'
            assert agent.system_prompt == '你是一个测试助手'
            assert agent.ui_config.show_preview is True
            assert 'markdown' in agent.ui_config.preview_types
            assert 'export_text' in agent.capabilities
        finally:
            config_path.unlink()
    
    def test_load_agent_missing_required_fields(self):
        """测试加载缺少必需字段的配置（应该返回 None）"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'agent_id': '',  # 空字符串，验证会失败
                'name': '测试 Agent'
            }
            yaml.dump(config_data, f, allow_unicode=True)
            config_path = Path(f.name)
        
        try:
            service = AgentService()
            agent = service.load_agent(config_path)
            assert agent is None
        finally:
            config_path.unlink()
    
    def test_load_agent_invalid_yaml(self):
        """测试加载无效的 YAML 文件（应该返回 None）"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = Path(f.name)
        
        try:
            service = AgentService()
            agent = service.load_agent(config_path)
            assert agent is None
        finally:
            config_path.unlink()
    
    def test_load_agent_nonexistent_file(self):
        """测试加载不存在的文件（应该返回 None）"""
        service = AgentService()
        agent = service.load_agent(Path("/nonexistent/file.yaml"))
        assert agent is None
    
    def test_load_all_agents_empty_dir(self):
        """测试加载空目录（应该返回空列表）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = AgentService(config_dir=tmpdir)
            agents = service.load_all_agents()
            assert agents == []
    
    def test_load_all_agents_with_valid_configs(self):
        """测试加载多个有效的 Agent 配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建第一个配置文件
            config1_path = Path(tmpdir) / "agent1.yaml"
            with open(config1_path, 'w', encoding='utf-8') as f:
                yaml.dump({
                    'agent_id': 'agent1',
                    'name': 'Agent 1',
                    'system_prompt': 'Prompt 1',
                    'ui_config': {'show_preview': False, 'preview_types': []}
                }, f, allow_unicode=True)
            
            # 创建第二个配置文件
            config2_path = Path(tmpdir) / "agent2.yaml"
            with open(config2_path, 'w', encoding='utf-8') as f:
                yaml.dump({
                    'agent_id': 'agent2',
                    'name': 'Agent 2',
                    'system_prompt': 'Prompt 2',
                    'ui_config': {'show_preview': True, 'preview_types': ['markdown']}
                }, f, allow_unicode=True)
            
            service = AgentService(config_dir=tmpdir)
            agents = service.load_all_agents()
            
            assert len(agents) == 2
            agent_ids = [a.agent_id for a in agents]
            assert 'agent1' in agent_ids
            assert 'agent2' in agent_ids
    
    def test_load_all_agents_with_invalid_configs(self):
        """测试加载包含无效配置的目录（只返回有效的 Agent）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建有效配置
            config1_path = Path(tmpdir) / "valid.yaml"
            with open(config1_path, 'w', encoding='utf-8') as f:
                yaml.dump({
                    'agent_id': 'valid',
                    'name': 'Valid Agent',
                    'system_prompt': 'Valid prompt',
                    'ui_config': {'show_preview': False, 'preview_types': []}
                }, f, allow_unicode=True)
            
            # 创建无效配置（缺少必需字段）
            config2_path = Path(tmpdir) / "invalid.yaml"
            with open(config2_path, 'w', encoding='utf-8') as f:
                yaml.dump({
                    'agent_id': '',  # 空字符串，验证会失败
                    'name': 'Invalid Agent'
                }, f, allow_unicode=True)
            
            service = AgentService(config_dir=tmpdir)
            agents = service.load_all_agents()
            
            # 只应该返回有效的 Agent
            assert len(agents) == 1
            assert agents[0].agent_id == 'valid'
    
    def test_load_all_agents_cache(self):
        """测试缓存机制（5分钟内应该返回缓存）"""
        import time
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "agent.yaml"
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump({
                    'agent_id': 'cached',
                    'name': 'Cached Agent',
                    'system_prompt': 'Cached prompt',
                    'ui_config': {'show_preview': False, 'preview_types': []}
                }, f, allow_unicode=True)
            
            service = AgentService(config_dir=tmpdir)
            
            # 第一次加载
            agents1 = service.load_all_agents()
            assert len(agents1) == 1
            
            # 删除配置文件
            config_path.unlink()
            
            # 第二次加载（应该返回缓存）
            agents2 = service.load_all_agents()
            assert len(agents2) == 1
            assert agents2 == agents1
    
    def test_load_all_agents_supports_yml_extension(self):
        """测试支持 .yml 扩展名"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "agent.yml"
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump({
                    'agent_id': 'yml_agent',
                    'name': 'YML Agent',
                    'system_prompt': 'YML prompt',
                    'ui_config': {'show_preview': False, 'preview_types': []}
                }, f, allow_unicode=True)
            
            service = AgentService(config_dir=tmpdir)
            agents = service.load_all_agents()
            
            assert len(agents) == 1
            assert agents[0].agent_id == 'yml_agent'
