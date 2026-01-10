"""作品展示服务：管理作品和分类数据"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import asc
from ..database import SessionLocal
from ..db_models import WorkCategoryModel, WorkModel
from ..models import (
    WorkCategory, Work, WorkListItem, 
    WorkCategoryGroup, WorkCategoryResponse, WorkDetail
)


class WorkService:
    """作品展示服务类"""
    
    def __init__(self):
        """初始化作品展示服务"""
        pass
    
    def _get_db(self):
        """获取数据库会话（生成器）"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def get_categories_with_works(self) -> WorkCategoryResponse:
        """
        获取所有作品分类及其下的作品列表
        
        Returns:
            WorkCategoryResponse: 分类列表响应，包含每个分类及其作品
            
        Notes:
            - 只返回 visible=True 的作品
            - 分类按 order 字段升序排列
            - 每个分类下的作品按 order 字段升序排列
            - 如果某个分类下没有可见作品，则不返回该分类
        """
        db_gen = self._get_db()
        db = next(db_gen)
        try:
            # 查询所有分类（按order排序）
            categories = db.query(WorkCategoryModel).order_by(asc(WorkCategoryModel.order)).all()
            
            # 构建分类组列表
            category_groups = []
            
            for category in categories:
                # 查询该分类下的可见作品（按order排序）
                works = db.query(WorkModel).filter(
                    WorkModel.category_id == category.id,
                    WorkModel.visible == True
                ).order_by(asc(WorkModel.order)).all()
                
                # 只有该分类下有可见作品时，才添加到结果中
                if works:
                    work_items = [
                        WorkListItem(
                            id=work.id,
                            name=work.name,
                            description=work.description,
                            icon=work.icon,
                            order=work.order
                        )
                        for work in works
                    ]
                    
                    category_groups.append(
                        WorkCategoryGroup(
                            id=category.id,
                            name=category.name,
                            icon=category.icon,
                            order=category.order,
                            works=work_items
                        )
                    )
            
            return WorkCategoryResponse(categories=category_groups)
            
        finally:
            next(db_gen, None)
    
    def get_work_detail(self, work_id: str) -> Optional[WorkDetail]:
        """
        获取作品详情
        
        Args:
            work_id: 作品ID
            
        Returns:
            WorkDetail: 作品详情，如果作品不存在或不可见则返回None
            
        Notes:
            - 只能查询 visible=True 的作品
            - html_path 会被转换为完整的访问URL
        """
        db_gen = self._get_db()
        db = next(db_gen)
        try:
            # 查询作品及其分类
            work = db.query(WorkModel).filter(
                WorkModel.id == work_id,
                WorkModel.visible == True
            ).first()
            
            if not work:
                return None
            
            # 获取分类信息
            category = db.query(WorkCategoryModel).filter(
                WorkCategoryModel.id == work.category_id
            ).first()
            
            # 生成HTML访问URL
            html_url = f"/static/{work.html_path}"
            
            # 构建响应
            return WorkDetail(
                id=work.id,
                name=work.name,
                description=work.description,
                category_id=work.category_id,
                category_name=category.name if category else "",
                icon=work.icon,
                order=work.order,
                html_url=html_url,
                created_at=work.created_at
            )
            
        finally:
            next(db_gen, None)
