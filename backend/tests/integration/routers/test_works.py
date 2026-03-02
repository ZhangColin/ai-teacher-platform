# -*- coding: utf-8 -*-
"""作品管理路由集成测试

测试 works.py 中的所有端点，目标覆盖率 80%+
"""
import pytest
import shutil
from io import BytesIO
from pathlib import Path
from sqlalchemy.orm import Session

from src.db_models import WorkModel, WorkCategoryModel


# ==================== 辅助函数 ====================

def create_test_work(db: Session, category_id: str, name: str = "测试作品", visible: bool = True) -> str:
    """创建测试作品"""
    work = WorkModel(
        name=name,
        description=f"{name}的描述",
        html_path=f"/fake/path/{name}.html",
        category_id=category_id,
        visible=visible,
        order=1
    )
    db.add(work)
    db.commit()
    db.refresh(work)
    return work.id


def create_test_category(db: Session, name: str = "测试分类", order: int = 1) -> str:
    """创建测试作品分类"""
    category = WorkCategoryModel(
        name=name,
        order=order
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category.id


# ==================== 用户端作品分类接口测试 ====================

class TestWorkCategoriesPublic:
    """测试用户端作品分类接口"""

    @pytest.mark.asyncio
    async def test_get_work_categories(self, logged_in_client, db_session):
        """测试获取作品分类列表"""
        # 创建测试分类和作品
        category_id = create_test_category(db_session, "分类1")
        create_test_work(db_session, category_id, "作品1", visible=True)
        create_test_work(db_session, category_id, "作品2", visible=True)

        response = await logged_in_client.get("/api/v1/works/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) == 1
        assert data["categories"][0]["name"] == "分类1"
        assert len(data["categories"][0]["works"]) == 2

    @pytest.mark.asyncio
    async def test_get_work_categories_empty(self, logged_in_client, db_session):
        """测试空分类列表"""
        response = await logged_in_client.get("/api/v1/works/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) == 0

    @pytest.mark.asyncio
    async def test_get_work_categories_unauthorized(self, async_client):
        """测试未授权访问"""
        response = await async_client.get("/api/v1/works/categories")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_work_categories_only_visible(self, logged_in_client, db_session):
        """测试只返回可见作品"""
        category_id = create_test_category(db_session)
        create_test_work(db_session, category_id, "可见作品", visible=True)
        create_test_work(db_session, category_id, "不可见作品", visible=False)

        response = await logged_in_client.get("/api/v1/works/categories")
        assert response.status_code == 200
        data = response.json()
        assert len(data["categories"][0]["works"]) == 1
        assert data["categories"][0]["works"][0]["name"] == "可见作品"

    @pytest.mark.asyncio
    async def test_get_work_categories_order(self, logged_in_client, db_session):
        """测试分类按order排序"""
        cat3_id = create_test_category(db_session, "分类3", order=3)
        cat1_id = create_test_category(db_session, "分类1", order=1)
        cat2_id = create_test_category(db_session, "分类2", order=2)

        # 为每个分类添加可见作品，确保分类会被返回
        create_test_work(db_session, cat3_id, "作品3", visible=True)
        create_test_work(db_session, cat1_id, "作品1", visible=True)
        create_test_work(db_session, cat2_id, "作品2", visible=True)

        response = await logged_in_client.get("/api/v1/works/categories")
        assert response.status_code == 200
        data = response.json()
        assert data["categories"][0]["name"] == "分类1"
        assert data["categories"][1]["name"] == "分类2"
        assert data["categories"][2]["name"] == "分类3"


# ==================== 用户端作品详情接口测试 ====================

class TestWorkDetailPublic:
    """测试用户端作品详情接口"""

    @pytest.mark.asyncio
    async def test_get_work_detail(self, logged_in_client, db_session):
        """测试获取作品详情"""
        category_id = create_test_category(db_session)
        work_id = create_test_work(db_session, category_id, "测试作品")

        response = await logged_in_client.get(f"/api/v1/works/{work_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == work_id
        assert data["name"] == "测试作品"

    @pytest.mark.asyncio
    async def test_get_work_detail_not_found(self, logged_in_client):
        """测试作品不存在"""
        response = await logged_in_client.get("/api/v1/works/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_work_detail_not_visible(self, logged_in_client, db_session):
        """测试访问不可见作品"""
        category_id = create_test_category(db_session)
        work_id = create_test_work(db_session, category_id, visible=False)

        response = await logged_in_client.get(f"/api/v1/works/{work_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_work_detail_unauthorized(self, async_client, db_session):
        """测试未授权访问"""
        category_id = create_test_category(db_session)
        work_id = create_test_work(db_session, category_id)

        response = await async_client.get(f"/api/v1/works/{work_id}")
        assert response.status_code == 401
