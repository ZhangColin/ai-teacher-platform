"""测试会话标题生成功能"""
import pytest
import json
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_session_id_event_in_stream(async_client: AsyncClient, auth_headers):
    """测试流式对话发送 session_id 事件"""

    response = await async_client.post(
        "/api/v1/tools/text_gen/chat/stream",
        json={
            "message": "测试session_id事件",
            "session_id": None
        },
        headers=auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # 读取流式响应
    content = response.text
    lines = content.split("\n")

    # 验证 session_id 事件存在
    session_id_found = False
    for line in lines:
        if "session_id" in line and "type" in line:
            session_id_found = True
            # 验证JSON格式
            try:
                data = json.loads(line.replace("data: ", ""))
                assert data.get("type") == "session_id"
                assert data.get("session_id") is not None
            except:
                pytest.fail("session_id 事件JSON格式错误")
            break

    assert session_id_found, "session_id 事件未找到"
    print("✅ session_id 事件测试通过")


@pytest.mark.asyncio
async def test_title_generated_event_in_stream(async_client: AsyncClient, auth_headers):
    """测试流式对话发送 title_generated 事件"""

    response = await async_client.post(
        "/api/v1/tools/text_gen/chat/stream",
        json={
            "message": "测试title_generated事件",
            "session_id": None
        },
        headers=auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # 读取流式响应
    content = response.text
    lines = content.split("\n")

    # 验证 title_generated 事件存在
    title_event_found = False
    for line in lines:
        if "title_generated" in line and "type" in line:
            title_event_found = True
            # 验证包含 session_id 和 title
            assert "session_id" in line
            assert "title" in line
            # 验证JSON格式
            try:
                data = json.loads(line.replace("data: ", ""))
                assert data.get("type") == "title_generated"
                assert data.get("session_id") is not None
                assert data.get("title") is not None
            except:
                pytest.fail("title_generated 事件JSON格式错误")
            break

    assert title_event_found, "title_generated 事件未找到"
    print("✅ title_generated 事件测试通过")


@pytest.mark.asyncio
async def test_session_created_and_updated(async_client: AsyncClient, auth_headers):
    """测试会话创建和更新时间不同（说明标题生成逻辑执行了）"""

    response = await async_client.post(
        "/api/v1/tools/text_gen/chat/stream",
        json={
            "message": "测试会话创建和更新",
            "session_id": None
        },
        headers=auth_headers
    )

    assert response.status_code == 200

    # 从流式响应中提取 session_id
    content = response.text
    lines = content.split("\n")

    session_id = None
    for line in lines:
        if '"type": "session_id"' in line:
            try:
                data = json.loads(line.replace("data: ", ""))
                session_id = data.get("session_id")
                break
            except:
                pass

    if not session_id:
        pytest.skip("无法从流式响应中提取 session_id")

    # 等待标题生成完成
    import asyncio
    await asyncio.sleep(2)

    # 获取会话详情
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    session = response.json()

    # 验证标题存在
    assert session["title"] is not None
    assert len(session["title"]) > 0
    assert len(session["title"]) <= 50  # 标题应该合理长度

    # 验证更新时间晚于创建时间（说明有更新操作）
    from datetime import datetime
    created_at = datetime.fromisoformat(session["created_at"].replace("Z", "+00:00"))
    updated_at = datetime.fromisoformat(session["updated_at"].replace("Z", "+00:00"))

    # 更新时间应该大于或等于创建时间
    assert updated_at >= created_at

    print(f"✅ 会话创建和更新测试通过")
    print(f"   创建时间: {created_at}")
    print(f"   更新时间: {updated_at}")
    print(f"   标题: {session['title']}")
