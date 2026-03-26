# -*- coding: utf-8 -*-
"""配置服务：从数据库加载配置"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from ..db_models import (
    NavigationModuleModel, AIToolCategoryModel, AIToolModel,
    NavigationModuleType, AIToolType
)
from ..models import NavigationModule, Tool

logger = logging.getLogger(__name__)


class ConfigService:
    """配置服务：从数据库读取配置"""

    def __init__(self, db: Session):
        self.db = db

    def get_navigation_modules(self) -> List[NavigationModule]:
        """获取导航模块列表"""
        models = self.db.query(NavigationModuleModel).order_by(NavigationModuleModel.order).all()
        return [
            NavigationModule(
                name=m.name,
                type=m.type.value,
                config_source=m.config_source,
                page_path=m.page_path,
                icon=m.icon,
                order=m.order
            )
            for m in models
        ]

    def get_tools_by_navigation_module(self, navigation_module_id: str) -> List[Tool]:
        """获取指定导航模块的工具"""
        # 获取导航模块
        nav_module = self.db.query(NavigationModuleModel).filter(
            NavigationModuleModel.id == navigation_module_id
        ).first()

        if not nav_module:
            return []

        # 获取工具
        models = self.db.query(AIToolModel).filter(
            AIToolModel.navigation_module_id == navigation_module_id,
            AIToolModel.visible == True
        ).order_by(AIToolModel.order).all()

        return [
            Tool(
                tool_id=m.tool_id,
                name=m.name,
                description=m.description,
                system_prompt=m.system_prompt,
                category=m.category.name if m.category else '',
                icon=m.icon,
                visible=m.visible,
                type=m.type.value,
                welcome_message=m.welcome_message,
                order=m.order,
                navigation_module_id=str(m.navigation_module_id),
                system_prompt_file=None,
                model=m.model,
                content_type=m.content_type or 'text',  # 默认为 text
                media_type=m.media_type,
                required_capability=m.required_capability or 'chat'  # 默认为 chat
            )
            for m in models
        ]

    def get_all_tools(self) -> List[Tool]:
        """获取所有工具"""
        models = self.db.query(AIToolModel).filter(
            AIToolModel.visible == True
        ).order_by(AIToolModel.order).all()

        return [
            Tool(
                tool_id=m.tool_id,
                name=m.name,
                description=m.description,
                system_prompt=m.system_prompt,
                category=m.category.name if m.category else '',
                icon=m.icon,
                visible=m.visible,
                type=m.type.value,
                welcome_message=m.welcome_message,
                order=m.order,
                navigation_module_id=str(m.navigation_module_id),
                system_prompt_file=None,
                model=m.model,
                content_type=m.content_type or 'text',  # 默认为 text
                media_type=m.media_type,
                required_capability=m.required_capability or 'chat'  # 默认为 chat
            )
            for m in models
        ]

    def get_tool_by_id(self, tool_id: str) -> Optional[Tool]:
        """根据 tool_id 获取工具"""
        m = self.db.query(AIToolModel).filter(
            AIToolModel.tool_id == tool_id
        ).first()

        if not m:
            return None

        return Tool(
            tool_id=m.tool_id,
            name=m.name,
            description=m.description,
            system_prompt=m.system_prompt,
            category=m.category.name if m.category else '',
            icon=m.icon,
            visible=m.visible,
            type=m.type.value,
            welcome_message=m.welcome_message,
            order=m.order,
            navigation_module_id=str(m.navigation_module_id),
            system_prompt_file=None,
            model=m.model,
            content_type=m.content_type or 'text',  # 默认为 text
            media_type=m.media_type,
            required_capability=m.required_capability or 'chat'  # 默认为 chat
        )

    def get_category_config(self, navigation_module_id: Optional[str] = None) -> dict:
        """获取分类配置"""
        query = self.db.query(AIToolCategoryModel)

        if navigation_module_id:
            query = query.filter(AIToolCategoryModel.navigation_module_id == navigation_module_id)

        categories = query.all()

        return {
            cat.name: {
                'order': cat.order,
                'icon': cat.icon
            }
            for cat in categories
        }