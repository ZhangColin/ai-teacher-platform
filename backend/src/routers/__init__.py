# -*- coding: utf-8 -*-
"""路由模块

将 main.py 中的路由按功能拆分到不同模块中，提高代码可维护性。
"""

from .auth import router as auth_router
from .users import router as users_router
from .tools import router as tools_router
from .sessions import router as sessions_router
from .admin_tools import router as admin_tools_router
from .works import router as works_router
from .courses import router as courses_router
from .common import router as common_router

__all__ = [
    "auth_router",
    "users_router",
    "tools_router",
    "sessions_router",
    "admin_tools_router",
    "works_router",
    "courses_router",
    "common_router",
]
