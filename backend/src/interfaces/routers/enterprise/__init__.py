# -*- coding: utf-8 -*-
"""企业后台路由"""
from fastapi import APIRouter
from . import users, points, consumptions

router = APIRouter(prefix="/api/v1/enterprise", tags=["企业后台"])
router.include_router(users.router)
router.include_router(points.router)
router.include_router(consumptions.router)
