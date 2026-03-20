# -*- coding: utf-8 -*-
"""
工具列表路由

提供工具列表查询接口，支持获取所有工具或按工具集过滤
"""
from fastapi import APIRouter, Depends
from src.models import ToolListResponse
from src.interfaces.dependencies import get_config_service, get_current_user
from src.services.config_service import ConfigService

router = APIRouter()


@router.get("/tools", response_model=ToolListResponse, tags=["工具"])
async def get_tools(
    current_user = Depends(get_current_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    获取所有工具列表

    返回所有可见的工具，按分类组织
    """
    # 加载所有工具（只返回 visible=true 的工具）
    tools = config_service.get_all_tools()

    # 获取分类配置
    category_config = config_service.get_category_config()

    # 按 category 聚合
    category_groups = []
    categories_dict = {}

    for tool in tools:
        category_name = tool.category

        # 如果分类不存在，创建新分类
        if category_name not in categories_dict:
            categories_dict[category_name] = {
                'name': category_name,
                'icon': category_config.get(category_name, {}).get('icon'),
                'tools': []
            }

        # 添加工具到分类
        categories_dict[category_name]['tools'].append({
            'tool_id': tool.tool_id,
            'name': tool.name,
            'description': tool.description,
            'icon': tool.icon,
            'category': tool.category,
            'visible': tool.visible,
            'type': tool.type,
            'welcome_message': tool.welcome_message,
            'toolset_id': tool.toolset_id,
            'model': tool.model,
            'content_type': tool.content_type,
            'media_type': tool.media_type,
        })

    # 转换为列表并按 order 排序
    category_groups = list(categories_dict.values())
    category_groups.sort(key=lambda x: category_config.get(x['name'], {}).get('order', 999))

    return ToolListResponse(categories=category_groups)


@router.get("/toolsets/{toolset_id}/tools", response_model=ToolListResponse, tags=["工具"])
async def get_toolset_tools(
    toolset_id: str,
    current_user = Depends(get_current_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    获取指定工具集的工具列表

    Args:
        toolset_id: 工具集ID（如 ai_tools, teaching_researcher）

    Returns:
        指定工具集的工具列表，按分类组织
    """
    # 加载指定工具集的工具
    tools = config_service.get_tools_by_toolset(toolset_id)

    # 获取分类配置
    category_config = config_service.get_category_config(toolset_id)

    # 按 category 聚合
    category_groups = []
    categories_dict = {}

    for tool in tools:
        category_name = tool.category

        # 如果分类不存在，创建新分类
        if category_name not in categories_dict:
            categories_dict[category_name] = {
                'name': category_name,
                'icon': category_config.get(category_name, {}).get('icon'),
                'tools': []
            }

        # 添加工具到分类
        categories_dict[category_name]['tools'].append({
            'tool_id': tool.tool_id,
            'name': tool.name,
            'description': tool.description,
            'icon': tool.icon,
            'category': tool.category,
            'visible': tool.visible,
            'type': tool.type,
            'welcome_message': tool.welcome_message,
            'toolset_id': tool.toolset_id,
            'model': tool.model,
            'content_type': tool.content_type,
            'media_type': tool.media_type,
        })

    # 转换为列表并按 order 排序
    category_groups = list(categories_dict.values())
    category_groups.sort(key=lambda x: category_config.get(x['name'], {}).get('order', 999))

    return ToolListResponse(categories=category_groups)
