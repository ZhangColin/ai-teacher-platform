# -*- coding: utf-8 -*-
"""
文件上传 API 路由

提供统一的文件上传接口，根据目标供应商自动选择处理策略
"""
import logging
import os
import tempfile
import uuid
from typing import Optional

from fastapi import APIRouter, UploadFile, Query, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.interfaces.dependencies import get_current_user
from src.db_models import UserModel
from src.services.file_parser_service import FileParserService
from src.infrastructure.providers.factory import ProviderFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["文件上传"])


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    provider: str = Query(..., description="目标供应商: kimi, deepseek, openai"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    统一文件上传接口

    根据目标供应商自动选择处理策略：
    - kimi/openai/claude: 上传到供应商服务器，返回 file_id
    - deepseek/glm: 本地解析文本，返回文本内容

    Args:
        file: 上传的文件
        provider: 目标供应商
        current_user: 当前用户
        db: 数据库会话

    Returns:
        {
            "success": True,
            "file_id": "...",  // API 模式
            "content": "...",  // 文本提取模式
            "provider": "kimi",
            "mode": "api" | "text_extraction"
        }
    """
    # 验证供应商
    if not ProviderFactory.is_provider_registered(provider):
        raise HTTPException(status_code=400, detail=f"不支持的供应商: {provider}")

    # 保存临时文件
    temp_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = os.path.join(tempfile.gettempdir(), temp_filename)

    try:
        # 保存上传的文件
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        file_size = len(content)
        logger.info(f"User {current_user.username} uploaded file: {file.filename} ({file_size} bytes)")

        # 根据供应商选择处理策略
        if provider in {"kimi", "openai"}:
            # API 模式 - 上传到供应商服务器
            # 注意：实际使用时需要从 ModelProviderService 获取 API key
            # 这里简化处理，传入空字符串，生产环境需要修改
            from src.services.model_provider_service import ModelProviderService
            provider_service = ModelProviderService(db)

            # 获取供应商配置
            provider_config = provider_service.get_provider_by_code(provider)
            if not provider_config or not provider_config.is_enabled:
                raise HTTPException(status_code=400, detail=f"供应商 {provider} 未配置或未启用")

            # 获取解密后的 API key
            api_key = provider_service.get_provider_api_key(provider_config.id)

            provider_instance = ProviderFactory.create(
                provider_name=provider,
                api_key=api_key,
                base_url=provider_config.base_url
            )
            file_id = await provider_instance.upload_file(temp_path, file.filename)

            if file_id:
                return {
                    "success": True,
                    "file_id": file_id,
                    "filename": file.filename,
                    "provider": provider,
                    "mode": "api"
                }
            else:
                raise HTTPException(status_code=500, detail="文件上传失败")

        else:
            # 文本提取模式
            parser = FileParserService()
            text_content = await parser.parse_file(temp_path, file.filename)

            # 生成预览（前 500 字符）
            preview = text_content[:500] if len(text_content) > 500 else text_content

            return {
                "success": True,
                "content": text_content,
                "content_preview": preview,
                "filename": file.filename,
                "provider": provider,
                "mode": "text_extraction"
            }

    except ValueError as e:
        # 不支持的文件格式
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)
