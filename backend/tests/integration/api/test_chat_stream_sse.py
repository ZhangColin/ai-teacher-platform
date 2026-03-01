"""
测试聊天流式API的SSE格式

验证后端返回的SSE数据格式正确，前端可以解析

注意：这些测试暂时被跳过，需要重构依赖注入架构后才能运行。
原因说明见 test_title_generation.py
"""
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.mark.skip(reason="待修复：需要重构服务层依赖注入架构")
@pytest.mark.asyncio
async def test_chat_stream_sse_format(async_client: AsyncClient, auth_headers):
    """测试流式聊天API返回的SSE格式正确"""
    response = await async_client.post(
        "/api/v1/tools/text_gen/chat/stream",
        json={
            "message": "Hello",
            "session_id": None,
            "history": []
        },
        headers=auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # 读取响应内容
    content = response.text
    print(f"\n=== SSE Response ===\n{content}\n=== End of SSE ===\n")

    # 验证SSE格式
    lines = content.split('\n')
    content_chunks = []

    for line in lines:
        if line.strip().startswith('data: '):
            data_str = line.strip()[6:].strip()  # 去掉 'data: '

            if data_str == '[DONE]':
                print("✓ Found [DONE] marker")
                break

            try:
                data = eval(data_str)  # 使用eval解析Python字典格式
                assert 'content' in data, f"Missing 'content' in {data}"
                content_chunks.append(data['content'])
                print(f"✓ Chunk: {repr(data['content'][:20])}")
            except Exception as e:
                pytest.fail(f"Failed to parse SSE data: {data_str}, error: {e}")

    # 验证至少收到一些内容
    assert len(content_chunks) > 0, "No content chunks received"
    full_content = ''.join(content_chunks)
    assert len(full_content) > 0, "Full response is empty"
    print(f"\n✓ Total content length: {len(full_content)} characters")


@pytest.mark.skip(reason="待修复：需要重构服务层依赖注入架构")
@pytest.mark.asyncio
async def test_chat_stream_with_real_ai(async_client: AsyncClient, auth_headers):
    """测试完整的流式对话（使用真实AI）"""
    response = await async_client.post(
        "/api/v1/tools/text_gen/chat/stream",
        json={
            "message": "Say 'Hello World' in 5 words",
            "session_id": None,
            "history": []
        },
        headers=auth_headers
    )

    assert response.status_code == 200

    # 收集所有内容
    content = response.text
    print(f"\n=== Full SSE Response ===\n{content}\n=== End ===\n")

    # 验证有[DONE]标记
    assert '[DONE]' in content, "Missing [DONE] marker in SSE stream"

    # 验证有content数据
    assert 'data: ' in content, "No data lines in SSE stream"

    print("\n✓ SSE format is correct")
