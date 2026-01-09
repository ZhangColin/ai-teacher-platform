"""常用工具服务：管理常用工具和分类数据"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import asc
from ..database import SessionLocal
from ..db_models import ToolCategoryModel, CommonToolModel
from ..models import (
    ToolCategory, CommonTool, CommonToolListItem, 
    ToolCategoryGroup, CommonToolCategoryResponse, CommonToolDetail
)


class CommonToolService:
    """常用工具服务类"""
    
    def __init__(self):
        """初始化常用工具服务"""
        pass
    
    def _get_db(self):
        """获取数据库会话（生成器）"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def get_categories_with_tools(self) -> CommonToolCategoryResponse:
        """
        获取所有工具分类及其下的工具列表
        
        Returns:
            CommonToolCategoryResponse: 分类列表响应，包含每个分类及其工具
            
        Notes:
            - 只返回 visible=True 的工具
            - 分类按 order 字段升序排列
            - 每个分类下的工具按 order 字段升序排列
            - 如果某个分类下没有可见工具，则不返回该分类
        """
        db_gen = self._get_db()
        db = next(db_gen)
        try:
            # 查询所有分类（按order排序）
            categories = db.query(ToolCategoryModel).order_by(asc(ToolCategoryModel.order)).all()
            
            # 构建分类组列表
            category_groups = []
            
            for category in categories:
                # 查询该分类下的可见工具（按order排序）
                tools = db.query(CommonToolModel).filter(
                    CommonToolModel.category_id == category.id,
                    CommonToolModel.visible == True
                ).order_by(asc(CommonToolModel.order)).all()
                
                # 只有该分类下有可见工具时，才添加到结果中
                if tools:
                    tool_items = [
                        CommonToolListItem(
                            id=tool.id,
                            name=tool.name,
                            description=tool.description,
                            type=tool.type.value,  # Enum转字符串
                            icon=tool.icon,
                            order=tool.order
                        )
                        for tool in tools
                    ]
                    
                    category_groups.append(
                        ToolCategoryGroup(
                            id=category.id,
                            name=category.name,
                            icon=category.icon,
                            order=category.order,
                            tools=tool_items
                        )
                    )
            
            return CommonToolCategoryResponse(categories=category_groups)
            
        finally:
            next(db_gen, None)
    
    def get_tool_detail(self, tool_id: str) -> Optional[CommonToolDetail]:
        """
        获取工具详情
        
        Args:
            tool_id: 工具ID
            
        Returns:
            CommonToolDetail: 工具详情，如果工具不存在或不可见则返回None
            
        Notes:
            - 只能查询 visible=True 的工具
            - HTML工具的 html_path 会被转换为完整的访问URL
        """
        db_gen = self._get_db()
        db = next(db_gen)
        try:
            # 查询工具及其分类
            tool = db.query(CommonToolModel).filter(
                CommonToolModel.id == tool_id,
                CommonToolModel.visible == True
            ).first()
            
            if not tool:
                return None
            
            # 获取分类信息
            category = db.query(ToolCategoryModel).filter(
                ToolCategoryModel.id == tool.category_id
            ).first()
            
            # 生成HTML访问URL（如果是HTML工具）
            html_url = None
            if tool.type.value == "html" and tool.html_path:
                html_url = f"/static/{tool.html_path}"
            
            return CommonToolDetail(
                id=tool.id,
                name=tool.name,
                description=tool.description,
                category_id=tool.category_id,
                category_name=category.name if category else "未分类",
                type=tool.type.value,  # Enum转字符串
                icon=tool.icon,
                order=tool.order,
                html_url=html_url,
                created_at=tool.created_at
            )
            
        finally:
            next(db_gen, None)
