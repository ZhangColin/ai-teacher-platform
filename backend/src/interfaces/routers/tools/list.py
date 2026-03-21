# -*- coding: utf-8 -*-
"""
工具列表路由

提供工具列表查询接口，支持获取所有工具或按导航模块过滤
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models import ToolListResponse
from src.interfaces.dependencies import get_config_service, get_current_user, get_db
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
            'navigation_module_id': tool.navigation_module_id,
            'model': tool.model,
            'content_type': tool.content_type,
            'media_type': tool.media_type,
        })

    # 转换为列表并按 order 排序
    category_groups = list(categories_dict.values())
    category_groups.sort(key=lambda x: category_config.get(x['name'], {}).get('order', 999))

    return ToolListResponse(categories=category_groups)


@router.get("/navigation-modules/{module_id}/tools", response_model=ToolListResponse, tags=["工具"])
async def get_navigation_module_tools(
    module_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定导航模块的工具列表

    Args:
        module_id: 导航模块ID（支持UUID或config_source值，如 ai-tools、teaching-researcher）

    Returns:
        该模块的工具列表，按分类组织
    """
    from src.db_models import NavigationModuleModel, AIToolModel, AIToolCategoryModel

    # 查找导航模块 - 先尝试按ID查找，再尝试按config_source查找
    nav_module = db.query(NavigationModuleModel).filter(
        NavigationModuleModel.id == module_id
    ).first()

    if not nav_module:
        # 尝试将简短ID（如 ai-tools）转换为 config_source（如 tools/ai_tools）
        config_source = f"tools/{module_id.replace('-', '_')}"
        nav_module = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.config_source == config_source
        ).first()

    if not nav_module:
        raise HTTPException(status_code=404, detail="导航模块不存在")

    # 使用找到的模块ID（UUID）查询工具和分类
    nav_module_id = str(nav_module.id)

    # 查询该模块下的工具
    tools = db.query(AIToolModel).filter(
        AIToolModel.navigation_module_id == nav_module_id,
        AIToolModel.visible == True
    ).order_by(AIToolModel.order).all()

    # 查询分类
    categories = db.query(AIToolCategoryModel).filter(
        AIToolCategoryModel.navigation_module_id == nav_module_id
    ).order_by(AIToolCategoryModel.order).all()

    # 构建分类字典
    categories_dict = {str(cat.id): cat for cat in categories}

    # 按分类聚合工具
    category_groups = {}
    for tool in tools:
        cat_id = tool.category_id or "uncategorized"
        if cat_id not in category_groups:
            if cat_id == "uncategorized":
                category_groups[cat_id] = {
                    'name': '未分类',
                    'icon': None,
                    'tools': []
                }
            elif str(cat_id) in categories_dict:
                category_groups[cat_id] = {
                    'name': categories_dict[str(cat_id)].name,
                    'icon': categories_dict[str(cat_id)].icon,
                    'tools': []
                }

        category_groups[cat_id]['tools'].append({
            'tool_id': tool.tool_id,
            'name': tool.name,
            'description': tool.description,
            'icon': tool.icon,
            'category': categories_dict[str(tool.category_id)].name if tool.category_id and str(tool.category_id) in categories_dict else '',
            'visible': tool.visible,
            'type': tool.type.value,
            'welcome_message': tool.welcome_message,
            'navigation_module_id': str(tool.navigation_module_id),
            'model': tool.model,
            'content_type': tool.content_type,
            'media_type': tool.media_type,
        })

    # 转换为列表并按 order 排序
    result_list = []
    for cat in categories:
        if str(cat.id) in category_groups:
            result_list.append(category_groups[str(cat.id)])

    return ToolListResponse(categories=result_list)


# 保留旧路由以保持向后兼容（废弃）
@router.get("/toolsets/{toolset_id}/tools", response_model=ToolListResponse, tags=["工具"], deprecated=True)
async def get_toolset_tools_deprecated(
    toolset_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定工具集的工具列表（已废弃，请使用 /navigation-modules/{module_id}/tools）

    Args:
        toolset_id: 工具集ID（如 ai_tools, teaching_researcher）

    Returns:
        指定工具集的工具列表，按分类组织
    """
    # 尝试通过 config_source 查找导航模块
    from src.db_models import NavigationModuleModel, AIToolModel, AIToolCategoryModel

    nav_module = db.query(NavigationModuleModel).filter(
        NavigationModuleModel.config_source == f"tools/{toolset_id}"
    ).first()

    if not nav_module:
        # 如果找不到，尝试使用 toolset_id 作为 module_id
        nav_module = db.query(NavigationModuleModel).filter(
            NavigationModuleModel.id == toolset_id
        ).first()

    if not nav_module:
        raise HTTPException(status_code=404, detail="工具集不存在")

    # 使用新的路由逻辑
    return await get_navigation_module_tools(str(nav_module.id), current_user, db)
