# works.py 测试提升与 require_admin 重构设计文档

**日期：** 2026-03-02
**作者：** Claude Code
**状态：** 已批准
**相关Issue：** 代码审查跟进任务

---

## 1. 概述

本设计旨在解决两个代码审查中发现的问题：
1. **works.py测试覆盖率仅31%** - 缺少集成测试
2. **require_admin函数重复** - 在works.py和courses.py中重复定义

采用**快速迭代式**方案，在一个atomic commit中完成所有改动。

### 1.1 目标

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| test_works.py测试数量 | 0 | 35+ |
| works.py测试覆盖率 | 31% | 80%+ |
| require_admin重复次数 | 2处 | 0处 |
| 总测试数量 | 805 | 840+ |

### 1.2 改动范围

- **新增：** `backend/tests/integration/routers/test_works.py`（约600行）
- **修改：** `backend/src/interfaces/dependencies.py`（+20行）
- **修改：** `backend/src/interfaces/routers/works/works.py`（-20行）
- **修改：** `backend/src/interfaces/routers/courses/courses.py`（-20行）

---

## 2. 架构设计

### 2.1 依赖注入重构

**当前状态：**
```
works.py (第42-61行)    →    require_admin定义
courses.py (第32-51行)   →    require_admin定义（重复！）
```

**重构后：**
```
interfaces/dependencies.py  →    require_admin定义（统一）
         ↓
         ↓ 导入
         ↓
works.py                   →    from dependencies import require_admin
courses.py                 →    from dependencies import require_admin
```

### 2.2 测试组织结构

```
tests/integration/routers/test_works.py
│
├── 辅助函数
│   ├── create_test_work(db, category_id)
│   ├── create_test_category(db, name)
│   └── create_test_html_file(content)
│
├── TestWorkCategoriesPublic (5个测试)
│   ├── test_get_work_categories
│   ├── test_get_work_categories_empty
│   └── ...
│
├── TestWorkDetailPublic (3个测试)
│   ├── test_get_work_detail
│   ├── test_get_work_detail_not_found
│   └── test_get_work_detail_not_visible
│
├── TestWorkManagement (20个测试)
│   ├── test_create_work_with_file
│   ├── test_create_work_file_too_large
│   ├── test_create_work_invalid_format
│   ├── test_update_work
│   ├── test_delete_work
│   ├── test_delete_work_with_file_cleanup
│   ├── test_move_work_up
│   ├── test_move_work_down
│   ├── test_toggle_visibility
│   └── ...
│
└── TestWorkCategoryManagement (10个测试)
    ├── test_create_category
    ├── test_update_category
    ├── test_delete_category
    └── ...
```

---

## 3. 详细设计

### 3.1 require_admin 重构

#### 3.1.1 在 interfaces/dependencies.py 中添加

```python
# -*- coding: utf-8 -*-
"""Interfaces layer dependency injection

This module provides dependency functions for FastAPI routes in the interfaces layer.
It bridges the new DDD structure with existing services.
"""
import sys
from pathlib import Path
from typing import Annotated

from fastapi import HTTPException, status, Depends

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.routers.dependencies import (
    get_tool_service,
    get_ai_service,
    get_session_service,
    get_artifact_parser,
    get_title_generator,
    get_auth_service,
    get_user_service,
    get_config_loader,
    get_conversion_service,
    get_common_tool_service,
    get_work_service,
    get_course_service,
)
from src.interfaces.auth import get_current_user
from src.models import UserInfo

# Export all dependencies for use in interfaces layer routes
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

#### 3.1.2 更新 works.py

**删除（第42-61行）：**
```python
async def require_admin(current_user: Annotated[UserInfo, Depends(get_current_user)]) -> UserInfo:
    """管理员权限验证（依赖注入函数）"""
    # ... (20行代码全部删除)
```

**更新导入：**
```python
# 从
from src.interfaces.auth import get_current_user
from src.interfaces.dependencies import get_work_service

# 改为
from src.interfaces.auth import get_current_user
from src.interfaces.dependencies import get_work_service, require_admin
```

#### 3.1.3 更新 courses.py

同样的修改：删除第32-51行，更新导入。

### 3.2 test_works.py 测试设计

#### 3.2.1 辅助函数

```python
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


def create_test_html_file(content: str = "<html><body>测试内容</body></html>") -> tuple:
    """创建测试HTML文件对象"""
    from fastapi.params import UploadFile
    import io

    content_bytes = content.encode("utf-8")
    filename = "test.html"
    content_type = "text/html"

    file_obj = UploadFile(
        filename=filename,
        file=io.BytesIO(content_bytes),
        headers={"content-type": content_type}
    )

    return file_obj, content_bytes, filename
```

#### 3.2.2 关键测试用例

**文件上传测试（核心场景）：**
```python
@pytest.mark.asyncio
async def test_create_work_with_file(logged_in_admin_client, db_session, tmp_path):
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
```

**权限验证测试：**
```python
@pytest.mark.asyncio
async def test_admin_work_by_non_admin(logged_in_client, db_session):
    """测试非管理员访问管理端点"""
    category_id = create_test_category(db_session)

    response = await logged_in_client.post(
        "/api/v1/admin/works",
        data={"title": "测试", "category_id": category_id}
    )

    assert response.status_code == 403
    assert "需要管理员权限" in response.json()["detail"]
```

**文件大小限制测试：**
```python
@pytest.mark.asyncio
async def test_create_work_file_too_large(logged_in_admin_client, db_session):
    """测试上传超大文件（>10MB）"""
    category_id = create_test_category(db_session)

    # 创建11MB的HTML内容
    large_html = "<html><body>" + "x" * (11 * 1024 * 1024) + "</body></html>"
    files = {"file": ("large.html", BytesIO(large_html.encode()), "text/html")}
    data = {"title": "超大文件", "category_id": category_id}

    response = await logged_in_admin_client.post("/api/v1/admin/works", files=files, data=data)

    assert response.status_code == 400
    assert "文件大小不能超过10MB" in response.json()["detail"]
```

**文件清理测试：**
```python
@pytest.mark.asyncio
async def test_delete_work_with_file_cleanup(logged_in_admin_client, db_session, tmp_path):
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
```

---

## 4. 实施计划

### Phase 1: 依赖注入重构（30分钟）

- [ ] 在`interfaces/dependencies.py`中添加`require_admin`函数
- [ ] 更新`__all__`导出列表
- [ ] 删除works.py中的`require_admin`定义（第42-61行）
- [ ] 删除courses.py中的`require_admin`定义（第32-51行）
- [ ] 更新导入语句
- [ ] 运行`pytest tests/integration/routers/test_courses.py -v`验证无回归

**验收标准：** 51个测试全部通过

### Phase 2: 创建测试套件（90分钟）

- [ ] 创建`tests/integration/routers/test_works.py`
- [ ] 实现辅助函数
- [ ] 实现TestWorkCategoriesPublic（5个测试）
- [ ] 实现TestWorkDetailPublic（3个测试）
- [ ] 实现TestWorkManagement（20个测试）
- [ ] 实现TestWorkCategoryManagement（10个测试）
- [ ] 运行`pytest tests/integration/routers/test_works.py -v`

**验收标准：** 38个测试全部通过

### Phase 3: 验证与优化（30分钟）

- [ ] 运行完整测试套件：`pytest tests/ -v`
- [ ] 检查覆盖率：`pytest --cov=src/interfaces/routers/works/works.py --cov-report=term-missing`
- [ ] 清理临时文件
- [ ] 代码格式化：`black .`

**验收标准：**
- 总测试数：840+
- works.py覆盖率：80%+
- 所有测试通过

---

## 5. 测试场景矩阵

### 5.1 作品管理端点

| 端点 | 方法 | 测试场景 | 权限 |
|------|------|---------|------|
| /works/categories | GET | 正常返回、空列表、未授权 | 用户 |
| /works/{work_id} | GET | 正常返回、不存在、不可见、未授权 | 用户 |
| /admin/works | GET | 分页、过滤、未授权、非管理员 | 管理员 |
| /admin/works | POST | 上传成功、文件过大、格式错误、权限验证 | 管理员 |
| /admin/works/{id} | PATCH | 更新成功、不存在、权限验证 | 管理员 |
| /admin/works/{id} | DELETE | 删除成功、文件清理、不存在、权限验证 | 管理员 |
| /admin/works/{id}/move-up | POST | 上移成功、已是第一位、不存在、权限验证 | 管理员 |
| /admin/works/{id}/move-down | POST | 下移成功、已是最末位、不存在、权限验证 | 管理员 |
| /admin/works/{id}/toggle-visibility | POST | 切换成功、不存在、权限验证 | 管理员 |

### 5.2 分类管理端点

| 端点 | 方法 | 测试场景 | 权限 |
|------|------|---------|------|
| /admin/work-categories | GET | 正常返回、空列表、未授权、非管理员 | 管理员 |
| /admin/work-categories | POST | 创建成功、重名、权限验证 | 管理员 |
| /admin/work-categories/{id} | PATCH | 更新成功、不存在、权限验证 | 管理员 |
| /admin/work-categories/{id} | DELETE | 删除成功、有作品时拒绝、不存在、权限验证 | 管理员 |
| /admin/work-categories/{id}/move-up | POST | 上移成功、已是第一位、不存在、权限验证 | 管理员 |
| /admin/work-categories/{id}/move-down | POST | 下移成功、已是最末位、不存在、权限验证 | 管理员 |

---

## 6. 验收标准

| 指标 | 当前值 | 目标值 | 验收命令 |
|------|--------|--------|----------|
| require_admin重复 | 2处 | 0处 | `grep -rn "def require_admin" src/interfaces/routers/` |
| test_works.py测试数 | 0 | 38 | `pytest tests/integration/routers/test_works.py --collect-only` |
| works.py覆盖率 | 31% | 80%+ | `pytest --cov=src/interfaces/routers/works/works.py` |
| 总测试数 | 805 | 843 | `pytest tests/ --collect-only` |
| 所有测试通过 | ✅ | ✅ | `pytest tests/ -v` |

---

## 7. 风险与回滚

### 7.1 风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 测试运行时间过长 | 中 | 低 | 使用pytest-xdist并行运行 |
| 文件系统权限问题 | 低 | 中 | 在CI环境中验证 |
| 覆盖率不达标 | 低 | 中 | 预留时间补充测试 |

### 7.2 回滚策略

如果测试失败或覆盖率不达标：
```bash
# 回滚到上一个commit
git reset --hard a21fbca

# 重新审查设计
# 查看失败日志
# 修复问题后重新提交
```

---

## 8. 参考资料

- 代码审查报告（2026-03-02）
- test_courses.py（参考模板）
- FastAPI测试文档：https://fastapi.tiangolo.com/tutorial/testing/
- pytest-asyncio文档：https://pytest-asyncio.readthedocs.io/

---

**审批记录：**
- 设计方案审批：✅ 2026-03-02
- 待实施

**下一步：**调用writing-plans技能创建详细实施计划
