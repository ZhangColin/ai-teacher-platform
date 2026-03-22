# -*- coding: utf-8 -*-
"""文件上传 API 测试"""
import pytest
import tempfile
import os

@pytest.fixture
def test_file():
    """创建测试文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("这是测试文件内容")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.mark.asyncio
async def test_upload_file_text_extraction_mode(logged_in_client, test_file):
    """测试文本提取模式（DeepSeek 等）"""
    # 使用 logged_in_client fixture（已包含认证）
    with open(test_file, 'rb') as f:
        response = await logged_in_client.post(
            "/api/v1/files/upload?provider=deepseek",
            files={"file": ("test.txt", f, "text/plain")}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["mode"] == "text_extraction"
    assert "content" in data
    assert "测试文件内容" in data["content"]
