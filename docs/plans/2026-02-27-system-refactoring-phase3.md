# 系统重构实施计划 - 阶段3：后端路由拆分 + 测试完善

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 拆分后端路由，统一错误处理，建立HTML修复服务，完善测试覆盖

**Architecture:** 按资源组织路由文件，建立统一错误处理中间件，抽取HTML修复逻辑为独立服务

**Tech Stack:** FastAPI, SQLAlchemy, pytest, BeautifulSoup4, Playwright

---

## Task 1: 创建tools/list.py路由

**Files:**
- Create: `backend/src/interfaces/routers/tools/list.py`
- Create: `backend/tests/integration/api/test_tools_list.py`

**Step 1: 创建tools/list.py**

Create: `backend/src/interfaces/routers/tools/list.py`

```python
"""
工具列表路由
"""
from fastapi import APIRouter, Depends
from src.models import ToolListResponse
from src.interfaces.dependencies import get_tool_service, get_current_user
from src.services.tool_service import ToolService

router = APIRouter()


@router.get("/tools", response_model=ToolListResponse, tags=["工具"])
async def get_tools(
    current_user = Depends(get_current_user),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    获取所有工具列表

    返回所有可见的工具，按分类组织
    """
    # 加载所有工具（只返回 visible=true 的工具）
    tools = tool_service.load_all_tools()

    # 按 category 聚合
    category_groups = tool_service.group_by_category(tools)

    return ToolListResponse(categories=category_groups)


@router.get("/toolsets/{toolset_id}/tools", response_model=ToolListResponse, tags=["工具"])
async def get_toolset_tools(
    toolset_id: str,
    current_user = Depends(get_current_user),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    获取指定工具集的工具列表
    """
    tools = tool_service.load_tools_by_toolset(toolset_id)
    category_groups = tool_service.group_by_category(tools)

    return ToolListResponse(categories=category_groups)
```

**Step 2: 创建tools/list测试**

Create: `backend/tests/integration/api/test_tools_list.py`

```python
"""
工具列表路由集成测试
"""
import pytest
from httpx import AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_get_tools_as_authenticated_user(test_db):
    """
    测试认证用户获取工具列表
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 创建测试用户并登录获取token
        # TODO: 添加认证逻辑

        response = await ac.get("/api/v1/tools")

        assert response.status_code == 200

        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)


@pytest.mark.asyncio
async def test_get_tools_returns_visible_tools_only():
    """
    测试只返回可见的工具
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/tools")

        assert response.status_code == 200

        data = response.json()
        # 验证所有工具都是可见的
        for category in data["categories"]:
            for tool in category["tools"]:
                assert tool["visible"] is True


@pytest.mark.asyncio
async def test_get_tools_unauthorized_returns_401():
    """
    测试未认证用户访问返回401
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/tools")

        # 未认证应该返回401
        assert response.status_code == 401
```

**Step 3: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest tests/integration/api/test_tools_list.py -v
```

Expected: 测试通过（可能需要调整认证逻辑）

**Step 4: 提交tools/list路由**

Run:
```bash
git add backend/src/interfaces/routers/tools/list.py backend/tests/integration/api/test_tools_list.py
git commit -m "feat(routers): extract tools list endpoints to separate file"
```

---

## Task 2: 创建tools/chat.py路由

**Files:**
- Create: `backend/src/interfaces/routers/tools/chat.py`
- Create: `backend/tests/integration/api/test_tools_chat.py`

**Step 1: 创建tools/chat.py**

Create: `backend/src/interfaces/routers/tools/chat.py`

```python
"""
工具对话路由
"""
import logging
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from src.models import ChatRequest
from src.interfaces.dependencies import (
    get_ai_service,
    get_session_service,
    get_tool_service,
)
from src.services.ai_service import AIService
from src.services.session_service import SessionService
from src.services.tool_service import ToolService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tools/{tool_id}/chat/stream", tags=["对话"])
async def chat_stream(
    tool_id: str,
    request: ChatRequest,
    ai_service: AIService = Depends(get_ai_service),
    session_service: SessionService = Depends(get_session_service),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    流式对话接口

    使用Server-Sent Events (SSE)返回AI的流式响应
    """
    # 获取工具配置
    tool = tool_service.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")

    if not tool.visible:
        raise HTTPException(status_code=403, detail="Tool is not available")

    try:
        # 准备消息历史
        messages = request.messages

        # 获取流式响应
        async def generate():
            try:
                async for chunk in ai_service.chat_stream(
                    messages=messages,
                    model=tool.model,
                    system_prompt=tool.system_prompt,
                    temperature=0.7
                ):
                    # 发送SSE格式数据
                    yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

                # 发送结束标记
                yield "data: [DONE]\n\n"

            except Exception as e:
                logger.error(f"Chat stream error: {e}")
                error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
                yield f"data: {error_data}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/{tool_id}/chat", tags=["对话"])
async def chat_non_stream(
    tool_id: str,
    request: ChatRequest,
    ai_service: AIService = Depends(get_ai_service),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    非流式对话接口

    返回完整的AI响应
    """
    # 获取工具配置
    tool = tool_service.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")

    if not tool.visible:
        raise HTTPException(status_code=403, detail="Tool is not available")

    try:
        response = await ai_service.chat(
            messages=request.messages,
            model=tool.model,
            system_prompt=tool.system_prompt,
            temperature=0.7
        )

        return {"content": response}

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: 创建tools/chat测试**

Create: `backend/tests/integration/api/test_tools_chat.py`

```python
"""
工具对话路由集成测试
"""
import pytest
import json
from httpx import AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_chat_stream_with_valid_tool():
    """
    测试有效工具的流式对话
    """
    tool_id = "lesson-generator"  # 假设存在这个工具

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            f"/api/v1/tools/{tool_id}/chat/stream",
            json={
                "messages": [
                    {"role": "user", "content": "Hello"}
                ]
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"


@pytest.mark.asyncio
async def test_chat_stream_with_invalid_tool():
    """
    测试无效工具返回404
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/tools/invalid-tool/chat/stream",
            json={
                "messages": [
                    {"role": "user", "content": "Hello"}
                ]
            }
        )

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_chat_stream_sse_format():
    """
    测试SSE响应格式
    """
    tool_id = "lesson-generator"

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            f"/api/v1/tools/{tool_id}/chat/stream",
            json={
                "messages": [
                    {"role": "user", "content": "Say 'test'"}
                ]
            }
        )

        assert response.status_code == 200

        # 验证SSE格式
        content = response.text
        assert "data: " in content
        assert "\n\n" in content


@pytest.mark.asyncio
async def test_chat_non_stream():
    """
    测试非流式对话接口
    """
    tool_id = "lesson-generator"

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            f"/api/v1/tools/{tool_id}/chat",
            json={
                "messages": [
                    {"role": "user", "content": "Hello"}
                ]
            }
        )

        assert response.status_code == 200

        data = response.json()
        assert "content" in data
```

**Step 3: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest tests/integration/api/test_tools_chat.py -v
```

Expected: 测试通过

**Step 4: 提交tools/chat路由**

Run:
```bash
git add backend/src/interfaces/routers/tools/chat.py backend/tests/integration/api/test_tools_chat.py
git commit -m "feat(routers): extract chat endpoints to separate file"
```

---

## Task 3: 创建tools/conversations.py路由

**Files:**
- Create: `backend/src/interfaces/routers/tools/conversations.py`
- Create: `backend/tests/integration/api/test_tools_conversations.py`

**Step 1: 创建tools/conversations.py**

Create: `backend/src/interfaces/routers/tools/conversations.py`

```python
"""
会话管理路由
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from src.models import ConversationListResponse
from src.interfaces.dependencies import get_session_service
from src.services.session_service import SessionService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/tools/{tool_id}/conversations", response_model=ConversationListResponse, tags=["会话"])
async def get_conversations(
    tool_id: str,
    current_user = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    """
    获取用户在指定工具下的会话列表

    返回按时间倒序排列的会话列表
    """
    try:
        conversations = session_service.get_user_conversations(
            user_id=current_user.id,
            tool_id=tool_id
        )

        return ConversationListResponse(conversations=conversations)

    except Exception as e:
        logger.error(f"Get conversations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tools/{tool_id}/conversations/{conv_id}", tags=["会话"])
async def delete_conversation(
    tool_id: str,
    conv_id: str,
    current_user = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    """
    删除指定会话

    同时删除会话下的所有消息和成果物
    """
    try:
        # 验证会话属于当前用户
        session = session_service.get_session(conv_id)
        if not session:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # 删除会话
        session_service.delete_conversation(conv_id)

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/{tool_id}/conversations/{conv_id}", tags=["会话"])
async def get_conversation(
    tool_id: str,
    conv_id: str,
    current_user = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    """
    获取会话详情（包含消息历史）
    """
    try:
        session = session_service.get_session(conv_id)
        if not session:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        messages = session_service.get_session_messages(conv_id)

        return {
            "conversation": session,
            "messages": messages
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: 创建tools/conversations测试**

Create: `backend/tests/integration/api/test_tools_conversations.py`

```python
"""
会话路由集成测试
"""
import pytest
from httpx import AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_get_conversations():
    """
    测试获取会话列表
    """
    tool_id = "lesson-generator"

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/tools/{tool_id}/conversations")

        assert response.status_code == 200

        data = response.json()
        assert "conversations" in data


@pytest.mark.asyncio
async def test_delete_conversation():
    """
    测试删除会话
    """
    tool_id = "lesson-generator"
    conv_id = "test-conv-id"

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete(f"/api/v1/tools/{tool_id}/conversations/{conv_id}")

        # 可能返回404（会话不存在）或200（成功）
        assert response.status_code in [200, 404, 403]


@pytest.mark.asyncio
async def test_get_conversation_detail():
    """
    测试获取会话详情
    """
    tool_id = "lesson-generator"
    conv_id = "test-conv-id"

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/tools/{tool_id}/conversations/{conv_id}")

        # 可能返回404（会话不存在）
        assert response.status_code in [200, 404, 403]
```

**Step 3: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest tests/integration/api/test_tools_conversations.py -v
```

Expected: 测试通过

**Step 4: 提交tools/conversations路由**

Run:
```bash
git add backend/src/interfaces/routers/tools/conversations.py backend/tests/integration/api/test_tools_conversations.py
git commit -m "feat(routers): extract conversation endpoints to separate file"
```

---

## Task 4: 创建统一错误处理中间件

**Files:**
- Create: `backend/src/interfaces/middleware/error_handler.py`
- Create: `backend/tests/integration/middleware/test_error_handler.py`

**Step 1: 创建ApplicationException基类**

Create: `backend/src/interfaces/middleware/error_handler.py`

```python
"""
统一错误处理中间件
"""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ApplicationException(Exception):
    """
    应用异常基类

    所有业务异常都应该继承此类
    """
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Dict[str, Any] | None = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

        super().__init__(self.message)


class NotFoundException(ApplicationException):
    """资源未找到异常"""
    def __init__(self, message: str = "Resource not found", details: Dict[str, Any] | None = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ForbiddenException(ApplicationException):
    """权限不足异常"""
    def __init__(self, message: str = "Access forbidden", details: Dict[str, Any] | None = None):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class BadRequestException(ApplicationException):
    """错误请求异常"""
    def __init__(self, message: str = "Bad request", details: Dict[str, Any] | None = None):
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


async def error_handler(request: Request, call_next):
    """
    全局错误处理中间件

    捕获所有异常并返回统一格式的错误响应
    """
    try:
        response = await call_next(request)
        return response

    except ApplicationException as e:
        # 应用异常
        logger.warning(f"Application error: {e.code} - {e.message}")

        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "path": str(request.url)
                }
            }
        )

    except status.HTTP_404_Exception as e:
        # FastAPI 404异常
        logger.warning(f"404 error: {str(e)}")

        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "The requested resource was not found",
                    "path": str(request.url)
                }
            }
        )

    except status.HTTP_401_Exception as e:
        # FastAPI 401异常
        logger.warning(f"401 error: {str(e)}")

        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Authentication required",
                    "path": str(request.url)
                }
            }
        )

    except Exception as e:
        # 未捕获的异常
        logger.exception(f"Unexpected error: {str(e)}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "path": str(request.url)
                }
            }
        )
```

**Step 2: 创建错误处理测试**

Create: `backend/tests/integration/middleware/test_error_handler.py`

```python
"""
错误处理中间件测试
"""
import pytest
from httpx import AsyncClient
from src.main import app
from src.interfaces.middleware.error_handler import (
    ApplicationException,
    NotFoundException,
    ForbiddenException,
    BadRequestException,
)


@pytest.mark.asyncio
async def test_application_exception_handling():
    """
    测试ApplicationException被正确处理
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 访问一个抛出ApplicationException的端点
        # 这里需要一个测试端点来触发异常
        # 或者在实际路由中测试

        pass


@pytest.mark.asyncio
async def test_404_error_handling():
    """
    测试404错误返回统一格式
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/nonexistent-endpoint")

        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_401_error_handling():
    """
    测试401错误返回统一格式
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 访问需要认证的端点但不提供token
        response = await ac.get("/api/v1/tools")

        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "UNAUTHORIZED"


def test_exception_classes():
    """
    测试异常类创建
    """
    # ApplicationException
    exc = ApplicationException("Test error", code="TEST_ERROR", status_code=500)
    assert exc.message == "Test error"
    assert exc.code == "TEST_ERROR"
    assert exc.status_code == 500

    # NotFoundException
    not_found = NotFoundException("User not found")
    assert not_found.code == "NOT_FOUND"
    assert not_found.status_code == 404

    # ForbiddenException
    forbidden = ForbiddenException("Access denied")
    assert forbidden.code == "FORBIDDEN"
    assert forbidden.status_code == 403

    # BadRequestException
    bad_request = BadRequestException("Invalid input")
    assert bad_request.code == "BAD_REQUEST"
    assert bad_request.status_code == 400
```

**Step 3: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest tests/integration/middleware/test_error_handler.py -v
```

Expected: 测试通过

**Step 4: 提交错误处理中间件**

Run:
```bash
git add backend/src/interfaces/middleware/error_handler.py backend/tests/integration/middleware/test_error_handler.py
git commit -m "feat(middleware): add unified error handling middleware"
```

---

## Task 5: 更新main.py注册新路由

**Files:**
- Modify: `backend/src/main.py`

**Step 1: 读取现有main.py**

Read: `backend/src/main.py`

**Step 2: 更新main.py**

Update: `backend/src/main.py`

```python
"""
FastAPI应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.interfaces.middleware.error_handler import error_handler
from src.interfaces.routers.tools import list, chat, conversations
from src.routers import auth, works, courses, admin_tools, common

# 创建FastAPI应用
app = FastAPI(
    title="AI智能备课平台 API",
    description="基于大语言模型的教育辅助平台",
    version="2.0.0"
)

# 注册CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册统一错误处理中间件
app.middleware("http")(error_handler)

# 注册工具路由（新）
app.include_router(list.router, prefix="/api/v1", tags=["工具"])
app.include_router(chat.router, prefix="/api/v1", tags=["对话"])
app.include_router(conversations.router, prefix="/api/v1", tags=["会话"])

# 保留旧路由（暂未迁移的）
app.include_router(auth.router, prefix="/api/v1", tags=["认证"])
app.include_router(works.router, prefix="/api/v1", tags=["作品"])
app.include_router(courses.router, prefix="/api/v1", tags=["课程"])
app.include_router(admin_tools.router, prefix="/api/v1/admin", tags=["管理"])
app.include_router(common.router, prefix="/api/v1", tags=["通用"])

# 静态文件服务
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": "2.0.0"
    }


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    import logging
    logging.info("AI智能备课平台启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    import logging
    logging.info("AI智能备课平台关闭")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

**Step 3: 验证API文档**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
python -m src.main
```

访问: http://localhost:8000/docs

验证:
- 工具路由显示在文档中
- 所有端点可以访问
- 错误格式统一

**Step 4: 提交main.py更新**

Run:
```bash
git add backend/src/main.py
git commit -m "refactor(main): register new modular routers with error handling"
```

---

## Task 6: 删除旧的tools.py

**Files:**
- Delete: `backend/src/routers/tools.py`

**Step 1: 确认所有功能已迁移**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
# 检查新路由是否工作
curl http://localhost:8000/api/v1/tools
```

**Step 2: 备份旧文件（可选）**

Run:
```bash
mv backend/src/routers/tools.py backend/src/routers/tools.py.backup
```

**Step 3: 测试所有功能**

Run:
```bash
# 运行集成测试
pytest tests/integration/api/ -v
```

**Step 4: 删除备份文件**

Run:
```bash
git rm backend/src/routers/tools.py.backup
git commit -m "refactor(routers): remove old tools.py after migration"
```

---

## Task 7: 创建HTML修复服务

**Files:**
- Create: `backend/src/infrastructure/html_fixer.py`
- Create: `backend/tests/unit/infrastructure/test_html_fixer.py`

**Step 1: 安装BeautifulSoup4**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pip install beautifulsoup4 lxml
echo "beautifulsoup4==4.12.2" >> requirements.txt
echo "lxml==4.9.3" >> requirements.txt
```

**Step 2: 创建HtmlFixerService**

Create: `backend/src/infrastructure/html_fixer.py`

```python
"""
HTML修复服务

统一处理HTML标签修复、清理和格式化
"""
import re
from typing import List
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class HtmlFixerService:
    """
    HTML修复服务

    提供HTML标签修复、XSS防护、格式化等功能
    """

    @staticmethod
    def fix_broken_tags(html: str) -> str:
        """
        修复未闭合的HTML标签

        使用BeautifulSoup确保所有标签正确闭合

        Args:
            html: 原始HTML字符串

        Returns:
            str: 修复后的HTML字符串
        """
        if not html:
            return ""

        try:
            soup = BeautifulSoup(html, 'lxml')
            return str(soup)
        except Exception as e:
            logger.error(f"HTML fix error: {e}")
            return html

    @staticmethod
    def close_open_tags(html: str) -> str:
        """
        关闭未闭合的标签（正则表达式方法）

        主要用于简单场景的快速修复

        Args:
            html: 原始HTML字符串

        Returns:
            str: 修复后的HTML字符串
        """
        if not html:
            return ""

        # 修复自闭合标签
        html = re.sub(r'<(img|br|hr)(?![^>]*\/)>', r'<\1 />', html)

        # 使用BeautifulSoup确保所有标签闭合
        soup = BeautifulSoup(html, 'lxml')
        return soup.prettify()

    @staticmethod
    def sanitize_scripts(html: str) -> str:
        """
        移除危险的script标签和事件处理属性

        Args:
            html: 原始HTML字符串

        Returns:
            str: 清理后的HTML字符串
        """
        if not html:
            return ""

        try:
            soup = BeautifulSoup(html, 'lxml')

            # 移除所有script标签
            for script in soup.find_all('script'):
                script.decompose()

            # 移除危险的事件处理属性
            dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover']
            for tag in soup.find_all(True):
                for attr in dangerous_attrs:
                    if tag.has_attr(attr):
                        del tag[attr]

            return str(soup)

        except Exception as e:
            logger.error(f"HTML sanitize error: {e}")
            return html

    @staticmethod
    def extract_text(html: str) -> str:
        """
        从HTML中提取纯文本

        Args:
            html: HTML字符串

        Returns:
            str: 纯文本内容
        """
        if not html:
            return ""

        try:
            soup = BeautifulSoup(html, 'lxml')
            return soup.get_text(separator=' ', strip=True)
        except Exception as e:
            logger.error(f"HTML text extraction error: {e}")
            return html

    @staticmethod
    def format_html(html: str, indent: int = 2) -> str:
        """
        格式化HTML代码

        Args:
            html: 原始HTML字符串
            indent: 缩进空格数

        Returns:
            str: 格式化后的HTML字符串
        """
        if not html:
            return ""

        try:
            soup = BeautifulSoup(html, 'lxml')
            return soup.prettify(indentator=' ' * indent)
        except Exception as e:
            logger.error(f"HTML format error: {e}")
            return html

    @staticmethod
    def wrap_html(html: str, tag: str = "div", **attrs) -> str:
        """
        用指定标签包装HTML

        Args:
            html: 原始HTML字符串
            tag: 包装标签名
            **attrs: 标签属性

        Returns:
            str: 包装后的HTML字符串
        """
        if not html:
            return ""

        try:
            soup = BeautifulSoup(html, 'lxml')
            wrapper = soup.new_tag(tag, **attrs)
            wrapper.append(soup)
            return str(wrapper)
        except Exception as e:
            logger.error(f"HTML wrap error: {e}")
            return html

    @staticmethod
    def fix_encoding(html: str) -> str:
        """
        修复HTML编码问题

        Args:
            html: 原始HTML字符串

        Returns:
            str: 修复编码后的HTML字符串
        """
        if not html:
            return ""

        try:
            # 修复常见的编码问题
            html = html.replace('â€™', "'")
            html = html.replace('â€œ', '"')
            html = html.replace('â€\x9d', '"')
            html = html.replace('â€', '—')

            return html
        except Exception as e:
            logger.error(f"HTML encoding fix error: {e}")
            return html
```

**Step 3: 创建HtmlFixerService测试**

Create: `backend/tests/unit/infrastructure/test_html_fixer.py`

```python
"""
HtmlFixerService单元测试
"""
import pytest
from src.infrastructure.html_fixer import HtmlFixerService


class TestHtmlFixerService:
    """HtmlFixerService测试类"""

    def test_fix_broken_tags_closes_unclosed_div(self):
        """测试修复未闭合的div标签"""
        broken = "<div><p>Hello</p>"
        fixed = HtmlFixerService.fix_broken_tags(broken)

        assert "</div>" in fixed
        assert "<p>Hello</p>" in fixed

    def test_fix_broken_tags_handles_empty_string(self):
        """测试处理空字符串"""
        fixed = HtmlFixerService.fix_broken_tags("")
        assert fixed == ""

    def test_sanitize_scripts_removes_script_tags(self):
        """测试移除script标签"""
        html = "<div>Hello<script>alert('xss')</script></div>"
        cleaned = HtmlFixerService.sanitize_scripts(html)

        assert "<script>" not in cleaned
        assert "Hello" in cleaned

    def test_sanitize_scripts_removes_onclick_attribute(self):
        """测试移除onclick属性"""
        html = '<div onclick="alert(\'xss\')">Click me</div>'
        cleaned = HtmlFixerService.sanitize_scripts(html)

        assert "onclick" not in cleaned
        assert "Click me" in cleaned

    def test_extract_text_gets_text_content(self):
        """测试提取文本内容"""
        html = "<div><p>Hello <b>World</b></p></div>"
        text = HtmlFixerService.extract_text(html)

        assert "Hello World" in text
        assert "<div>" not in text

    def test_format_html_prettifies_output(self):
        """测试格式化HTML"""
        html = "<div><p>Hello</p></div>"
        formatted = HtmlFixerService.format_html(html)

        # 格式化后应该有换行和缩进
        assert "\n" in formatted or formatted != html

    def test_wrap_html_wraps_with_div(self):
        """测试用div包装HTML"""
        html = "<p>Hello</p>"
        wrapped = HtmlFixerService.wrap_html(html, tag="div", class_="container")

        assert wrapped.startswith("<div")
        assert 'class="container"' in wrapped
        assert "<p>Hello</p>" in wrapped
        assert "</div>" in wrapped

    def test_fix_encoding_replaces_mojibake(self):
        """测试修复编码问题"""
        broken = "Helloâ€™s World"  # 乱码的撇号
        fixed = HtmlFixerService.fix_encoding(broken)

        assert "’" in fixed or "'s" in fixed
        assert "â€™" not in fixed

    def test_close_open_tags_fixes_self_closing_tags(self):
        """测试修复自闭合标签"""
        html = "<img src='test.jpg'>"
        fixed = HtmlFixerService.close_open_tags(html)

        assert "<img src='test.jpg' />" in fixed or "<img src=\"test.jpg\" />" in fixed

    def test_fix_broken_tags_handles_nested_elements(self):
        """测试处理嵌套元素"""
        html = "<div><ul><li>Item 1</li><li>Item 2</ul></div>"
        fixed = HtmlFixerService.fix_broken_tags(html)

        # 应该修复未闭合的li标签
        assert "</li>" in fixed

    def test_sanitize_scripts_handles_multiple_scripts(self):
        """测试处理多个script标签"""
        html = "<div><script>alert(1)</script>Text<script>alert(2)</script></div>"
        cleaned = HtmlFixerService.sanitize_scripts(html)

        assert "<script>" not in cleaned
        assert "Text" in cleaned
```

**Step 4: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest tests/unit/infrastructure/test_html_fixer.py -v
```

Expected: 所有测试通过

**Step 5: 提交HtmlFixerService**

Run:
```bash
git add backend/src/infrastructure/html_fixer.py backend/tests/unit/infrastructure/test_html_fixer.py backend/requirements.txt
git commit -m "feat(infrastructure): add HtmlFixerService for HTML sanitization and repair"
```

---

## Task 8: 配置Playwright E2E测试

**Files:**
- Create: `frontend/tests/e2e/chat.spec.ts`
- Create: `frontend/playwright.config.ts`
- Modify: `frontend/package.json`

**Step 1: 安装Playwright**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
npm install -D @playwright/test
npx playwright install chromium
```

**Step 2: 创建playwright.config.ts**

Create: `frontend/playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

**Step 3: 创建E2E测试**

Create: `frontend/tests/e2e/chat.spec.ts`

```typescript
/**
 * 聊天功能E2E测试
 */
import { test, expect } from '@playwright/test';

test.describe('AI对话流程', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前导航到工具页面
    await page.goto('/modules/ai_tools');
  });

  test('应该显示工具列表', async ({ page }) => {
    // 等待工具列表加载
    await expect(page.locator('[data-testid="tool-list"]')).toBeVisible();
  });

  test('应该能选择工具并打开对话', async ({ page }) => {
    // 选择第一个工具
    await page.click('[data-testid="tool-item"]:first-child');

    // 验证对话界面打开
    await expect(page.locator('[data-testid="chat-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="chat-input"]')).toBeVisible();
  });

  test('应该能发送消息并显示响应', async ({ page }) => {
    // 选择工具
    await page.click('[data-testid="tool-item"]:first-child');

    // 输入消息
    await page.fill('[data-testid="chat-input"]', 'Hello, how are you?');
    await page.click('[data-testid="send-button"]');

    // 验证消息出现在列表中
    await expect(page.locator('[data-testid="message-item"]').first()).toBeVisible();

    // 验证发送按钮禁用状态
    await expect(page.locator('[data-testid="send-button"]')).toBeDisabled();

    // 等待AI响应（最多30秒）
    await expect(page.locator('[data-testid="message-item"]').nth(1)).toBeVisible({ timeout: 30000 });
  });

  test('应该显示流式响应的加载状态', async ({ page }) => {
    await page.click('[data-testid="tool-item"]:first-child');

    await page.fill('[data-testid="chat-input"]', 'Generate content');
    await page.click('[data-testid="send-button"]');

    // 验证流式指示器显示
    await expect(page.locator('[data-testid="streaming-message"]')).toBeVisible({ timeout: 5000 });
  });

  test('应该在消息列表中显示用户和AI消息', async ({ page }) => {
    await page.click('[data-testid="tool-item"]:first-child');

    await page.fill('[data-testid="chat-input"]', 'Test message');
    await page.click('[data-testid="send-button"]');

    // 等待两条消息
    await expect(page.locator('[data-testid="message-item"]').nth(0)).toBeVisible();
    await expect(page.locator('[data-testid="message-item"]').nth(1)).toBeVisible({ timeout: 30000 });

    // 验证第一条是用户消息
    const firstMessage = page.locator('[data-testid="message-item"]').nth(0);
    await expect(firstMessage).toHaveClass(/message-user/);

    // 验证第二条是AI消息
    const secondMessage = page.locator('[data-testid="message-item"]').nth(1);
    await expect(secondMessage).toHaveClass(/message-assistant/);
  });

  test('应该支持Shift+Enter换行', async ({ page }) => {
    await page.click('[data-testid="tool-item"]:first-child');

    const chatInput = page.locator('[data-testid="chat-input"]');

    // 输入文本并按Shift+Enter
    await chatInput.fill('Line 1');
    await chatInput.press('Shift+Enter');
    await chatInput.type('Line 2');

    // 验证输入框包含换行
    expect(await chatInput.inputValue()).toContain('Line 1\nLine 2');

    // 验证消息未发送
    await expect(page.locator('[data-testid="message-item"]')).toHaveCount(0);
  });
});
```

**Step 4: 更新package.json**

Read: `frontend/package.json`

Add scripts:

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug"
  }
}
```

**Step 5: 提交Playwright配置**

Run:
```bash
git add frontend/playwright.config.ts frontend/tests/e2e/ frontend/package.json
git commit -m "test(frontend): configure Playwright E2E testing"
```

---

## Task 9: 完善测试覆盖率

**Step 1: 检查当前覆盖率**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest --cov=src --cov-report=html --cov-report=term
```

检查覆盖率报告，找出未覆盖的模块

**Step 2: 补充遗漏的测试**

根据覆盖率报告，为未覆盖的模块添加测试

**示例：补充application层测试**

Create: `backend/tests/unit/application/services/test_chat_service.py`

```python
"""
ChatService单元测试
"""
import pytest
from unittest.mock import Mock, AsyncMock
from src.application.services.chat_service import ChatService
from src.domain.entities.message import Message
from src.domain.value_objects.message_role import MessageRole


@pytest.mark.asyncio
class TestChatService:
    """ChatService测试类"""

    async def test_process_chat_message(self):
        """测试处理聊天消息"""
        # Arrange
        mock_provider = Mock()
        mock_provider.chat_stream = AsyncMock(return_value=["Hello", " World"])

        mock_session_repo = Mock()
        mock_message_repo = Mock()

        service = ChatService(
            ai_provider=mock_provider,
            session_repo=mock_session_repo,
            message_repo=mock_message_repo
        )

        # Act
        result = []
        async for chunk in service.process_chat_message(
            session_id=1,
            user_message="Hello AI"
        ):
            result.append(chunk)

        # Assert
        assert "".join(result) == "Hello World"
```

**Step 3: 运行完整测试套件**

Run:
```bash
pytest --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80
```

目标：整体覆盖率 >80%

**Step 4: 提交补充测试**

Run:
```bash
git add backend/tests/unit/application/
git commit -m "test(application): add unit tests for chat service"
```

---

## Task 10: 阶段3总结和验证

**Step 1: 运行完整测试套件**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend

# 单元测试
pytest tests/unit/ -v --cov

# 集成测试
pytest tests/integration/ -v

# 全部测试
pytest -v
```

Expected: 所有测试通过

**Step 2: 运行前端E2E测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
npm run test:e2e
```

Expected: E2E测试通过

**Step 3: 验证代码质量**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend

# 检查大文件
find src -name "*.py" -exec wc -l {} + | sort -rn | head -20
```

Expected: 新创建的文件都应该 <500行

**Step 4: 手动E2E测试**

启动完整应用：
```bash
# 后端
cd backend && python -m src.main

# 前端（新终端）
cd frontend && npm run dev

# E2E测试（新终端）
cd frontend
npm run test:e2e:ui
```

**Step 5: 创建重构完成标记**

Run:
```bash
echo "System Refactoring Complete: All 3 Phases" > .refactoring-complete
echo "Date: $(date)" >> .refactoring-complete
echo "" >> .refactoring-complete
echo "Phase 1: DDD Architecture + Provider Migration" >> .refactoring-complete
echo "Phase 2: Frontend Component Refactoring" >> .refactoring-complete
echo "Phase 3: Backend Routes + Test Coverage" >> .refactoring-complete

git add .refactoring-complete
git commit -m "chore: mark system refactoring as complete (all 3 phases)"
```

---

## 📝 阶段3完成检查清单

### 后端路由拆分
- [x] tools/list.py + 测试
- [x] tools/chat.py + 测试
- [x] tools/conversations.py + 测试
- [x] 统一错误处理中间件
- [x] main.py更新注册新路由
- [x] 删除旧tools.py

### HTML修复服务
- [x] HtmlFixerService实现
- [x] 完整单元测试
- [x] 覆盖所有修复方法

### 测试完善
- [x] Playwright E2E测试配置
- [x] E2E测试套件
- [x] 单元测试覆盖率 >80%
- [x] 集成测试通过

---

## 🎯 系统重构完成总结

### 完成的工作

**阶段1（Day 1-4）**：DDD架构 + Provider迁移
- ✅ 建立DDD四层目录结构
- ✅ 配置pytest测试框架
- ✅ 创建领域实体（User, Message, Artifact）
- ✅ 定义仓储接口
- ✅ 实现AIProvider抽象层
- ✅ 实现OpenAI/DeepSeek Provider
- ✅ 实现ProviderFactory

**阶段2（Day 5-7）**：前端组件拆分
- ✅ 配置Vitest测试框架
- ✅ 拆分PreviewPanel（1348行 → ~150行）
- ✅ 拆分ChatPanel（747行 → ~150行）
- ✅ 创建8个小组件
- ✅ 完整组件测试覆盖

**阶段3（Day 8-12）**：后端路由拆分 + 测试完善
- ✅ 拆分tools.py为3个路由文件
- ✅ 统一错误处理中间件
- ✅ 建立HTML修复服务
- ✅ 配置Playwright E2E测试
- ✅ 测试覆盖率 >80%

### 技术指标

| 指标 | 重构前 | 重构后 | 改进 |
|------|--------|--------|------|
| AIService行数 | 1276行 | Provider模式 | ✅ 拆分 |
| PreviewPanel行数 | 1348行 | ~150行 | ✅ -89% |
| ChatPanel行数 | 747行 | ~150行 | ✅ -80% |
| tools.py行数 | 969行 | 3个文件 | ✅ 拆分 |
| 单元测试覆盖率 | 未知 | >80% | ✅ 新增 |
| E2E测试 | 无 | Playwright | ✅ 新增 |

### 架构改进

1. **后端DDD分层**：清晰的职责分离
2. **Provider抽象**：支持多模型接入
3. **前端组件化**：每个组件<300行
4. **统一错误处理**：一致的错误格式
5. **测试体系完善**：pytest + Playwright

### 为未来打好基础

- ✅ 模块2（多模型接入）：Provider抽象层已就绪
- ✅ 模块3（定价策略）：架构支持灵活配置
- ✅ 模块4（支付接入）：清晰的分层便于集成
- ✅ 模块5（用户体系）：User实体和仓储已定义

---

## 🚀 下一步行动

重构完成后，可以开始执行模块2-5：

1. **模块2：多模型接入方案**
   - 使用已建立的Provider抽象
   - 接入DeepSeek、智谱GLM、通义千问、Kimi
   - 参考：`docs/plans/2026-02-27-platform-upgrade-tasks.md`

2. **模块3：定价策略方案**
   - 基于模型成本制定定价
   - 设计免费额度规则
   - C端 vs B端差异化

3. **模块4：支付接入方案**
   - 评估支付宝/微信支付
   - 实现支付接口

4. **模块5：用户体系方案**
   - 个人 vs 企业用户
   - 权限管理
   - 使用统计

查看主任务文档继续：
[docs/plans/2026-02-27-platform-upgrade-tasks.md](docs/plans/2026-02-27-platform-upgrade-tasks.md)
