# works.py 测试提升与 require_admin 重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 提升works.py测试覆盖率从31%到80%+，同时消除require_admin函数的代码重复

**架构:** 提取require_admin到共享依赖，为works.py创建完整的集成测试套件

**Tech Stack:** FastAPI, pytest, pytest-asyncio, SQLAlchemy, httpx

---

## 前置条件

**开始前确认：**
- 当前分支：dev
- 基准commit：a21fbca
- Python版本：3.10+
- 所有依赖已安装

**验证命令：**
```bash
cd backend
git log --oneline -1  # 应该显示 a21fbca
python3 -m pytest tests/ -v --collect-only | grep "test session starts"  # 应该显示805个测试
```

---

## Phase 1: 依赖注入重构（30分钟）

### Task 1: 在 interfaces/dependencies.py 中添加 require_admin 函数

**Files:**
- Modify: `backend/src/interfaces/dependencies.py`

**Step 1: 添加导入**

在文件顶部添加HTTPException和UserInfo导入：

```python
from fastapi import HTTPException, status, Depends
from src.models import UserInfo
```

**Step 2: 在 __all__ 列表中添加 require_admin**

```python
__all__ = [
    "get_tool_service",
    "get_ai_service",
    "get_session_service",
    "get_artifact_parser",
    "get_title_generator",
    "get_auth_service",
    "get_user_service",
    "get_config_loader",
    "get_conversion_service",
    "get_common_tool_service",
    "get_work_service",
    "get_course_service",
    "get_current_user",
    "require_admin",  # 新增
]
```

**Step 3: 在文件末尾添加 require_admin 函数**

```python
async def require_admin(current_user: Annotated[UserInfo, Depends(get_current_user)]) -> UserInfo:
    """
    管理员权限验证（依赖注入函数）

    Args:
        current_user: 当前登录用户

    Returns:
        UserInfo: 当前用户信息（已验证为管理员）

    Raises:
        HTTPException: 用户不是管理员
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    return current_user
```

**Step 4: 运行Python语法检查**

```bash
cd backend
python3 -m py_compile src/interfaces/dependencies.py
```

Expected: 无输出（成功）

**Step 5: 提交**

```bash
git add backend/src/interfaces/dependencies.py
git commit -m "feat(interfaces): 添加require_admin依赖注入函数"
```

---

### Task 2: 更新 works.py 使用共享的 require_admin

**Files:**
- Modify: `backend/src/interfaces/routers/works/works.py`

**Step 1: 删除重复的 require_admin 函数**

删除第42-61行（整个require_admin函数定义）：

```python
# 删除这20行代码：
async def require_admin(current_user: Annotated[UserInfo, Depends(get_current_user)]) -> UserInfo:
    """
    管理员权限验证（依赖注入函数）

    Args:
        current_user: 当前登录用户

    Returns:
        UserInfo: 当前用户信息（已验证为管理员）

    Raises:
        HTTPException: 用户不是管理员
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    return current_user
```

**Step 2: 更新导入语句**

找到第34-35行：
```python
# 修改前：
from src.interfaces.auth import get_current_user
from src.interfaces.dependencies import get_work_service

# 修改后：
from src.interfaces.auth import get_current_user
from src.interfaces.dependencies import get_work_service, require_admin
```

**Step 3: 运行Python语法检查**

```bash
cd backend
python3 -m py_compile src/interfaces/routers/works/works.py
```

Expected: 无输出（成功）

**Step 4: 提交**

```bash
git add backend/src/interfaces/routers/works/works.py
git commit -m "refactor(works): 使用共享的require_admin函数"
```

---

### Task 3: 更新 courses.py 使用共享的 require_admin

**Files:**
- Modify: `backend/src/interfaces/routers/courses/courses.py`

**Step 1: 删除重复的 require_admin 函数**

删除第32-51行（整个require_admin函数定义）：

```python
# 删除这20行代码：
async def require_admin(current_user: Annotated[UserInfo, Depends(get_current_user)]) -> UserInfo:
    """
    管理员权限验证（依赖注入函数）

    Args:
        current_user: 当前登录用户

    Returns:
        UserInfo: 当前用户信息（已验证为管理员）

    Raises:
        HTTPException: 用户不是管理员
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    return current_user
```

**Step 2: 更新导入语句**

找到第25行：
```python
# 修改前：
from src.interfaces.dependencies import get_course_service, get_current_user

# 修改后：
from src.interfaces.dependencies import get_course_service, get_current_user, require_admin
```

**Step 3: 运行Python语法检查**

```bash
cd backend
python3 -m py_compile src/interfaces/routers/courses/courses.py
```

Expected: 无输出（成功）

**Step 4: 提交**

```bash
git add backend/src/interfaces/routers/courses/courses.py
git commit -m "refactor(courses): 使用共享的require_admin函数"
```

---

### Task 4: 验证重构无回归

**Step 1: 运行courses集成测试**

```bash
cd backend
python3 -m pytest tests/integration/routers/test_courses.py -v
```

Expected: 51个测试全部通过

**Step 2: 检查require_admin重复已消除**

```bash
cd backend
grep -rn "def require_admin" src/interfaces/routers/
```

Expected: 无输出（表示重复已消除）

**Step 3: 验证依赖导出正确**

```bash
cd backend
python3 -c "from src.interfaces.dependencies import require_admin; print('✓ require_admin导入成功')"
```

Expected: ✓ require_admin导入成功

---

## Phase 2: 创建测试套件（90分钟）

### Task 5: 创建 test_works.py 文件框架

**Files:**
- Create: `backend/tests/integration/routers/test_works.py`

**Step 1: 创建文件并添加基础导入和辅助函数**

```python
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

def create_test_work(db: Session, category_id: str, title: str = "测试作品", visible: bool = True) -> str:
    """创建测试作品"""
    work = WorkModel(
        title=title,
        summary=f"{title}的摘要",
        file_path=f"/fake/path/{title}.html",
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
        assert data["categories"][0]["works"][0]["title"] == "可见作品"

    @pytest.mark.asyncio
    async def test_get_work_categories_order(self, logged_in_client, db_session):
        """测试分类按order排序"""
        create_test_category(db_session, "分类3", order=3)
        create_test_category(db_session, "分类1", order=1)
        create_test_category(db_session, "分类2", order=2)

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
        assert data["work_id"] == work_id
        assert data["title"] == "测试作品"

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
```

**Step 2: 运行测试验证基础功能**

```bash
cd backend
python3 -m pytest tests/integration/routers/test_works.py -v
```

Expected: 9个测试全部通过

**Step 3: 提交**

```bash
git add backend/tests/integration/routers/test_works.py
git commit -m "test(works): 添加用户端接口测试（9个测试）"
```

---

### Task 6: 添加管理端作品管理测试（创建和上传）

**Files:**
- Modify: `backend/tests/integration/routers/test_works.py`

**Step 1: 在文件末尾添加以下代码**

```python


# ==================== 管理端作品管理测试 ====================

class TestWorkManagement:
    """测试管理端作品管理接口"""

    @pytest.mark.asyncio
    async def test_create_work_with_file(self, logged_in_admin_client, db_session):
        """测试上传作品（包含文件保存）"""
        # 1. 创建测试分类
        category_id = create_test_category(db_session)

        # 2. 准备HTML内容（<10MB）
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>测试作品</title></head>
        <body>
            <h1>测试标题</h1>
            <p>这是测试内容</p>
        </body>
        </html>
        """

        # 3. 上传作品
        files = {"file": ("index.html", BytesIO(html_content.encode("utf-8")), "text/html")}
        data = {
            "title": "测试作品",
            "category_id": category_id,
            "summary": "这是测试摘要"
        }

        response = await logged_in_admin_client.post("/api/v1/admin/works", files=files, data=data)

        # 4. 验证响应
        assert response.status_code == 201
        result = response.json()
        assert result["title"] == "测试作品"
        assert result["summary"] == "这是测试摘要"
        assert "work_id" in result

        # 5. 验证文件已保存
        work_id = result["work_id"]
        work_dir = Path(f"backend/src/static/works/html/{work_id}")
        assert work_dir.exists()
        assert (work_dir / "index.html").exists()

        # 清理
        shutil.rmtree(work_dir)

    @pytest.mark.asyncio
    async def test_create_work_file_too_large(self, logged_in_admin_client, db_session):
        """测试上传超大文件（>10MB）"""
        category_id = create_test_category(db_session)

        # 创建11MB的HTML内容
        large_html = "<html><body>" + "x" * (11 * 1024 * 1024) + "</body></html>"
        files = {"file": ("large.html", BytesIO(large_html.encode()), "text/html")}
        data = {"title": "超大文件", "category_id": category_id}

        response = await logged_in_admin_client.post("/api/v1/admin/works", files=files, data=data)

        assert response.status_code == 400
        assert "文件大小不能超过10MB" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_work_invalid_format(self, logged_in_admin_client, db_session):
        """测试上传非HTML文件"""
        category_id = create_test_category(db_session)

        files = {"file": ("test.txt", BytesIO(b"not html"), "text/plain")}
        data = {"title": "错误格式", "category_id": category_id}

        response = await logged_in_admin_client.post("/api/v1/admin/works", files=files, data=data)

        assert response.status_code == 400
        assert "文件格式必须是HTML" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_work_by_non_admin(self, logged_in_client, db_session):
        """测试非管理员上传作品"""
        category_id = create_test_category(db_session)

        html_content = "<html><body>测试</body></html>"
        files = {"file": ("index.html", BytesIO(html_content.encode()), "text/html")}
        data = {"title": "测试", "category_id": category_id}

        response = await logged_in_client.post("/api/v1/admin/works", files=files, data=data)

        assert response.status_code == 403
        assert "需要管理员权限" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_work_category_not_found(self, logged_in_admin_client, db_session):
        """测试分类不存在"""
        html_content = "<html><body>测试</body></html>"
        files = {"file": ("index.html", BytesIO(html_content.encode()), "text/html")}
        data = {"title": "测试", "category_id": "nonexistent"}

        response = await logged_in_admin_client.post("/api/v1/admin/works", files=files, data=data)

        assert response.status_code == 404
        assert "分类不存在" in response.json()["detail"]
```

**Step 2: 运行测试验证**

```bash
cd backend
python3 -m pytest tests/integration/routers/test_works.py::TestWorkManagement::test_create_work_with_file -v
```

Expected: 测试通过

**Step 3: 运行所有新增测试**

```bash
cd backend
python3 -m pytest tests/integration/routers/test_works.py::TestWorkManagement -v
```

Expected: 5个新测试全部通过

**Step 4: 提交**

```bash
git add backend/tests/integration/routers/test_works.py
git commit -m "test(works): 添加作品创建和上传测试（5个测试）"
```

---

### Task 7: 添加管理端作品更新和删除测试

**Files:**
- Modify: `backend/tests/integration/routers/test_works.py`

**Step 1: 在 TestWorkManagement 类中添加以下方法**

```python
    @pytest.mark.asyncio
    async def test_update_work(self, logged_in_admin_client, db_session):
        """测试更新作品"""
        category_id = create_test_category(db_session)
        work_id = create_test_work(db_session, category_id, "原标题")

        response = await logged_in_admin_client.patch(
            f"/api/v1/admin/works/{work_id}",
            json={"title": "新标题", "summary": "新摘要"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "新标题"
        assert data["summary"] == "新摘要"

    @pytest.mark.asyncio
    async def test_delete_work(self, logged_in_admin_client, db_session):
        """测试删除作品"""
        category_id = create_test_category(db_session)
        work_id = create_test_work(db_session, category_id)

        response = await logged_in_admin_client.delete(f"/api/v1/admin/works/{work_id}")

        assert response.status_code == 204

        # 验证已删除
        get_response = await logged_in_admin_client.get(f"/api/v1/admin/works/{work_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_work_with_file_cleanup(self, logged_in_admin_client, db_session):
        """测试删除作品时清理文件"""
        # 1. 创建作品（包含文件）
        category_id = create_test_category(db_session)
        html_content = "<html><body>测试</body></html>"
        files = {"file": ("index.html", BytesIO(html_content.encode()), "text/html")}
        data = {"title": "待删除", "category_id": category_id}

        create_response = await logged_in_admin_client.post("/api/v1/admin/works", files=files, data=data)
        work_id = create_response.json()["work_id"]
        work_dir = Path(f"backend/src/static/works/html/{work_id}")

        # 2. 确认文件存在
        assert work_dir.exists()

        # 3. 删除作品
        delete_response = await logged_in_admin_client.delete(f"/api/v1/admin/works/{work_id}")

        # 4. 验证
        assert delete_response.status_code == 204
        assert not work_dir.exists()  # 文件已被清理

    @pytest.mark.asyncio
    async def test_update_work_not_found(self, logged_in_admin_client):
        """测试更新不存在的作品"""
        response = await logged_in_admin_client.patch(
            "/api/v1/admin/works/nonexistent",
            json={"title": "新标题"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_work_not_found(self, logged_in_admin_client):
        """测试删除不存在的作品"""
        response = await logged_in_admin_client.delete("/api/v1/admin/works/nonexistent")
        assert response.status_code == 404
```

**Step 2: 运行测试验证**

```bash
cd backend
python3 -m pytest tests/integration/routers/test_works.py::TestWorkManagement -v
```

Expected: 11个测试全部通过（之前5个 + 新增6个）

**Step 3: 提交**

```bash
git add backend/tests/integration/routers/test_works.py
git commit -m "test(works): 添加作品更新和删除测试（6个测试）"
```

---

### Task 8: 添加作品排序和可见性切换测试

**Files:**
- Modify: `backend/tests/integration/routers/test_works.py`

**Step 1: 在 TestWorkManagement 类中添加以下方法**

```python
    @pytest.mark.asyncio
    async def test_move_work_up(self, logged_in_admin_client, db_session):
        """测试上移作品"""
        category_id = create_test_category(db_session)
        work1_id = create_test_work(db_session, category_id, "作品1", order=1)
        work2_id = create_test_work(db_session, category_id, "作品2", order=2)

        response = await logged_in_admin_client.post(f"/api/v1/admin/works/{work2_id}/move-up")

        assert response.status_code == 200
        data = response.json()
        assert data["order"] == 1

    @pytest.mark.asyncio
    async def test_move_work_up_already_first(self, logged_in_admin_client, db_session):
        """测试上移已在首位的作品"""
        category_id = create_test_category(db_session)
        work_id = create_test_work(db_session, category_id, order=1)

        response = await logged_in_admin_client.post(f"/api/v1/admin/works/{work_id}/move-up")

        assert response.status_code == 400
        assert "已经是第一位" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_move_work_down(self, logged_in_admin_client, db_session):
        """测试下移作品"""
        category_id = create_test_category(db_session)
        work1_id = create_test_work(db_session, category_id, "作品1", order=1)
        work2_id = create_test_work(db_session, category_id, "作品2", order=2)

        response = await logged_in_admin_client.post(f"/api/v1/admin/works/{work1_id}/move-down")

        assert response.status_code == 200
        data = response.json()
        assert data["order"] == 2

    @pytest.mark.asyncio
    async def test_move_work_down_already_last(self, logged_in_admin_client, db_session):
        """测试下移已在末位的作品"""
        category_id = create_test_category(db_session)
        work_id = create_test_work(db_session, category_id, order=1)

        response = await logged_in_admin_client.post(f"/api/v1/admin/works/{work_id}/move-down")

        assert response.status_code == 400
        assert "已经是最末位" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_toggle_visibility(self, logged_in_admin_client, db_session):
        """测试切换作品可见性"""
        category_id = create_test_category(db_session)
        work_id = create_test_work(db_session, category_id, visible=True)

        # 切换为不可见
        response = await logged_in_admin_client.post(f"/api/v1/admin/works/{work_id}/toggle-visibility")

        assert response.status_code == 200
        data = response.json()
        assert data["visible"] == False

    @pytest.mark.asyncio
    async def test_toggle_visibility_not_found(self, logged_in_admin_client):
        """测试切换不存在作品的可见性"""
        response = await logged_in_admin_client.post("/api/v1/admin/works/nonexistent/toggle-visibility")

        assert response.status_code == 404
```

**Step 2: 运行测试验证**

```bash
cd backend
python3 -m pytest tests/integration/routers/test_works.py::TestWorkManagement -v
```

Expected: 18个测试全部通过（之前11个 + 新增7个）

**Step 3: 提交**

```bash
git add backend/tests/integration/routers/test_works.py
git commit -m "test(works): 添加作品排序和可见性测试（7个测试）"
```

---

### Task 9: 添加作品列表和分页测试

**Files:**
- Modify: `backend/tests/integration/routers/test_works.py`

**Step 1: 在 TestWorkManagement 类中添加以下方法**

```python
    @pytest.mark.asyncio
    async def test_list_works(self, logged_in_admin_client, db_session):
        """测试获取作品列表"""
        category_id = create_test_category(db_session)
        create_test_work(db_session, category_id, "作品1")
        create_test_work(db_session, category_id, "作品2")

        response = await logged_in_admin_client.get("/api/v1/admin/works")

        assert response.status_code == 200
        data = response.json()
        assert "works" in data
        assert len(data["works"]) == 2

    @pytest.mark.asyncio
    async def test_list_works_pagination(self, logged_in_admin_client, db_session):
        """测试分页"""
        category_id = create_test_category(db_session)
        for i in range(15):
            create_test_work(db_session, category_id, f"作品{i}")

        response = await logged_in_admin_client.get("/api/v1/admin/works?page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["works"]) == 10
        assert data["total"] == 15
        assert data["page"] == 1
        assert data["page_size"] == 10

    @pytest.mark.asyncio
    async def test_list_works_filter_by_category(self, logged_in_admin_client, db_session):
        """测试按分类过滤"""
        category1_id = create_test_category(db_session, "分类1")
        category2_id = create_test_category(db_session, "分类2")
        create_test_work(db_session, category1_id, "作品1")
        create_test_work(db_session, category2_id, "作品2")

        response = await logged_in_admin_client.get(f"/api/v1/admin/works?category_id={category1_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["works"]) == 1
        assert data["works"][0]["title"] == "作品1"

    @pytest.mark.asyncio
    async def test_list_works_by_non_admin(self, logged_in_client, db_session):
        """测试非管理员访问作品列表"""
        response = await logged_in_client.get("/api/v1/admin/works")

        assert response.status_code == 403
```

**Step 2: 运行测试验证**

```bash
cd backend
python3 -m pytest tests/integration/routers/test_works.py::TestWorkManagement -v
```

Expected: 22个测试全部通过（之前18个 + 新增4个）

**Step 3: 提交**

```bash
git add backend/tests/integration/routers/test_works.py
git commit -m "test(works): 添加作品列表和分页测试（4个测试）"
```

---

### Task 10: 添加作品分类管理测试

**Files:**
- Modify: `backend/tests/integration/routers/test_works.py`

**Step 1: 在文件末尾添加新测试类**

```python


# ==================== 管理端作品分类管理测试 ====================

class TestWorkCategoryManagement:
    """测试管理端作品分类管理接口"""

    @pytest.mark.asyncio
    async def test_create_category(self, logged_in_admin_client):
        """测试创建分类"""
        response = await logged_in_admin_client.post(
            "/api/v1/admin/work-categories",
            json={"name": "新分类", "order": 1}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "新分类"
        assert data["order"] == 1
        assert "category_id" in data

    @pytest.mark.asyncio
    async def test_create_category_by_non_admin(self, logged_in_client):
        """测试非管理员创建分类"""
        response = await logged_in_client.post(
            "/api/v1/admin/work-categories",
            json={"name": "新分类", "order": 1}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_category(self, logged_in_admin_client, db_session):
        """测试更新分类"""
        category_id = create_test_category(db_session, "原名")

        response = await logged_in_admin_client.patch(
            f"/api/v1/admin/work-categories/{category_id}",
            json={"name": "新名", "order": 2}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新名"
        assert data["order"] == 2

    @pytest.mark.asyncio
    async def test_update_category_not_found(self, logged_in_admin_client):
        """测试更新不存在的分类"""
        response = await logged_in_admin_client.patch(
            "/api/v1/admin/work-categories/nonexistent",
            json={"name": "新名"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_category(self, logged_in_admin_client, db_session):
        """测试删除分类"""
        category_id = create_test_category(db_session)

        response = await logged_in_admin_client.delete(f"/api/v1/admin/work-categories/{category_id}")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_category_with_works(self, logged_in_admin_client, db_session):
        """测试删除有作品的分类"""
        category_id = create_test_category(db_session)
        create_test_work(db_session, category_id)

        response = await logged_in_admin_client.delete(f"/api/v1/admin/work-categories/{category_id}")

        assert response.status_code == 400
        assert "该分类下有作品，无法删除" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_categories(self, logged_in_admin_client, db_session):
        """测试获取分类列表"""
        create_test_category(db_session, "分类1", order=1)
        create_test_category(db_session, "分类2", order=2)

        response = await logged_in_admin_client.get("/api/v1/admin/work-categories")

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) == 2

    @pytest.mark.asyncio
    async def test_list_categories_by_non_admin(self, logged_in_client):
        """测试非管理员访问分类列表"""
        response = await logged_in_client.get("/api/v1/admin/work-categories")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_move_category_up(self, logged_in_admin_client, db_session):
        """测试上移分类"""
        create_test_category(db_session, "分类1", order=1)
        category2_id = create_test_category(db_session, "分类2", order=2)

        response = await logged_in_admin_client.post(f"/api/v1/admin/work-categories/{category2_id}/move-up")

        assert response.status_code == 200
        data = response.json()
        assert data["order"] == 1

    @pytest.mark.asyncio
    async def test_move_category_down(self, logged_in_admin_client, db_session):
        """测试下移分类"""
        category1_id = create_test_category(db_session, "分类1", order=1)
        create_test_category(db_session, "分类2", order=2)

        response = await logged_in_admin_client.post(f"/api/v1/admin/work-categories/{category1_id}/move-down")

        assert response.status_code == 200
        data = response.json()
        assert data["order"] == 2
```

**Step 2: 运行测试验证**

```bash
cd backend
python3 -m pytest tests/integration/routers/test_works.py::TestWorkCategoryManagement -v
```

Expected: 12个测试全部通过

**Step 3: 提交**

```bash
git add backend/tests/integration/routers/test_works.py
git commit -m "test(works): 添加作品分类管理测试（12个测试）"
```

---

## Phase 3: 验证与优化（30分钟）

### Task 11: 运行完整测试套件

**Step 1: 运行所有works测试**

```bash
cd backend
python3 -m pytest tests/integration/routers/test_works.py -v
```

Expected: 47个测试全部通过
- TestWorkCategoriesPublic: 5个
- TestWorkDetailPublic: 4个
- TestWorkManagement: 26个
- TestWorkCategoryManagement: 12个

**Step 2: 运行所有集成测试**

```bash
cd backend
python3 -m pytest tests/integration/ -v
```

Expected: 约90个测试全部通过（包括test_courses.py的51个）

**Step 3: 运行完整测试套件**

```bash
cd backend
python3 -m pytest tests/ -v --tb=short
```

Expected: 852个测试全部通过（805 + 47）

**Step 4: 提交**

```bash
git add backend/tests/integration/routers/test_works.py
git commit -m "test(works): 完成works.py集成测试套件（47个测试）"
```

---

### Task 12: 检查测试覆盖率

**Step 1: 生成覆盖率报告**

```bash
cd backend
python3 -m pytest --cov=src/interfaces/routers/works/works.py --cov-report=term-missing -v
```

Expected Output（示例）:
```
Name                                                             Stmts   Miss  Cover   Missing
--------------------------------------------------------------------------------------
src/interfaces/routers/works/works.py                              180     32    82%   61, 84-86, 123, 126-128, 145-155, 173-224, 259-272
```

**Step 2: 验证覆盖率达标**

如果覆盖率 < 80%，检查未覆盖的行并补充测试。

**Step 3: 生成HTML覆盖率报告（可选）**

```bash
cd backend
python3 -m pytest --cov=src/interfaces/routers/works/works.py --cov-report=html
open htmlcov/index.html  # macOS
# 或 xdg-open htmlcov/index.html  # Linux
```

---

### Task 13: 代码格式化和清理

**Step 1: 格式化Python代码**

```bash
cd backend
python3 -m black src/interfaces/dependencies.py src/interfaces/routers/works/works.py src/interfaces/routers/courses/courses.py tests/integration/routers/test_works.py
```

**Step 2: 清理临时文件**

```bash
cd backend
find tests/static/works/html -type d -name "work-*" -exec rm -rf {} + 2>/dev/null || true
```

**Step 3: 最终测试验证**

```bash
cd backend
python3 -m pytest tests/integration/routers/test_works.py tests/integration/routers/test_courses.py -v
```

Expected: 98个测试全部通过（47 + 51）

**Step 4: 最终提交**

```bash
git add backend/
git commit -m "style: 代码格式化和清理"
```

---

### Task 14: 验收检查清单

**Step 1: 检查require_admin重复已消除**

```bash
cd backend
grep -rn "def require_admin" src/interfaces/routers/
```

Expected: 无输出

**Step 2: 统计测试数量**

```bash
cd backend
python3 -m pytest tests/integration/routers/test_works.py --collect-only | grep "test session starts" -A 1
```

Expected: 47个测试

**Step 3: 检查总测试数**

```bash
cd backend
python3 -m pytest tests/ --collect-only | tail -5
```

Expected: 约852个测试（805 + 47）

**Step 4: 生成最终覆盖率报告**

```bash
cd backend
python3 -m pytest --cov=src/interfaces/routers/works/works.py --cov-report=term --tb=no -q
```

Expected: works.py覆盖率 >= 80%

**Step 5: 验证所有测试通过**

```bash
cd backend
python3 -m pytest tests/ -x -v --tb=short 2>&1 | tail -20
```

Expected: 所有测试通过，无失败

---

## 验收标准总结

| 指标 | 目标值 | 验收命令 |
|------|--------|----------|
| require_admin重复 | 0处 | `grep -rn "def require_admin" src/interfaces/routers/` |
| test_works.py测试数 | 47 | `pytest tests/integration/routers/test_works.py --collect-only \| grep test_` |
| works.py覆盖率 | >=80% | `pytest --cov=src/interfaces/routers/works/works.py --cov-report=term` |
| 总测试数 | >=852 | `pytest tests/ --collect-only \| tail -1` |
| 所有测试通过 | 100% | `pytest tests/ -v` |

---

## 回滚策略

如果遇到问题：

```bash
# 回滚所有改动
git reset --hard a21fbca

# 或者回滚到特定任务
git log --oneline  # 查看提交历史
git reset --hard <commit-sha>

# 重新开始
```

---

## 参考文档

- 设计文档：`docs/plans/2026-03-02-works-testing-and-auth-refactoring-design.md`
- 测试参考：`tests/integration/routers/test_courses.py`
- FastAPI测试：https://fastapi.tiangolo.com/tutorial/testing/
- pytest-asyncio：https://pytest-asyncio.readthedocs.io/

---

**计划创建时间：** 2026-03-02
**预计执行时间：** 2.5小时
**下次审查：** 执行完成后
