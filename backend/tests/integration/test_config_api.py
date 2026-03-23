# -*- coding: utf-8 -*-
"""配置管理 API 集成测试

测试导航模块和AI工具的管理接口
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_navigation_modules_as_admin(async_client, db_session):
    """测试管理员获取导航模块列表"""
    from src.db_models import UserModel, NavigationModuleModel, NavigationModuleType
    from src.services.auth_service import AuthService
    from src.models import User
    import bcrypt
    from datetime import datetime
    import uuid

    # 创建管理员用户
    password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin_user = UserModel(
        username="admin_test",
        email="admin@test.com",
        password_hash=password_hash,
        is_admin=True,
        created_at=datetime.now()
    )
    db_session.add(admin_user)
    admin_user.enterprise_id = db_session.test_enterprise_id
    db_session.commit()
    db_session.refresh(admin_user)

    # 创建User实体并生成token
    user_entity = User(
        user_id=admin_user.user_id,
        username=admin_user.username,
        email=admin_user.email,
        password_hash=admin_user.password_hash
    )
    auth_service = AuthService()
    token = auth_service.generate_token(user_entity)

    # 设置认证头
    async_client.headers["Authorization"] = f"Bearer {token}"

    # 创建测试导航模块
    module1 = NavigationModuleModel(
        id=str(uuid.uuid4()),
        name="AI工具",
        type=NavigationModuleType.ai_tools,
        config_source="ai_tools",
        page_path=None,
        icon="sparkles",
        order=1
    )
    module2 = NavigationModuleModel(
        id=str(uuid.uuid4()),
        name="教案管理",
        type=NavigationModuleType.page,
        config_source=None,
        page_path="/works",
        icon="document-text",
        order=2
    )
    db_session.add(module1)
    db_session.add(module2)
    module2.enterprise_id = db_session.test_enterprise_id
    db_session.commit()

    # 获取导航模块列表
    response = await async_client.get("/api/v1/admin/navigation-modules")

    assert response.status_code == 200, f"期望200，实际{response.status_code}，响应: {response.text}"

    data = response.json()
    assert "modules" in data
    assert len(data["modules"]) == 2
    assert data["modules"][0]["name"] == "AI工具"
    assert data["modules"][1]["name"] == "教案管理"


@pytest.mark.asyncio
async def test_get_navigation_modules_without_auth(async_client):
    """测试未认证用户获取导航模块列表"""
    response = await async_client.get("/api/v1/admin/navigation-modules")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_navigation_modules_as_regular_user(async_client, db_session):
    """测试普通用户获取导航模块列表（应该失败）"""
    from src.db_models import UserModel
    import bcrypt
    from datetime import datetime

    # 创建普通用户
    password_hash = bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = UserModel(
        username="regular_user",
        email="user@test.com",
        password_hash=password_hash,
        is_admin=False,
        created_at=datetime.now()
    )
    db_session.add(user)
    user.enterprise_id = db_session.test_enterprise_id
    db_session.commit()
    db_session.refresh(user)

    # 登录获取token
    response = await async_client.post("/api/v1/auth/login", json={
        "account": "regular_user",
        "password": "user123"
    })
    assert response.status_code == 200
    token = response.json()["token"]

    # 设置认证头
    async_client.headers["Authorization"] = f"Bearer {token}"

    # 尝试获取导航模块列表
    response = await async_client.get("/api/v1/admin/navigation-modules")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_navigation_module(async_client, db_session):
    """测试创建导航模块"""
    from src.db_models import UserModel
    from src.services.auth_service import AuthService
    from src.models import User
    import bcrypt
    from datetime import datetime

    # 创建管理员用户
    password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin_user = UserModel(
        username="admin_create",
        email="admin_create@test.com",
        password_hash=password_hash,
        is_admin=True,
        created_at=datetime.now()
    )
    db_session.add(admin_user)
    admin_user.enterprise_id = db_session.test_enterprise_id
    db_session.commit()
    db_session.refresh(admin_user)

    # 创建User实体并生成token
    user_entity = User(
        user_id=admin_user.user_id,
        username=admin_user.username,
        email=admin_user.email,
        password_hash=admin_user.password_hash
    )
    auth_service = AuthService()
    token = auth_service.generate_token(user_entity)

    # 设置认证头
    async_client.headers["Authorization"] = f"Bearer {token}"

    # 创建导航模块
    module_data = {
        "name": "新模块",
        "type": "page",
        "page_path": "/new-page",
        "icon": "star",
        "order": 3
    }
    response = await async_client.post("/api/v1/admin/navigation-modules", json=module_data)

    assert response.status_code == 201, f"期望201，实际{response.status_code}，响应: {response.text}"

    data = response.json()
    assert "module" in data
    assert data["module"]["name"] == "新模块"
    assert data["module"]["type"] == "page"
    assert data["module"]["page_path"] == "/new-page"


@pytest.mark.asyncio
async def test_create_navigation_module_duplicate_name(async_client, db_session):
    """测试创建重复名称的导航模块"""
    from src.db_models import UserModel, NavigationModuleModel, NavigationModuleType
    from src.services.auth_service import AuthService
    from src.models import User
    import bcrypt
    from datetime import datetime
    import uuid

    # 创建管理员用户
    password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin_user = UserModel(
        username="admin_dup",
        email="admin_dup@test.com",
        password_hash=password_hash,
        is_admin=True,
        created_at=datetime.now()
    )
    db_session.add(admin_user)
    admin_user.enterprise_id = db_session.test_enterprise_id
    db_session.commit()
    db_session.refresh(admin_user)

    # 创建User实体并生成token
    user_entity = User(
        user_id=admin_user.user_id,
        username=admin_user.username,
        email=admin_user.email,
        password_hash=admin_user.password_hash
    )
    auth_service = AuthService()
    token = auth_service.generate_token(user_entity)

    # 设置认证头
    async_client.headers["Authorization"] = f"Bearer {token}"

    # 创建已存在的模块
    existing_module = NavigationModuleModel(
        id=str(uuid.uuid4()),
        name="重复名称",
        type=NavigationModuleType.page,
        config_source=None,
        page_path="/existing",
        icon="document",
        order=1
    )
    db_session.add(existing_module)
    existing_module.enterprise_id = db_session.test_enterprise_id
    db_session.commit()

    # 尝试创建同名模块
    module_data = {
        "name": "重复名称",
        "type": "page",
        "page_path": "/new",
        "icon": "star",
        "order": 2
    }
    response = await async_client.post("/api/v1/admin/navigation-modules", json=module_data)

    assert response.status_code == 409
    assert "已存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_ai_tools_as_admin(async_client, db_session):
    """测试管理员获取AI工具列表"""
    from src.db_models import UserModel, NavigationModuleModel, NavigationModuleType, AIToolModel, AIToolCategoryModel, AIToolType
    from src.services.auth_service import AuthService
    from src.models import User
    import bcrypt
    from datetime import datetime
    import uuid

    # 创建管理员用户
    password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin_user = UserModel(
        username="admin_tools",
        email="admin_tools@test.com",
        password_hash=password_hash,
        is_admin=True,
        created_at=datetime.now()
    )
    db_session.add(admin_user)
    admin_user.enterprise_id = db_session.test_enterprise_id
    db_session.commit()
    db_session.refresh(admin_user)

    # 创建User实体并生成token
    user_entity = User(
        user_id=admin_user.user_id,
        username=admin_user.username,
        email=admin_user.email,
        password_hash=admin_user.password_hash
    )
    auth_service = AuthService()
    token = auth_service.generate_token(user_entity)

    # 设置认证头
    async_client.headers["Authorization"] = f"Bearer {token}"

    # 创建测试数据
    nav_module = NavigationModuleModel(
        id=str(uuid.uuid4()),
        name="测试工具集",
        type=NavigationModuleType.ai_tools,
        config_source="test_tools",
        order=1
    )
    db_session.add(nav_module)
    db_session.flush()

    category = AIToolCategoryModel(
        id=str(uuid.uuid4()),
        navigation_module_id=nav_module.id,
        name="测试分类",
        icon="test-icon",
        order=1
    )
    db_session.add(category)
    db_session.flush()

    tool1 = AIToolModel(
        id=str(uuid.uuid4()),
        tool_id="tool1",
        navigation_module_id=nav_module.id,
        category_id=category.id,
        name="工具1",
        description="测试工具1",
        system_prompt="你是一个测试助手",
        icon="sparkles",
        type=AIToolType.normal,
        content_type="text",
        media_type=None,
        model="deepseek:deepseek-chat",
        welcome_message="欢迎使用",
        visible=True,
        order=1
    )
    tool2 = AIToolModel(
        id=str(uuid.uuid4()),
        tool_id="tool2",
        navigation_module_id=nav_module.id,
        category_id=category.id,
        name="工具2",
        description="测试工具2",
        system_prompt="你是一个测试助手2",
        icon="star",
        type=AIToolType.normal,
        content_type="text",
        media_type=None,
        model="deepseek:deepseek-chat",
        welcome_message="欢迎使用2",
        visible=False,
        order=2
    )
    db_session.add(tool1)
    db_session.add(tool2)
    tool2.enterprise_id = db_session.test_enterprise_id
    db_session.commit()

    # 获取所有工具
    response = await async_client.get("/api/v1/admin/ai-tools")

    assert response.status_code == 200, f"期望200，实际{response.status_code}，响应: {response.text}"

    data = response.json()
    assert "tools" in data
    assert "total" in data
    assert data["total"] == 2
    assert len(data["tools"]) == 2


@pytest.mark.asyncio
async def test_get_ai_tools_with_filters(async_client, db_session):
    """测试带过滤条件的AI工具列表"""
    from src.db_models import UserModel, NavigationModuleModel, NavigationModuleType, AIToolModel, AIToolCategoryModel, AIToolType
    from src.services.auth_service import AuthService
    from src.models import User
    import bcrypt
    from datetime import datetime
    import uuid

    # 创建管理员用户
    password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin_user = UserModel(
        username="admin_filter",
        email="admin_filter@test.com",
        password_hash=password_hash,
        is_admin=True,
        created_at=datetime.now()
    )
    db_session.add(admin_user)
    admin_user.enterprise_id = db_session.test_enterprise_id
    db_session.commit()
    db_session.refresh(admin_user)

    # 创建User实体并生成token
    user_entity = User(
        user_id=admin_user.user_id,
        username=admin_user.username,
        email=admin_user.email,
        password_hash=admin_user.password_hash
    )
    auth_service = AuthService()
    token = auth_service.generate_token(user_entity)

    # 设置认证头
    async_client.headers["Authorization"] = f"Bearer {token}"

    # 创建测试数据
    nav_module = NavigationModuleModel(
        id=str(uuid.uuid4()),
        name="过滤测试工具集",
        type=NavigationModuleType.ai_tools,
        config_source="filter_tools",
        order=1
    )
    db_session.add(nav_module)
    db_session.flush()

    category = AIToolCategoryModel(
        id=str(uuid.uuid4()),
        navigation_module_id=nav_module.id,
        name="过滤分类",
        icon="filter",
        order=1
    )
    db_session.add(category)
    db_session.flush()

    tool1 = AIToolModel(
        id=str(uuid.uuid4()),
        tool_id="visible_tool",
        navigation_module_id=nav_module.id,
        category_id=category.id,
        name="可见工具",
        description="可见工具描述",
        system_prompt="你是一个助手",
        icon="eye",
        type=AIToolType.normal,
        content_type="text",
        media_type=None,
        model="deepseek:deepseek-chat",
        welcome_message="欢迎",
        visible=True,
        order=1
    )
    tool2 = AIToolModel(
        id=str(uuid.uuid4()),
        tool_id="hidden_tool",
        navigation_module_id=nav_module.id,
        category_id=category.id,
        name="隐藏工具",
        description="隐藏工具描述",
        system_prompt="你是一个隐藏助手",
        icon="eye-off",
        type=AIToolType.normal,
        content_type="text",
        media_type=None,
        model="deepseek:deepseek-chat",
        welcome_message="隐藏欢迎",
        visible=False,
        order=2
    )
    db_session.add(tool1)
    db_session.add(tool2)
    tool2.enterprise_id = db_session.test_enterprise_id
    db_session.commit()

    # 测试只获取可见工具
    response = await async_client.get("/api/v1/admin/ai-tools?visible=true")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["tools"][0]["tool_id"] == "visible_tool"

    # 测试只获取隐藏工具
    response = await async_client.get("/api/v1/admin/ai-tools?visible=false")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["tools"][0]["tool_id"] == "hidden_tool"


@pytest.mark.asyncio
async def test_get_ai_tools_without_auth(async_client):
    """测试未认证用户获取AI工具列表"""
    response = await async_client.get("/api/v1/admin/ai-tools")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_ai_tool(async_client, db_session):
    """测试创建AI工具"""
    from src.db_models import UserModel, NavigationModuleModel, NavigationModuleType, AIToolCategoryModel
    from src.services.auth_service import AuthService
    from src.models import User
    import bcrypt
    from datetime import datetime
    import uuid

    # 创建管理员用户
    password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin_user = UserModel(
        username="admin_create_tool",
        email="admin_create_tool@test.com",
        password_hash=password_hash,
        is_admin=True,
        created_at=datetime.now()
    )
    db_session.add(admin_user)
    admin_user.enterprise_id = db_session.test_enterprise_id
    db_session.commit()
    db_session.refresh(admin_user)

    # 创建User实体并生成token
    user_entity = User(
        user_id=admin_user.user_id,
        username=admin_user.username,
        email=admin_user.email,
        password_hash=admin_user.password_hash
    )
    auth_service = AuthService()
    token = auth_service.generate_token(user_entity)

    # 设置认证头
    async_client.headers["Authorization"] = f"Bearer {token}"

    # 创建测试导航模块和分类
    nav_module = NavigationModuleModel(
        id=str(uuid.uuid4()),
        name="创建测试工具集",
        type=NavigationModuleType.ai_tools,
        config_source="create_test_tools",
        order=1
    )
    db_session.add(nav_module)
    db_session.flush()

    category = AIToolCategoryModel(
        id=str(uuid.uuid4()),
        navigation_module_id=nav_module.id,
        name="创建测试分类",
        icon="plus",
        order=1
    )
    db_session.add(category)
    category.enterprise_id = db_session.test_enterprise_id
    db_session.commit()

    # 创建AI工具
    tool_data = {
        "tool_id": "new_tool",
        "navigation_module_id": str(nav_module.id),
        "category_id": str(category.id),
        "name": "新工具",
        "description": "这是一个新工具",
        "system_prompt": "你是一个新工具助手",
        "icon": "plus-circle",
        "type": "normal",
        "content_type": "text",
        "media_type": None,
        "model": "deepseek:deepseek-chat",
        "welcome_message": "欢迎使用新工具",
        "visible": True,
        "order": 1
    }
    response = await async_client.post("/api/v1/admin/ai-tools", json=tool_data)

    assert response.status_code == 201, f"期望201，实际{response.status_code}，响应: {response.text}"

    data = response.json()
    assert "tool" in data
    assert data["tool"]["tool_id"] == "new_tool"
    assert data["tool"]["name"] == "新工具"


@pytest.mark.asyncio
async def test_backward_compatibility_tools_api(async_client, db_session):
    """测试向后兼容：现有的 /api/v1/tools API 仍然工作"""
    from src.db_models import UserModel
    import bcrypt
    from datetime import datetime

    # 创建普通用户
    password_hash = bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = UserModel(
        username="compat_user",
        email="compat@test.com",
        password_hash=password_hash,
        is_admin=False,
        created_at=datetime.now()
    )
    db_session.add(user)
    user.enterprise_id = db_session.test_enterprise_id
    db_session.commit()
    db_session.refresh(user)

    # 登录获取token
    response = await async_client.post("/api/v1/auth/login", json={
        "account": "compat_user",
        "password": "user123"
    })
    assert response.status_code == 200
    token = response.json()["token"]

    # 设置认证头
    async_client.headers["Authorization"] = f"Bearer {token}"

    # 获取工具列表（使用现有API）
    response = await async_client.get("/api/v1/tools")

    assert response.status_code == 200, f"期望200，实际{response.status_code}，响应: {response.text}"

    data = response.json()
    assert "categories" in data


@pytest.mark.asyncio
async def test_backward_compatibility_navigation_api(async_client, db_session):
    """测试向后兼容：现有的 /api/v1/navigation API 仍然工作"""
    from src.db_models import UserModel
    import bcrypt
    from datetime import datetime

    # 创建普通用户
    password_hash = bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = UserModel(
        username="compat_nav_user",
        email="compat_nav@test.com",
        password_hash=password_hash,
        is_admin=False,
        created_at=datetime.now()
    )
    db_session.add(user)
    user.enterprise_id = db_session.test_enterprise_id
    db_session.commit()
    db_session.refresh(user)

    # 登录获取token
    response = await async_client.post("/api/v1/auth/login", json={
        "account": "compat_nav_user",
        "password": "user123"
    })
    assert response.status_code == 200
    token = response.json()["token"]

    # 设置认证头
    async_client.headers["Authorization"] = f"Bearer {token}"

    # 获取导航配置（使用现有API）
    response = await async_client.get("/api/v1/navigation")

    assert response.status_code == 200, f"期望200，实际{response.status_code}，响应: {response.text}"

    data = response.json()
    assert "modules" in data
