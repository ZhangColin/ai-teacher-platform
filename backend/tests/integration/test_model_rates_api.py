# -*- coding: utf-8 -*-
"""模型汇率批量设置 API 集成测试"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_model_rates_status_as_admin(async_client, db_session):
    """测试管理员获取模型汇率状态"""
    from src.db_models import UserModel, ModelProviderModel, ModelConfigModel
    from src.services.auth_service import AuthService
    from src.models import User
    import bcrypt
    from datetime import datetime

    # 创建管理员用户
    password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin = UserModel(
        username="admin_test",
        nickname="测试管理员",
        password_hash=password_hash,
        is_admin=True,
        created_at=datetime.now()
    )
    db_session.add(admin)
    admin.enterprise_id = db_session.test_enterprise_id
    db_session.commit()
    db_session.refresh(admin)

    # 创建User实体并生成token
    user_entity = User(
        user_id=admin.user_id,
        username=admin.username,
        email=admin.email,
        password_hash=admin.password_hash
    )
    auth_service = AuthService()
    token = auth_service.generate_token(user_entity)

    # 设置认证头
    async_client.headers["Authorization"] = f"Bearer {token}"

    # 创建测试供应商
    provider = ModelProviderModel(
        provider_code="test_provider",
        provider_name="测试供应商",
        api_key_encrypted="encrypted_key_for_test",
        base_url="https://api.test.com",
        is_enabled=True,
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)

    # 创建测试模型
    model = ModelConfigModel(
        provider_id=provider.id,
        model_code="test-model",
        model_name="测试模型",
        capabilities="chat",
        is_enabled=True,
    )
    db_session.add(model)
    db_session.commit()

    response = await async_client.get("/api/v1/admin/point-rates/status")

    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) > 0

    # 验证第一个模型的数据结构
    model_item = data["models"][0]
    assert "model_config_id" in model_item
    assert "provider_code" in model_item
    assert "model_code" in model_item
    assert "rate_config" in model_item


@pytest.mark.asyncio
async def test_get_model_rates_status_without_auth(async_client):
    """测试未认证用户获取模型汇率状态"""
    response = await async_client.get("/api/v1/admin/point-rates/status")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_batch_update_rates_create(async_client, db_session):
    """测试批量创建汇率配置"""
    from src.db_models import UserModel, ModelProviderModel, ModelConfigModel
    from src.services.auth_service import AuthService
    from src.models import User
    import bcrypt
    from datetime import datetime

    # 创建管理员用户
    password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin = UserModel(
        username="admin_create",
        nickname="创建测试管理员",
        password_hash=password_hash,
        is_admin=True,
        created_at=datetime.now()
    )
    db_session.add(admin)
    admin.enterprise_id = db_session.test_enterprise_id
    db_session.commit()
    db_session.refresh(admin)

    # 创建User实体并生成token
    user_entity = User(
        user_id=admin.user_id,
        username=admin.username,
        email=admin.email,
        password_hash=admin.password_hash
    )
    auth_service = AuthService()
    token = auth_service.generate_token(user_entity)

    # 设置认证头
    async_client.headers["Authorization"] = f"Bearer {token}"

    # 创建测试供应商
    provider = ModelProviderModel(
        provider_code="test_provider_create",
        provider_name="测试供应商创建",
        api_key_encrypted="encrypted_key_for_test",
        base_url="https://api.test.com",
        is_enabled=True,
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)

    # 创建测试模型
    model = ModelConfigModel(
        provider_id=provider.id,
        model_code="test-model-create",
        model_name="测试模型创建",
        capabilities="chat",
        is_enabled=True,
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)

    response = await async_client.post(
        "/api/v1/admin/point-rates/batch-update",
        json={
            "updates": [
                {
                    "model_config_id": str(model.id),
                    "tokens_per_point_input": 2000,
                    "tokens_per_point_output": 1000,
                    "is_enabled": True
                }
            ]
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["updated"] == 1

    # 验证数据库中的记录
    from src.db_models import ModelPointRateModel
    rate = db_session.query(ModelPointRateModel).filter(
        ModelPointRateModel.model_config_id == model.id
    ).first()
    assert rate is not None
    assert rate.tokens_per_point_input == 2000
    assert rate.tokens_per_point_output == 1000
    assert rate.separate_io is True


@pytest.mark.asyncio
async def test_batch_update_rates_update(async_client, db_session):
    """测试批量更新汇率配置"""
    from src.db_models import UserModel, ModelProviderModel, ModelConfigModel, ModelPointRateModel
    from src.services.auth_service import AuthService
    from src.models import User
    import bcrypt
    from datetime import datetime

    # 创建管理员用户
    password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin = UserModel(
        username="admin_update",
        nickname="更新测试管理员",
        password_hash=password_hash,
        is_admin=True,
        created_at=datetime.now()
    )
    db_session.add(admin)
    admin.enterprise_id = db_session.test_enterprise_id
    db_session.commit()
    db_session.refresh(admin)

    # 创建User实体并生成token
    user_entity = User(
        user_id=admin.user_id,
        username=admin.username,
        email=admin.email,
        password_hash=admin.password_hash
    )
    auth_service = AuthService()
    token = auth_service.generate_token(user_entity)

    # 设置认证头
    async_client.headers["Authorization"] = f"Bearer {token}"

    # 创建测试供应商
    provider = ModelProviderModel(
        provider_code="test_provider_update",
        provider_name="测试供应商更新",
        api_key_encrypted="encrypted_key_for_test",
        base_url="https://api.test.com",
        is_enabled=True,
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)

    # 创建测试模型
    model = ModelConfigModel(
        provider_id=provider.id,
        model_code="test-model-update",
        model_name="测试模型更新",
        capabilities="chat",
        is_enabled=True,
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)

    # 先创建配置
    rate = ModelPointRateModel(
        model_config_id=model.id,
        tokens_per_point=1000,
        separate_io=True,
        tokens_per_point_input=2000,
        tokens_per_point_output=1000,
        is_enabled=True,
    )
    db_session.add(rate)
    db_session.commit()

    # 更新配置
    response = await async_client.post(
        "/api/v1/admin/point-rates/batch-update",
        json={
            "updates": [
                {
                    "model_config_id": str(model.id),
                    "tokens_per_point_input": 3000,
                    "tokens_per_point_output": 1500,
                    "is_enabled": False
                }
            ]
        }
    )

    assert response.status_code == 200

    # 验证更新
    db_session.refresh(rate)
    assert rate.tokens_per_point_input == 3000
    assert rate.tokens_per_point_output == 1500
    assert rate.is_enabled is False


@pytest.mark.asyncio
async def test_batch_update_rates_multiple_models(async_client, db_session):
    """测试批量更新多个模型的汇率配置"""
    from src.db_models import UserModel, ModelProviderModel, ModelConfigModel
    from src.services.auth_service import AuthService
    from src.models import User
    import bcrypt
    from datetime import datetime

    # 创建管理员用户
    password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin = UserModel(
        username="admin_batch",
        nickname="批量测试管理员",
        password_hash=password_hash,
        is_admin=True,
        created_at=datetime.now()
    )
    db_session.add(admin)
    admin.enterprise_id = db_session.test_enterprise_id
    db_session.commit()
    db_session.refresh(admin)

    # 创建User实体并生成token
    user_entity = User(
        user_id=admin.user_id,
        username=admin.username,
        email=admin.email,
        password_hash=admin.password_hash
    )
    auth_service = AuthService()
    token = auth_service.generate_token(user_entity)

    # 设置认证头
    async_client.headers["Authorization"] = f"Bearer {token}"

    # 创建测试供应商
    provider = ModelProviderModel(
        provider_code="test_provider_batch",
        provider_name="测试供应商批量",
        api_key_encrypted="encrypted_key_for_test",
        base_url="https://api.test.com",
        is_enabled=True,
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)

    # 创建多个测试模型
    model1 = ModelConfigModel(
        provider_id=provider.id,
        model_code="test-model-1",
        model_name="测试模型1",
        capabilities="chat",
        is_enabled=True,
    )
    model2 = ModelConfigModel(
        provider_id=provider.id,
        model_code="test-model-2",
        model_name="测试模型2",
        capabilities="chat",
        is_enabled=True,
    )
    db_session.add(model1)
    db_session.add(model2)
    db_session.commit()
    db_session.refresh(model1)
    db_session.refresh(model2)

    response = await async_client.post(
        "/api/v1/admin/point-rates/batch-update",
        json={
            "updates": [
                {
                    "model_config_id": str(model1.id),
                    "tokens_per_point_input": 2000,
                    "tokens_per_point_output": 1000,
                    "is_enabled": True
                },
                {
                    "model_config_id": str(model2.id),
                    "tokens_per_point_input": 3000,
                    "tokens_per_point_output": 1500,
                    "is_enabled": False
                }
            ]
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["updated"] == 2

    # 验证数据库中的记录
    from src.db_models import ModelPointRateModel
    rate1 = db_session.query(ModelPointRateModel).filter(
        ModelPointRateModel.model_config_id == model1.id
    ).first()
    rate2 = db_session.query(ModelPointRateModel).filter(
        ModelPointRateModel.model_config_id == model2.id
    ).first()

    assert rate1 is not None
    assert rate1.tokens_per_point_input == 2000
    assert rate1.tokens_per_point_output == 1000
    assert rate1.is_enabled is True

    assert rate2 is not None
    assert rate2.tokens_per_point_input == 3000
    assert rate2.tokens_per_point_output == 1500
    assert rate2.is_enabled is False
