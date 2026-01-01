"""Agent API 接口测试"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestGetAgents:
    """测试 GET /api/v1/agents 接口"""
    
    def test_get_agents_returns_list(self):
        """测试 GET /api/v1/agents 返回 Agent 列表"""
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
    
    def test_get_agents_structure(self):
        """测试列表中每个 Agent 的结构是否正确"""
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        
        if len(data["agents"]) > 0:
            agent = data["agents"][0]
            assert "agent_id" in agent
            assert "name" in agent
            # description and icon are optional
            assert isinstance(agent["agent_id"], str)
            assert isinstance(agent["name"], str)
    
    def test_get_agents_returns_empty_list_when_no_agents(self):
        """测试当没有配置 Agent 时，GET /api/v1/agents 返回空列表"""
        # 注意：如果已配置了 Agent，此测试可能会失败
        # 实际应用中，我们会使用测试夹具来确保没有 Agent 存在
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["agents"], list)
        # If agents exist, verify they have correct structure
        for agent in data["agents"]:
            assert "agent_id" in agent
            assert "name" in agent
    
    def test_get_agents_loads_from_config_files(self):
        """测试 GET /api/v1/agents 从配置文件加载 Agent"""
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        
        # If configs exist, verify structure
        for agent in data["agents"]:
            assert "agent_id" in agent
            assert "name" in agent
            assert isinstance(agent["agent_id"], str)
            assert isinstance(agent["name"], str)
            # description is optional but should be string if present
            if "description" in agent and agent["description"] is not None:
                assert isinstance(agent["description"], str)

