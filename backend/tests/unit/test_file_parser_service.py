# -*- coding: utf-8 -*-
"""文件解析服务测试"""
import pytest
import tempfile
import os
from src.services.file_parser_service import FileParserService


@pytest.fixture
def parser():
    return FileParserService()


@pytest.fixture
def temp_txt_file():
    """创建临时文本文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("测试内容\n这是第二行")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.mark.asyncio
async def test_parse_txt_file(parser, temp_txt_file):
    """测试解析文本文件"""
    result = await parser.parse_file(temp_txt_file, "test.txt")
    assert "测试内容" in result
    assert "这是第二行" in result


@pytest.mark.asyncio
async def test_unsupported_format(parser):
    """测试不支持的格式"""
    with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
        f.write(b"content")
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Unsupported file format"):
            await parser.parse_file(temp_path, "test.xyz")
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_supported_formats(parser):
    """测试支持的格式列表"""
    formats = parser.SUPPORTED_FORMATS
    assert '.txt' in formats
    assert '.pdf' in formats
    assert '.docx' in formats
    assert '.xlsx' in formats
    assert '.pptx' in formats
