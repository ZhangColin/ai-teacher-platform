# -*- coding: utf-8 -*-
"""AI 工具路由

包含工具列表、工具对话、历史会话、多模态生成等接口。
"""
import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse

from src.models import (
    UserInfo,
    ToolListResponse,
    ToolListItem,
    CategoryGroup,
    ConversationListResponse,
    ConversationListItem,
    ChatRequest,
    ChatResponse,
    Message,
    MultiModalContent,
    MediaGenerateRequest,
    MediaGenerateResponse,
)

from .auth import get_current_user
from .dependencies import (
    get_tool_service,
    get_session_service,
    get_ai_service,
    get_artifact_parser,
    get_title_generator,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["工具"])


def make_absolute_url(relative_url: str, request: Request) -> str:
    """
    将相对URL转换为绝对URL

    Args:
        relative_url: 相对URL（如 /static/media/audio/xxx.mp3）
        request: FastAPI Request对象

    Returns:
        绝对URL（如 http://localhost:8000/static/media/audio/xxx.mp3）
    """
    # 如果已经是绝对URL，直接返回
    if relative_url.startswith(('http://', 'https://')):
        return relative_url

    # 构建绝对URL
    base_url = str(request.base_url).rstrip('/')
    return f"{base_url}{relative_url}"


# 用于存储任务状态的字典（简单实现，生产环境建议使用Redis）
task_storage: dict[str, dict] = {}


@router.get("/tools", response_model=ToolListResponse)
async def get_tools(current_user: Annotated[UserInfo, Depends(get_current_user)] = None):
    """获取所有已配置的工具列表，按分类组织"""
    tool_service = get_tool_service()
    # 加载所有工具（只返回 visible=true 的工具）
    tools = tool_service.load_all_tools()

    # 按 category 聚合
    category_groups = tool_service.group_by_category(tools)

    # 转换为 API 响应格式
    categories = []
    for group in category_groups:
        tool_items = [
            ToolListItem(
                tool_id=tool.tool_id,
                name=tool.name,
                description=tool.description,
                icon=tool.icon,
                category=tool.category,
                visible=tool.visible,
                type=tool.type,
                welcome_message=tool.welcome_message,
                toolset_id=tool.toolset_id,
                content_type=tool.content_type,
                media_type=tool.media_type
            )
            for tool in group['tools']
        ]

        categories.append(
            CategoryGroup(
                name=group['name'],
                icon=group['icon'],
                tools=tool_items
            )
        )

    return ToolListResponse(categories=categories)


@router.get("/toolsets/{toolset_id}/tools", response_model=ToolListResponse)
async def get_toolset_tools(
    toolset_id: str,
    current_user: Annotated[UserInfo, Depends(get_current_user)] = None,
):
    """获取指定工具集的工具列表，按分类组织"""
    tool_service = get_tool_service()
    # 加载指定工具集的工具（只返回 visible=true 的工具）
    tools = tool_service.load_tools_by_toolset(toolset_id)

    # 按 category 聚合
    category_groups = tool_service.group_by_category(tools, toolset_id=toolset_id)

    # 转换为 API 响应格式
    categories = []
    for group in category_groups:
        tool_items = [
            ToolListItem(
                tool_id=tool.tool_id,
                name=tool.name,
                description=tool.description,
                icon=tool.icon,
                category=tool.category,
                visible=tool.visible,
                type=tool.type,
                welcome_message=tool.welcome_message,
                toolset_id=tool.toolset_id,
                content_type=tool.content_type,
                media_type=tool.media_type
            )
            for tool in group['tools']
        ]

        categories.append(
            CategoryGroup(
                name=group['name'],
                icon=group['icon'],
                tools=tool_items
            )
        )

    return ToolListResponse(categories=categories)


# 已删除废弃端点: GET /common-tools
# 前端现在使用 /common-tools/categories 和 /common-tools/tools/{tool_id} (routers/common.py)
# 删除日期: 2026-03-01

@router.get("/tools/{tool_id}/chat")
async def get_tool_chat_info(
    tool_id: str,
    current_user: Annotated[UserInfo, Depends(get_current_user)] = None,
):
    """获取工具对话信息（用于 OPTIONS 请求等）"""
    tool_service = get_tool_service()
    tool = tool_service.get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    return {"message": "OK"}


@router.post("/tools/{tool_id}/chat", response_model=ChatResponse)
async def chat(
    tool_id: str,
    request: ChatRequest,
    current_user: Annotated[UserInfo, Depends(get_current_user)] = None,
):
    """向指定工具发送消息，获取 AI 回复。如果 session_id 不存在，自动创建新会话。"""
    logger.info(f"🚀 chat() 函数被调用 - tool_id: {tool_id}, user: {current_user.username}, session_id: {request.session_id}")

    tool_service = get_tool_service()
    session_service = get_session_service()
    ai_service = get_ai_service()
    artifact_parser = get_artifact_parser()
    title_generator = get_title_generator()

    # 验证工具是否存在
    tool = tool_service.get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    # 处理会话：如果 session_id 不存在，创建新会话
    session_id = request.session_id
    session = None

    if session_id:
        # 验证会话是否存在且属于当前用户
        session = session_service.get_session_by_id(session_id, user_id=current_user.user_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found"
            )
    else:
        # 创建新会话（基于第一条消息自动生成标题）
        session = session_service.create_session(
            user_id=current_user.user_id,
            tool_id=tool_id,
            first_message=request.message
        )
        session_id = session.session_id

    # 获取历史消息
    history_list = []
    if request.history:
        # 使用请求中提供的历史消息
        for msg in request.history:
            if msg.role not in ["user", "assistant"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的消息角色: {msg.role}，必须是 'user' 或 'assistant'"
                )
            history_list.append({
                "role": msg.role,
                "content": msg.content
            })
    else:
        # 从数据库读取历史消息
        messages = session_service.get_messages_by_session(session_id, user_id=current_user.user_id)
        for msg in messages:
            history_list.append({
                "role": msg.role,
                "content": msg.content
            })

    # 添加当前用户消息到历史
    history_list.append({
        "role": "user",
        "content": request.message
    })

    # 调用 AI 服务进行对话（传入工具的模型配置）
    reply = await ai_service.chat(
        system_prompt=tool.system_prompt,
        history=history_list[:-1],  # 不包含当前消息
        user_message=request.message,
        model_config=tool.model  # 传入工具指定的模型配置
    )

    # 记录最终返回的完整内容（用于排查HTML问题）
    logger.info("=" * 80)
    logger.info("最终返回给前端的完整内容:")
    logger.info(f"内容总长度: {len(reply)} 字符")
    if '<html' in reply.lower() or '<!doctype' in reply.lower():
        logger.info("包含HTML内容")
        logger.info(f"完整HTML内容（前2000字符）:\n{reply[:2000]}")
        logger.info(f"完整HTML内容（后2000字符）:\n{reply[-2000:]}")
        # 检查HTML结构完整性
        html_tags = ['<!doctype', '<html', '</html>', '<head', '</head>', '<body', '</body>']
        for tag in html_tags:
            count = reply.lower().count(tag)
            if count > 0:
                logger.info(f"  {tag}: {count} 个")
    logger.info("=" * 80)

    # 保存用户消息到数据库（显式控制时间戳，确保消息顺序）
    user_message_time = datetime.now()
    logger.info(f"保存用户消息 - 时间戳: {user_message_time}, 会话ID: {session_id}")
    session_service.add_message(
        session_id=session_id,
        role="user",
        content=request.message,
        user_id=current_user.user_id,
        created_at=user_message_time
    )

    # 保存 AI 回复到数据库（确保晚于用户消息 1 秒，避免精度问题）
    ai_message_time = user_message_time + timedelta(seconds=1)
    logger.info(f"保存 AI 消息 - 时间戳: {ai_message_time}, 会话ID: {session_id}")
    session_service.add_message(
        session_id=session_id,
        role="assistant",
        content=reply,
        user_id=current_user.user_id,
        created_at=ai_message_time
    )

    # 检查是否是第一轮对话，如果是则生成标题
    messages = session_service.get_messages_by_session(session_id, user_id=current_user.user_id)
    logger.info(f"会话消息数量检查 - 会话ID: {session_id}, 消息数: {len(messages)}")

    if len(messages) == 2:  # 第一轮对话：1条用户消息 + 1条AI回复
        try:
            logger.info(f"检测到第一轮对话，开始生成会话标题 - 用户消息: {request.message[:50]}")
            # 生成标题
            title = await title_generator.generate_title(request.message, reply)
            # 更新会话标题
            session_service.update_session_title(session_id, title, user_id=current_user.user_id)
            logger.info(f"会话标题已生成并更新：{title}")
        except Exception as e:
            logger.error(f"生成会话标题失败，使用降级方案: {e}", exc_info=True)
            # 降级方案：使用简单截取
            try:
                fallback_title = title_generator._fallback_title(request.message)
                session_service.update_session_title(session_id, fallback_title, user_id=current_user.user_id)
                logger.info(f"使用降级方案生成标题：{fallback_title}")
            except Exception as e2:
                logger.error(f"降级方案也失败了: {e2}", exc_info=True)
    else:
        logger.info(f"非第一轮对话，跳过标题生成")

    # 解析成果物
    artifacts = artifact_parser.parse_from_markdown(reply)
    logger.info(f"解析成果物完成，成果物数量: {len(artifacts)}")

    # 修复 HTML 成果物中的常见 AI 生成错误
    for artifact in artifacts:
        if artifact.type == 'html':
            original_content = artifact.content
            # 修复 === 后面跟空字符串的错误：==='' -> ==='
            fixed_content = original_content.split("==='").join("==='")
            fixed_content = fixed_content.split('===""').join('==="')
            # 如果有修复，更新 artifact 内容
            if fixed_content != original_content:
                fix_count = original_content.count("==='") + original_content.count('===""')
                logger.info(f"🔧 修复了 {fix_count} 处 HTML 语法错误（==='' -> ==='）")
                artifact.content = fixed_content

    for i, artifact in enumerate(artifacts):
        logger.info(f"  成果物 {i+1}: type={artifact.type}, language={artifact.language}, content长度={len(artifact.content)}")
        if artifact.type == 'html':
            logger.info(f"    HTML内容预览（前500字符）:\n{artifact.content[:500]}")
            logger.info(f"    HTML内容预览（后500字符）:\n{artifact.content[-500:]}")
            # 检查HTML是否完整
            if '</html>' not in artifact.content.lower():
                logger.warning(f"    ⚠️ HTML成果物缺少 </html> 闭合标签！")
            if '<body' in artifact.content.lower() and '</body>' not in artifact.content.lower():
                logger.warning(f"    ⚠️ HTML成果物缺少 </body> 闭合标签！")

    return ChatResponse(
        session_id=session_id,
        reply=reply,
        artifacts=artifacts
    )


@router.post("/tools/{tool_id}/chat/stream")
async def chat_stream(
    tool_id: str,
    request: ChatRequest,
    current_user: Annotated[UserInfo, Depends(get_current_user)] = None,
):
    """向指定工具发送消息，获取 AI 流式回复。如果 session_id 不存在，自动创建新会话。"""
    logger.info(f"🌊 流式聊天请求 - tool_id: {tool_id}, user: {current_user.username if current_user else 'None'}, message: {request.message[:50]}")
    tool_service = get_tool_service()
    session_service = get_session_service()
    ai_service = get_ai_service()
    title_generator = get_title_generator()

    # 验证工具是否存在
    tool = tool_service.get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    # 处理会话：如果 session_id 不存在，创建新会话
    session_id = request.session_id
    session = None

    if session_id:
        # 验证会话是否存在且属于当前用户
        session = session_service.get_session_by_id(session_id, user_id=current_user.user_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found"
            )
    else:
        # 创建新会话（基于第一条消息自动生成标题）
        session = session_service.create_session(
            user_id=current_user.user_id,
            tool_id=tool_id,
            first_message=request.message
        )
        session_id = session.session_id

    # 获取历史消息
    history_list = []
    if request.history:
        # 使用请求中提供的历史消息
        for msg in request.history:
            if msg.role not in ["user", "assistant"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的消息角色: {msg.role}，必须是 'user' 或 'assistant'"
                )
            history_list.append({
                "role": msg.role,
                "content": msg.content
            })
    else:
        # 从数据库读取历史消息
        messages = session_service.get_messages_by_session(session_id, user_id=current_user.user_id)
        for msg in messages:
            history_list.append({
                "role": msg.role,
                "content": msg.content
            })

    # 保存用户消息到数据库（显式控制时间戳，确保消息顺序）
    user_message_time = datetime.now()
    logger.info(f"保存用户消息 - 时间戳: {user_message_time}, 会话ID: {session_id}")
    session_service.add_message(
        session_id=session_id,
        role="user",
        content=request.message,
        user_id=current_user.user_id,
        created_at=user_message_time
    )

    # 流式生成回复
    async def generate_stream():
        full_reply = ""
        chunk_count = 0
        try:
            # 先发送 session_id
            yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"

            # 流式接收 AI 回复
            async for chunk in ai_service.chat_stream(
                system_prompt=tool.system_prompt,
                history=history_list,
                user_message=request.message
            ):
                if chunk:
                    chunk_count += 1
                    full_reply += chunk
                    # 发送内容块
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

            logger.info(f"流式输出完成 - 总chunk数: {chunk_count}, 总内容长度: {len(full_reply)} 字符")
            if 'html' in full_reply.lower() or '<html' in full_reply.lower():
                logger.info(f"HTML内容检测 - 包含<html>标签: {'<html' in full_reply.lower()}, 包含</html>标签: {'</html>' in full_reply.lower()}")
                logger.debug(f"HTML内容预览（前500字符）: {full_reply[:500]}")
                logger.debug(f"HTML内容预览（后500字符）: {full_reply[-500:]}")

            # 保存完整回复到数据库（确保晚于用户消息 1 秒，避免精度问题）
            ai_message_time = user_message_time + timedelta(seconds=1)
            logger.info(f"💾 准备保存 AI 消息 - 时间戳: {ai_message_time}, 会话ID: {session_id}, 内容长度: {len(full_reply)}")
            session_service.add_message(
                session_id=session_id,
                role="assistant",
                content=full_reply,
                user_id=current_user.user_id,
                created_at=ai_message_time
            )
            logger.info(f"✅ AI 消息已保存")

            # 检查是否是第一轮对话，如果是则生成标题
            messages = session_service.get_messages_by_session(session_id, user_id=current_user.user_id)
            logger.info(f"📊 会话消息数量检查 - 会话ID: {session_id}, 消息数: {len(messages)}")

            if len(messages) == 2:  # 第一轮对话：1条用户消息 + 1条AI回复
                try:
                    logger.info(f"🎯 检测到第一轮对话，开始生成会话标题 - 用户消息: {request.message[:50]}")
                    # 生成标题
                    title = await title_generator.generate_title(request.message, full_reply)
                    # 更新会话标题
                    session_service.update_session_title(session_id, title, user_id=current_user.user_id)
                    logger.info(f"✅ 会话标题已生成并更新：{title}")
                    # 发送标题生成完成事件
                    yield f"data: {json.dumps({'type': 'title_generated', 'title': title})}\n\n"
                except Exception as e:
                    logger.error(f"❌ 生成会话标题失败，使用降级方案: {e}", exc_info=True)
                    # 降级方案：使用简单截取
                    try:
                        fallback_title = title_generator._fallback_title(request.message)
                        session_service.update_session_title(session_id, fallback_title, user_id=current_user.user_id)
                        logger.info(f"⚠️ 使用降级方案生成标题：{fallback_title}")
                        # 发送降级标题事件
                        yield f"data: {json.dumps({'type': 'title_generated', 'title': fallback_title})}\n\n"
                    except Exception as e2:
                        logger.error(f"❌ 降级方案也失败了: {e2}", exc_info=True)
            else:
                logger.info(f"⏭️ 非第一轮对话，跳过标题生成（消息数: {len(messages)}）")

            # 解析成果物
            artifact_parser = get_artifact_parser()
            artifacts = artifact_parser.parse_from_markdown(full_reply)
            logger.info(f"解析成果物完成 - 成果物数量: {len(artifacts)}")

            # 修复 HTML 成果物中的常见 AI 生成错误
            for artifact in artifacts:
                if artifact.type == 'html':
                    original_content = artifact.content
                    # 修复 === 后面跟空字符串的错误：==='' -> ==='
                    fixed_content = original_content.split("==='").join("==='")
                    fixed_content = fixed_content.split('===""').join('==="')
                    # 如果有修复，更新 artifact 内容
                    if fixed_content != original_content:
                        fix_count = original_content.count("==='") + original_content.count('===""')
                        logger.info(f"🔧 [流式] 修复了 {fix_count} 处 HTML 语法错误（==='' -> ==='）")
                        artifact.content = fixed_content

            # 发送完成信号和成果物（转换为字典格式以便序列化）
            artifacts_dict = [
                {
                    'type': a.type,
                    'content': a.content,
                    'language': a.language,
                    'timestamp': a.timestamp.isoformat() if a.timestamp else None
                }
                for a in artifacts
            ]
            yield f"data: {json.dumps({'type': 'done', 'artifacts': artifacts_dict})}\n\n"

        except Exception as e:
            logger.error(f"流式对话异常: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )


@router.get("/tools/{tool_id}/conversations", response_model=ConversationListResponse)
async def get_conversations(
    tool_id: str,
    current_user: Annotated[UserInfo, Depends(get_current_user)] = None,
):
    """获取当前用户在当前工具下的所有历史对话列表"""
    tool_service = get_tool_service()
    session_service = get_session_service()

    # 验证工具是否存在
    tool = tool_service.get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    # 获取会话列表
    sessions = session_service.get_sessions_by_user_and_tool(
        user_id=current_user.user_id,
        tool_id=tool_id
    )

    # 转换为 API 响应格式
    conversations = [
        ConversationListItem(
            session_id=session.session_id,
            title=session.title,
            updated_at=session.updated_at
        )
        for session in sessions
    ]

    return ConversationListResponse(conversations=conversations)


@router.delete("/tools/{tool_id}/conversations/{conv_id}")
async def delete_conversation(
    tool_id: str,
    conv_id: str,
    current_user: Annotated[UserInfo, Depends(get_current_user)] = None,
):
    """删除指定对话"""
    session_service = get_session_service()
    success = session_service.delete_session(conv_id, user_id=current_user.user_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation '{conv_id}' not found"
        )

    return {"message": "Conversation deleted successfully"}


# ==================== 多模态生成接口 ====================
# TODO: 将此端点迁移到 interfaces/routers/tools/media.py
# 原因：完成DDD架构迁移，保持新旧架构分离
# 复杂度：高（~250行代码，涉及同步/异步模式、会话管理、任务状态）
# 优先级：中（端点工作正常，无紧急迁移需求）
# 创建日期: 2026-03-01

@router.post("/tools/{tool_id}/generate-media", response_model=MediaGenerateResponse)
async def generate_media(
    tool_id: str,
    media_request: MediaGenerateRequest,
    http_request: Request,
    current_user: Annotated[UserInfo, Depends(get_current_user)] = None,
):
    """
    多模态内容生成（图片、音频、视频）

    - **tool_id**: 工具ID（必须是多模态工具）
    - **message**: 用户提示词
    - **session_id**: 会话ID（可选，首次为空）
    - **size**: 生成尺寸（可选）
    - **count**: 生成数量（可选，1-4）
    - **style**: 生成风格（可选）

    Returns:
        包含task_id的响应，客户端需要轮询查询生成结果
    """
    try:
        logger.info(f"收到多模态生成请求 - 工具: {tool_id}, size={media_request.size}, count={media_request.count}, style={media_request.style}")

        tool_service = get_tool_service()
        session_service = get_session_service()
        ai_service = get_ai_service()
        title_generator = get_title_generator()

        # 1. 获取工具配置
        tool = tool_service.get_tool_by_id(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="工具不存在")

        # 验证是多模态工具
        if tool.content_type != "multimodal":
            raise HTTPException(
                status_code=400,
                detail=f"工具 {tool_id} 不支持多模态生成，请使用文本对话接口"
            )

        # 2. 创建或获取会话
        session_id = media_request.session_id
        if not session_id:
            # 首次生成，创建新会话
            session_id = str(uuid.uuid4())

            # 生成会话标题（只传用户提示词，不传AI回复）
            title = await title_generator.generate_title(
                user_message=media_request.message,
                ai_response=None
            )

            # 保存会话到数据库
            await session_service.create_session_with_id(
                session_id=session_id,
                user_id=current_user.user_id,
                tool_id=tool_id,
                title=title
            )

            logger.info(f"创建新会话 - session_id: {session_id}, 标题: {title}")
        else:
            # 验证会话所有权
            session = await session_service.get_session(session_id)
            if not session or session.user_id != current_user.user_id:
                raise HTTPException(status_code=403, detail="无权访问此会话")

        # 3. 保存用户消息
        user_message_id = str(uuid.uuid4())
        await session_service.save_message(
            message_id=user_message_id,
            session_id=session_id,
            role="user",
            content=media_request.message
        )

        # 4. 调用AI服务生成内容
        task_id = str(uuid.uuid4())

        try:
            # 根据媒体类型调用不同的生成方法
            if tool.media_type == "image":
                logger.info(f"开始调用GLM图像生成 - 提示词: {media_request.message[:50]}...")

                glm_result = await ai_service.generate_image(
                    prompt=media_request.message,
                    model_config=tool.model or "glm:cogview-4",
                    size=media_request.size,
                    count=media_request.count,
                    style=media_request.style
                )

                logger.info(f"GLM返回结果: {glm_result}")

                # 检查GLM是同步还是异步返回
                if glm_result.get("mode") == "sync":
                    # 同步模式：GLM直接返回了图片
                    # 提取图片URLs
                    image_data = glm_result.get("data", [])
                    media_urls = [img.get("url") for img in image_data if img.get("url")]

                    logger.info(f"获取到 {len(media_urls)} 张图片")

                    # 构建元数据
                    metadata = {
                        "size": media_request.size,
                        "count": len(media_urls),
                        "style": media_request.style
                    }

                    # 直接保存AI回复消息
                    ai_message_id = str(uuid.uuid4())
                    media_content_obj = MultiModalContent(
                        content_type="image",
                        media_urls=media_urls,
                        metadata=metadata
                    )

                    ai_message = Message(
                        message_id=ai_message_id,
                        session_id=session_id,
                        role="assistant",
                        content="",
                        created_at=None
                    )
                    ai_message.set_media_content(media_content_obj)

                    await session_service.save_message_with_media(
                        message_id=ai_message_id,
                        session_id=session_id,
                        role="assistant",
                        content="",
                        media_content=ai_message.media_content
                    )

                    # 标记为同步模式，直接返回完成状态
                    task_storage[task_id] = {
                        "session_id": session_id,
                        "status": "completed",
                        "media_urls": media_urls,
                        "metadata": metadata
                    }

                    logger.info(f"同步生成完成 - task_id: {task_id}, 图片数量: {len(media_urls)}")

                    # 直接返回完成状态，不需要前端轮询
                    return MediaGenerateResponse(
                        session_id=session_id,
                        message_id=ai_message_id,
                        task_id=task_id,
                        status="completed",
                        media_urls=media_urls,
                        content_type="image"
                    )

                else:
                    # 异步模式：需要轮询
                    async_result = glm_result.get("result", {})
                    glm_task_id = async_result.get("id") or async_result.get("task_id")

                    # 存储任务状态
                    task_storage[task_id] = {
                        "glm_task_id": glm_task_id,
                        "session_id": session_id,
                        "message_id": user_message_id,
                        "tool_id": tool_id,
                        "media_type": tool.media_type,
                        "status": "processing",
                        "request_params": {
                            "size": media_request.size,
                            "count": media_request.count,
                            "style": media_request.style
                        },
                        "query_fail_count": 0
                    }

                    logger.info(f"异步任务已提交 - task_id: {task_id}, glm_task_id: {glm_task_id}")

            elif tool.media_type == "audio":
                logger.info(f"开始调用GLM音频生成 - 文本: {media_request.message[:50]}...")

                glm_result = await ai_service.generate_audio(
                    prompt=media_request.message,
                    model_config=tool.model or "glm:glm-tts",
                    voice=media_request.voice if hasattr(media_request, 'voice') else None
                )

                logger.info(f"GLM返回结果: {glm_result}")

                # GLM-TTS是同步返回
                if glm_result.get("mode") == "sync":
                    # 提取音频URLs
                    audio_data = glm_result.get("data", [])
                    media_urls = [audio.get("url") for audio in audio_data if audio.get("url")]

                    # 将相对URL转换为绝对URL（确保前端可以正确访问）
                    media_urls = [make_absolute_url(url, http_request) for url in media_urls]

                    logger.info(f"获取到 {len(media_urls)} 个音频")

                    # 构建元数据
                    metadata = {
                        "text_length": len(media_request.message),
                        "voice": media_request.voice if hasattr(media_request, 'voice') else "default"
                    }

                    # 保存AI回复消息（包含音频URLs）
                    ai_message_id = str(uuid.uuid4())
                    media_content_obj = MultiModalContent(
                        content_type="audio",
                        media_urls=media_urls,
                        metadata=metadata
                    )

                    ai_message = Message(
                        message_id=ai_message_id,
                        session_id=session_id,
                        role="assistant",
                        content="",
                        created_at=None
                    )
                    ai_message.set_media_content(media_content_obj)

                    await session_service.save_message_with_media(
                        message_id=ai_message_id,
                        session_id=session_id,
                        role="assistant",
                        content="",
                        media_content=ai_message.media_content
                    )

                    # 标记为同步模式，直接返回完成状态
                    task_storage[task_id] = {
                        "session_id": session_id,
                        "status": "completed",
                        "media_urls": media_urls,
                        "metadata": metadata
                    }

                    logger.info(f"同步生成完成 - task_id: {task_id}, 音频数量: {len(media_urls)}")

                    # 直接返回完成状态，不需要前端轮询
                    return MediaGenerateResponse(
                        session_id=session_id,
                        message_id=ai_message_id,
                        task_id=task_id,
                        status="completed",
                        media_urls=media_urls,
                        content_type="audio"
                    )

            elif tool.media_type == "video":
                logger.info(f"开始调用GLM视频生成 - 提示词: {media_request.message[:50]}...")

                glm_result = await ai_service.generate_video(
                    prompt=media_request.message,
                    model_config=tool.model or "glm:cogvideox-2",
                    size=media_request.size,
                    fps=media_request.fps if hasattr(media_request, 'fps') else None,
                    quality=media_request.quality if hasattr(media_request, 'quality') else None,
                    with_audio=media_request.with_audio if hasattr(media_request, 'with_audio') else False
                )

                logger.info(f"GLM返回结果: {glm_result}")

                # CogVideoX是异步返回，需要轮询
                if glm_result.get("mode") == "async":
                    async_result = glm_result.get("result", {})
                    glm_task_id = async_result.get("id") or async_result.get("task_id")

                    # 存储任务状态
                    task_storage[task_id] = {
                        "glm_task_id": glm_task_id,
                        "session_id": session_id,
                        "message_id": user_message_id,
                        "tool_id": tool_id,
                        "media_type": tool.media_type,
                        "status": "processing",
                        "request_params": {
                            "size": media_request.size,
                            "fps": media_request.fps if hasattr(media_request, 'fps') else None,
                            "quality": media_request.quality if hasattr(media_request, 'quality') else None
                        },
                        "query_fail_count": 0
                    }

                    logger.info(f"异步任务已提交 - task_id: {task_id}, glm_task_id: {glm_task_id}")

            else:
                raise HTTPException(status_code=400, detail=f"不支持的媒体类型: {tool.media_type}")

        except Exception as e:
            logger.error(f"调用AI生成服务失败: {e}", exc_info=True)
            raise HTTPException(status_code=503, detail=f"AI服务调用失败: {str(e)}")

        # 5. 返回响应
        return MediaGenerateResponse(
            session_id=session_id,
            message_id=user_message_id,
            task_id=task_id,
            status="processing"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"多模态生成接口异常: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
