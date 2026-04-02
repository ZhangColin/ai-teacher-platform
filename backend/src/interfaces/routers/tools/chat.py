# -*- coding: utf-8 -*-
"""
工具对话路由

提供工具对话接口，支持流式和非流式两种模式
"""
import logging
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from src.models import ChatRequest, ChatResponse, Message, Artifact, UserInfo
from src.interfaces.dependencies import (
    get_ai_service_with_db,
    get_session_service,
    get_config_service,
    get_artifact_parser,
    get_title_generator,
)
from src.services.ai_service import AIService
from src.services.session_service import SessionService
from src.services.config_service import ConfigService
from src.services.token_service import TokenService
from src.services.point_service import PointService
from src.database import get_db
from typing import Annotated
from src.interfaces.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tools/{tool_id}/chat/stream", tags=["对话"])
async def chat_stream(
    tool_id: str,
    request: ChatRequest,
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    ai_service: AIService = Depends(get_ai_service_with_db),
    session_service: SessionService = Depends(get_session_service),
    config_service: ConfigService = Depends(get_config_service),
    title_generator = Depends(get_title_generator),
):
    """
    流式对话接口

    使用Server-Sent Events (SSE)返回AI的流式响应
    """
    # 获取工具配置
    tool = config_service.get_tool_by_id(tool_id)

    # 调试输出 - 打印完整请求
    import json
    logger.info(f"🔍 收到请求: {json.dumps({'tool_id': tool_id, 'model': request.model, 'message': request.message[:50] if request.message else None})}")
    logger.info(f"🔍 查找工具: tool_id='{tool_id}'")
    logger.info(f"🔍 找到工具: {tool}")

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    if not tool.visible:
        raise HTTPException(status_code=403, detail="Tool is not available")

    try:
        # 处理会话：如果 session_id 不存在，创建新会话
        session_id = request.session_id
        session = None

        if not session_id:
            # 创建新会话
            session = session_service.create_session(
                user_id=current_user.user_id,
                tool_id=tool_id,
                title=request.message[:50]  # 使用消息前50字作为临时标题
            )
            session_id = session.session_id
            logger.info(f"✅ 创建新会话: {session_id}")
        else:
            # 获取现有会话
            session = await session_service.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
            if session.user_id != current_user.user_id:
                raise HTTPException(status_code=403, detail="Access denied")

        # 准备消息历史
        if request.history:
            # 使用请求中提供的历史
            history_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in request.history
            ]
        else:
            # 从数据库读取历史
            db_messages = session_service.get_session_messages(session_id)
            history_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in db_messages
            ]

        # 保存用户消息
        session_service.add_message(
            session_id=session_id,
            role="user",
            content=request.message,
            user_id=current_user.user_id
        )

        # 准备模型配置（优先级：用户请求 > 会话模型 > 工具默认模型）
        model_config = request.model  # 用户手动选择的模型
        if not model_config and session and session.model_provider and session.model_name:
            # 会话级别的模型
            model_config = f"{session.model_provider}:{session.model_name}"
        if not model_config:
            # 工具默认模型
            model_config = tool.model if tool.model else None

        logger.info(f"📊 使用模型配置: {model_config or '系统默认'}")

        # 获取流式响应
        async def generate():
            # 直接获取 logger 以避免作用域问题
            import logging
            _logger = logging.getLogger(__name__)
            try:
                # 检查积分（在开始 AI 请求之前）
                db = next(get_db())
                try:
                    point_service = PointService(db)
                    # 捕获可能的异常，确保返回友好的错误消息
                    try:
                        logger.info(f"🔍 开始积分检查 - 用户:{current_user.user_id}")
                        has_points = point_service.check_points_before_request(current_user.user_id)
                        logger.info(f"🔍 积分检查结果 - has_points:{has_points}")
                        if not has_points:
                            logger.warning(f"🚫 积分不足，拒绝请求 - 用户:{current_user.user_id}")
                            yield f"data: {json.dumps({'type': 'error', 'error': '积分不足，请联系企业管理员充值'}, ensure_ascii=False)}\n\n"
                            yield "data: [DONE]\n\n"
                            return
                    except ValueError as e:
                        # 处理用户未关联企业等异常情况
                        error_msg = str(e)
                        logger.error(f"🚫 积分检查异常 - 用户:{current_user.user_id}, 错误:{error_msg}")
                        if "未关联企业" in error_msg:
                            yield f"data: {json.dumps({'type': 'error', 'error': '您尚未关联企业，请联系管理员'}, ensure_ascii=False)}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'error', 'error': f'积分检查失败：{error_msg}'}, ensure_ascii=False)}\n\n"
                        yield "data: [DONE]\n\n"
                        return
                finally:
                    db.close()

                # 首先发送 session_id 事件（如果是新会话）
                session_event = json.dumps({
                    "type": "session_id",
                    "session_id": session_id
                }, ensure_ascii=False)
                yield f"data: {session_event}\n\n"

                full_response = ""
                usage_info = None  # 用于存储最终的usage信息

                async for chunk in ai_service.chat_stream(
                    system_prompt=tool.system_prompt,
                    history=history_messages,
                    user_message=request.message,
                    model_config=model_config
                ):
                    # 检查是否是usage信息（字典类型）
                    if isinstance(chunk, dict):
                        if chunk.get('type') == 'usage':
                            usage_info = chunk
                            _logger.info(f"📊 收到Token使用信息: {usage_info}")
                            continue  # 不发送usage信息给前端
                    else:
                        # 普通内容chunk
                        full_response += chunk
                        # 发送SSE格式数据
                        yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

                # 发送结束标记
                yield "data: [DONE]\n\n"

                # 解析模型信息（优先从 usage_info 获取，其次从 model_config 解析）
                # usage_info 中的模型信息是 AI 服务实际使用的模型，更可靠
                model_provider = None
                model_name = None
                if usage_info:
                    model_provider = usage_info.get('model_provider')
                    model_name = usage_info.get('model_name')
                # 如果 usage_info 中没有模型信息，从 model_config 解析
                if not model_provider and not model_name and model_config and ":" in model_config:
                    model_provider, model_name = model_config.split(":", 1)

                # 保存AI消息（带token信息）并捕获返回的 message_id
                ai_message = session_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                    user_id=current_user.user_id,
                    model_provider=model_provider,
                    model_name=model_name,
                    prompt_tokens=usage_info.get('prompt_tokens') if usage_info else None,
                    completion_tokens=usage_info.get('completion_tokens') if usage_info else None,
                    total_tokens=usage_info.get('total_tokens') if usage_info else None
                )
                ai_message_id = ai_message.message_id  # 直接获取 message_id
                _logger.info(f"✅ AI 消息已保存（含token信息）, message_id: {ai_message_id}")

                # 记录消息数量（用户消息 + AI消息 = 2），用于后续判断是否第一轮对话
                messages_count_after_ai = 2

                # 记录Token使用日志
                if usage_info and model_provider and model_name:
                    try:
                        # 创建token日志
                        from sqlalchemy.orm import Session
                        db = next(get_db())
                        try:
                            token_service = TokenService(db)
                            token_service.create_token_log(
                                user_id=current_user.user_id,
                                session_id=session_id,
                                message_id=ai_message_id,
                                model_provider=model_provider,
                                model_name=model_name,
                                prompt_tokens=usage_info['prompt_tokens'],
                                completion_tokens=usage_info['completion_tokens'],
                                total_tokens=usage_info['total_tokens']
                            )
                            _logger.info(f"✅ Token日志已记录")
                        finally:
                            db.close()
                    except Exception as e:
                        _logger.error(f"❌ 记录Token日志失败: {e}", exc_info=True)

                # 扣减积分（不满一积分的，扣除一积分）
                print(f"[积分扣减调试] usage_info={bool(usage_info)}, model_provider={model_provider}, model_name={model_name}, ai_message_id={ai_message_id}")
                if usage_info:
                    print(f"[积分扣减调试] usage_info内容: {usage_info}")
                if usage_info and model_provider and model_name and ai_message_id:
                    print(f"[积分扣减调试] 条件满足，开始扣减积分")
                    try:
                        db = next(get_db())
                        try:
                            point_service = PointService(db)
                            points = usage_info.get('points_deducted', 0)
                            # 确保至少扣除1积分
                            points = max(1, points)
                            print(f"[积分扣减调试] 准备扣减积分: points={points}")
                            consumption = point_service.deduct_points(
                                enterprise_id=current_user.enterprise_id,
                                user_id=current_user.user_id,
                                session_id=session_id,
                                message_id=ai_message_id,
                                model_provider=model_provider,
                                model_name=model_name,
                                prompt_tokens=usage_info.get('prompt_tokens', 0),
                                completion_tokens=usage_info.get('completion_tokens', 0),
                                points=points
                            )
                            # 🔥 关键修复：提交事务，确保数据写入数据库
                            db.commit()
                            print(f"[积分扣减调试] ✅ 积分扣减完成 - 消耗:{points}（赠送:{consumption.gratis_points_used}, 充值:{consumption.paid_points_used}）")
                            _logger.info(f"✅ 积分扣减完成 - 消耗:{points}（赠送:{consumption.gratis_points_used}, 充值:{consumption.paid_points_used}）")
                        finally:
                            db.close()
                    except Exception as e:
                        print(f"[积分扣减调试] ❌ 积分扣减失败: {e}")
                        _logger.error(f"❌ 积分扣减失败: {e}", exc_info=True)
                else:
                    print(f"[积分扣减调试] ❌ 条件不满足，跳过积分扣减")

                # 更新会话的模型选择（如果用户手动选择了模型）
                if request.model and model_provider and model_name:
                    session_service.update_session_model(
                        session_id=session_id,
                        model_provider=model_provider,
                        model_name=model_name,
                        user_id=current_user.user_id
                    )
                    _logger.info(f"✅ 会话模型已更新为 {model_provider}:{model_name}")

                # 检查是否是第一轮对话，如果是则生成标题
                _logger.info(f"📊 会话消息数量检查 - 会话ID: {session_id}, 消息数: {messages_count_after_ai}")

                if messages_count_after_ai == 2:  # 第一轮对话：1条用户消息 + 1条AI回复
                    try:
                        _logger.info(f"🎯 检测到第一轮对话，开始生成会话标题 - 用户消息: {request.message[:50]}")
                        # 生成标题（带 token 信息）
                        title, title_usage = await title_generator.generate_title_with_usage(
                            user_message=request.message,
                            ai_response=full_response,
                            model_provider=model_provider,
                            model_name=model_name
                        )
                        # 更新会话标题
                        session_service.update_session_title(session_id, title, user_id=current_user.user_id)
                        _logger.info(f"✅ 会话标题已生成并更新：{title}")
                        # 发送标题生成完成事件（包含 session_id，前端用于刷新列表）
                        yield f"data: {json.dumps({'type': 'title_generated', 'session_id': session_id, 'title': title}, ensure_ascii=False)}\n\n"

                        # 扣减标题生成的积分
                        if title_usage and title_usage.get('total_tokens', 0) > 0:
                            try:
                                db_title = next(get_db())
                                try:
                                    point_service_title = PointService(db_title)
                                    # 计算积分
                                    points = point_service_title.calculate_points_from_tokens(
                                        provider_code=model_provider,
                                        model_code=model_name,
                                        prompt_tokens=title_usage.get('prompt_tokens', 0),
                                        completion_tokens=title_usage.get('completion_tokens', 0)
                                    )
                                    points = max(1, points)  # 至少扣除1积分

                                    # 扣减积分
                                    consumption = point_service_title.deduct_points(
                                        enterprise_id=current_user.enterprise_id,
                                        user_id=current_user.user_id,
                                        session_id=session_id,
                                        message_id="",  # 标题生成没有关联消息
                                        model_provider=model_provider,
                                        model_name=model_name,
                                        prompt_tokens=title_usage.get('prompt_tokens', 0),
                                        completion_tokens=title_usage.get('completion_tokens', 0),
                                        points=points
                                    )
                                    _logger.info(f"✅ 标题生成积分扣减完成 - 消耗:{points}（赠送:{consumption.gratis_points_used}, 充值:{consumption.paid_points_used}）")
                                finally:
                                    db_title.close()
                            except Exception as e:
                                _logger.error(f"❌ 标题生成扣积分失败: {e}", exc_info=True)
                    except Exception as e:
                        _logger.error(f"❌ 生成会话标题失败，使用降级方案: {e}", exc_info=True)
                        # 降级方案：使用简单截取
                        try:
                            fallback_title = title_generator._fallback_title(request.message)
                            session_service.update_session_title(session_id, fallback_title, user_id=current_user.user_id)
                            _logger.info(f"⚠️ 使用降级方案生成标题：{fallback_title}")
                            # 发送降级标题事件
                            yield f"data: {json.dumps({'type': 'title_generated', 'session_id': session_id, 'title': fallback_title}, ensure_ascii=False)}\n\n"
                        except Exception as e2:
                            _logger.error(f"❌ 降级方案也失败了: {e2}", exc_info=True)
                else:
                    _logger.info(f"⏭️ 非第一轮对话，跳过标题生成（消息数: {messages_count_after_ai}）")

            except Exception as e:
                _logger.error(f"Chat stream error: {e}")
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/{tool_id}/chat", response_model=ChatResponse, tags=["对话"])
async def chat_non_stream(
    tool_id: str,
    request: ChatRequest,
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    ai_service: AIService = Depends(get_ai_service_with_db),
    session_service: SessionService = Depends(get_session_service),
    config_service: ConfigService = Depends(get_config_service),
    artifact_parser = Depends(get_artifact_parser),
    title_generator = Depends(get_title_generator),
):
    """
    非流式对话接口

    返回完整的AI响应
    """
    # 获取工具配置
    tool = config_service.get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    if not tool.visible:
        raise HTTPException(status_code=403, detail="Tool is not available")

    try:
        # 处理会话
        session_id = request.session_id
        session = None

        if not session_id:
            # 创建新会话
            session = session_service.create_session(
                user_id=current_user.user_id,
                tool_id=tool_id,
                title=request.message[:50]
            )
            session_id = session.session_id
        else:
            # 获取现有会话
            session = await session_service.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
            if session.user_id != current_user.user_id:
                raise HTTPException(status_code=403, detail="Access denied")

        # 准备消息历史
        if request.history:
            history_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in request.history
            ]
        else:
            # 从数据库读取历史
            db_messages = session_service.get_session_messages(session_id)
            history_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in db_messages
            ]

        # 保存用户消息
        session_service.add_message(
            session_id=session_id,
            role="user",
            content=request.message,
            user_id=current_user.user_id
        )

        # 准备模型配置（优先级：用户请求 > 会话模型 > 工具默认模型）
        model_config = request.model  # 用户手动选择的模型
        if not model_config and session and session.model_provider and session.model_name:
            # 会话级别的模型
            model_config = f"{session.model_provider}:{session.model_name}"
        if not model_config:
            # 工具默认模型
            model_config = tool.model if tool.model else None

        logger.info(f"📊 使用模型配置: {model_config or '系统默认'}")

        # 检查积分（在调用 AI 请求之前）
        db = next(get_db())
        try:
            point_service = PointService(db)
            try:
                has_points = point_service.check_points_before_request(current_user.user_id)
                if not has_points:
                    raise HTTPException(status_code=402, detail="积分不足，请联系企业管理员充值")
            except ValueError as e:
                error_msg = str(e)
                if "未关联企业" in error_msg:
                    raise HTTPException(status_code=400, detail="您尚未关联企业，请联系管理员")
                else:
                    raise HTTPException(status_code=500, detail=f"积分检查失败：{error_msg}")
        finally:
            db.close()

        # 获取AI响应（现在返回元组：(content, usage_info)）
        response_content, usage_info = await ai_service.chat(
            system_prompt=tool.system_prompt,
            history=history_messages,
            user_message=request.message,
            model_config=model_config
        )

        # 解析模型信息（优先从 usage_info 获取，其次从 model_config 解析）
        # usage_info 中的模型信息是 AI 服务实际使用的模型，更可靠
        model_provider = None
        model_name = None
        if usage_info:
            model_provider = usage_info.get('model_provider')
            model_name = usage_info.get('model_name')
        # 如果 usage_info 中没有模型信息，从 model_config 解析
        if not model_provider and not model_name and model_config and ":" in model_config:
            model_provider, model_name = model_config.split(":", 1)

        # 保存AI消息（带token信息）并捕获返回的 message_id
        ai_message = session_service.add_message(
            session_id=session_id,
            role="assistant",
            content=response_content,
            user_id=current_user.user_id,
            model_provider=model_provider,
            model_name=model_name,
            prompt_tokens=usage_info.get('prompt_tokens') if usage_info else None,
            completion_tokens=usage_info.get('completion_tokens') if usage_info else None,
            total_tokens=usage_info.get('total_tokens') if usage_info else None
        )
        ai_message_id = ai_message.message_id  # 直接获取 message_id
        logger.info(f"✅ AI 消息已保存（含token信息）, message_id: {ai_message_id}")

        # 记录消息数量（用户消息 + AI消息 = 2），用于后续判断是否第一轮对话
        messages_count_after_ai = 2

        # 记录Token使用日志
        if usage_info and model_provider and model_name:
            try:
                # 创建token日志
                db = next(get_db())
                try:
                    token_service = TokenService(db)
                    token_service.create_token_log(
                        user_id=current_user.user_id,
                        session_id=session_id,
                        message_id=ai_message_id,
                        model_provider=model_provider,
                        model_name=model_name,
                        prompt_tokens=usage_info['prompt_tokens'],
                        completion_tokens=usage_info['completion_tokens'],
                        total_tokens=usage_info['total_tokens']
                    )
                    logger.info(f"✅ Token日志已记录")
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"❌ 记录Token日志失败: {e}", exc_info=True)

        # 扣减积分（主消息响应的积分）
        if usage_info and model_provider and model_name:
            try:
                db = next(get_db())
                try:
                    point_service = PointService(db)
                    points = usage_info.get('points_deducted', 0)
                    # 确保至少扣除1积分
                    points = max(1, points)
                    consumption = point_service.deduct_points(
                        enterprise_id=current_user.enterprise_id,
                        user_id=current_user.user_id,
                        session_id=session_id,
                        message_id=ai_message_id,
                        model_provider=model_provider,
                        model_name=model_name,
                        prompt_tokens=usage_info.get('prompt_tokens', 0),
                        completion_tokens=usage_info.get('completion_tokens', 0),
                        points=points
                    )
                    # 🔥 关键修复：提交事务，确保数据写入数据库
                    db.commit()
                    logger.info(f"✅ 积分扣减完成 - 消耗:{points}（赠送:{consumption.gratis_points_used}, 充值:{consumption.paid_points_used}）")
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"❌ 积分扣减失败: {e}", exc_info=True)

        # 更新会话的模型选择（如果用户手动选择了模型）
        if request.model and model_provider and model_name:
            session_service.update_session_model(
                session_id=session_id,
                model_provider=model_provider,
                model_name=model_name,
                user_id=current_user.user_id
            )
            logger.info(f"✅ 会话模型已更新为 {model_provider}:{model_name}")

        # 解析成果物
        artifacts = artifact_parser.parse_from_markdown(response_content)

        # 检查是否是第一轮对话，如果是则生成标题
        logger.info(f"会话消息数量检查 - 会话ID: {session_id}, 消息数: {messages_count_after_ai}")

        if messages_count_after_ai == 2:  # 第一轮对话：1条用户消息 + 1条AI回复
            try:
                logger.info(f"检测到第一轮对话，开始生成会话标题 - 用户消息: {request.message[:50]}")
                # 生成标题（带 token 信息）
                title, title_usage = await title_generator.generate_title_with_usage(
                    user_message=request.message,
                    ai_response=response_content,
                    model_provider=model_provider,
                    model_name=model_name
                )
                # 更新会话标题
                session_service.update_session_title(session_id, title, user_id=current_user.user_id)
                logger.info(f"会话标题已生成并更新：{title}")

                # 扣减标题生成的积分
                if title_usage and title_usage.get('total_tokens', 0) > 0:
                    try:
                        db_title = next(get_db())
                        try:
                            point_service_title = PointService(db_title)
                            # 计算积分
                            points = point_service_title.calculate_points_from_tokens(
                                provider_code=model_provider,
                                model_code=model_name,
                                prompt_tokens=title_usage.get('prompt_tokens', 0),
                                completion_tokens=title_usage.get('completion_tokens', 0)
                            )
                            points = max(1, points)  # 至少扣除1积分

                            # 扣减积分
                            consumption = point_service_title.deduct_points(
                                enterprise_id=current_user.enterprise_id,
                                user_id=current_user.user_id,
                                session_id=session_id,
                                message_id="",  # 标题生成没有关联消息
                                model_provider=model_provider,
                                model_name=model_name,
                                prompt_tokens=title_usage.get('prompt_tokens', 0),
                                completion_tokens=title_usage.get('completion_tokens', 0),
                                points=points
                            )
                            logger.info(f"✅ 标题生成积分扣减完成 - 消耗:{points}（赠送:{consumption.gratis_points_used}, 充值:{consumption.paid_points_used}）")
                        finally:
                            db_title.close()
                    except Exception as e:
                        logger.error(f"❌ 标题生成扣积分失败: {e}", exc_info=True)
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

        # 构建响应（包含token信息）
        from src.models import TokenUsage
        token_usage = None
        if usage_info and model_provider and model_name:
            token_usage = TokenUsage(
                model_provider=model_provider,
                model_name=model_name,
                prompt_tokens=usage_info.get('prompt_tokens', 0),
                completion_tokens=usage_info.get('completion_tokens', 0),
                total_tokens=usage_info.get('total_tokens', 0)
            )

        return ChatResponse(
            reply=response_content,
            artifacts=artifacts,
            session_id=session_id,
            token_usage=token_usage
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
