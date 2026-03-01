# -*- coding: utf-8 -*-
"""路由模块

将 main.py 中的路由按功能拆分到不同模块中，提高代码可维护性。

注意：
- auth_router 已迁移到 src/interfaces/routers/auth/
- sessions_router 已迁移到 src/interfaces/routers/sessions/
- tools_router 已迁移到 src/interfaces/routers/tools/（2026-03-01）
"""

from .users import router as users_router
# from .tools import router as tools_router  # 已迁移到 interfaces 层（2026-03-01）
# from .sessions import router as sessions_router  # 已迁移到 interfaces 层
from .admin_tools import router as admin_tools_router
from .works import router as works_router
from .courses import router as courses_router
from .common import router as common_router

__all__ = [
    "users_router",
    # "tools_router",  # 已迁移到 interfaces 层（2026-03-01）
    # "sessions_router",  # 已迁移到 interfaces 层
    "admin_tools_router",
    "works_router",
    "courses_router",
    "common_router",
]
