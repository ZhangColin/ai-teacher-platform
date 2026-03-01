# -*- coding: utf-8 -*-
"""Interfaces layer dependency injection

This module provides dependency functions for FastAPI routes in the interfaces layer.
It bridges the new DDD structure with existing services.
"""
import sys
from pathlib import Path

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
)
from src.interfaces.auth import get_current_user

# Export all dependencies for use in interfaces layer routes
__all__ = [
    "get_tool_service",
    "get_ai_service",
    "get_session_service",
    "get_artifact_parser",
    "get_title_generator",
    "get_current_user",
]
