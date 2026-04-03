# -*- coding: utf-8 -*-
"""模型供应商配置服务

提供模型供应商和模型配置的 CRUD 操作
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.db_models import (
    ModelProviderModel,
    ModelConfigModel
)
from src.models import (
    ModelProviderListItem,
    ModelConfigListItem,
    CreateModelProviderRequest,
    UpdateModelProviderRequest,
    CreateModelConfigRequest,
    UpdateModelConfigRequest
)
from src.services.encryption_service import EncryptionService

logger = logging.getLogger(__name__)


class ModelProviderService:
    """模型供应商配置服务"""

    def __init__(self, db: Session):
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db
        # 初始化加密服务（从环境变量读取密钥）
        self.encryption = EncryptionService()

    # ==================== 模型供应商 CRUD ====================

    def get_all_providers(self, include_disabled: bool = False) -> List[ModelProviderListItem]:
        """
        获取所有模型供应商

        Args:
            include_disabled: 是否包含已禁用的供应商

        Returns:
            供应商列表
        """
        query = self.db.query(ModelProviderModel)

        if not include_disabled:
            query = query.filter(ModelProviderModel.is_enabled == True)

        providers = query.order_by(ModelProviderModel.order).all()

        return [
            ModelProviderListItem(
                id=p.id,
                provider_code=p.provider_code,
                provider_name=p.provider_name,
                base_url=p.base_url,
                is_enabled=p.is_enabled,
                is_default=p.is_default,
                order=p.order,
                created_at=p.created_at,
                updated_at=p.updated_at
            )
            for p in providers
        ]

    def get_provider_by_id(self, provider_id: str) -> Optional[ModelProviderListItem]:
        """
        根据ID获取供应商

        Args:
            provider_id: 供应商ID

        Returns:
            供应商信息，如果不存在返回None
        """
        provider = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.id == provider_id
        ).first()

        if not provider:
            return None

        return ModelProviderListItem(
            id=provider.id,
            provider_code=provider.provider_code,
            provider_name=provider.provider_name,
            base_url=provider.base_url,
            is_enabled=provider.is_enabled,
            is_default=provider.is_default,
            order=provider.order,
            created_at=provider.created_at,
            updated_at=provider.updated_at
        )

    def get_provider_by_code(self, provider_code: str) -> Optional[ModelProviderListItem]:
        """
        根据代码获取供应商

        Args:
            provider_code: 供应商代码（如：openai, deepseek）

        Returns:
            供应商信息，如果不存在返回None
        """
        provider = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.provider_code == provider_code
        ).first()

        if not provider:
            return None

        return ModelProviderListItem(
            id=provider.id,
            provider_code=provider.provider_code,
            provider_name=provider.provider_name,
            base_url=provider.base_url,
            is_enabled=provider.is_enabled,
            is_default=provider.is_default,
            order=provider.order,
            created_at=provider.created_at,
            updated_at=provider.updated_at
        )

    def get_default_provider(self) -> Optional[ModelProviderListItem]:
        """
        获取默认供应商

        Returns:
            默认供应商信息，如果不存在返回None
        """
        provider = self.db.query(ModelProviderModel).filter(
            and_(
                ModelProviderModel.is_default == True,
                ModelProviderModel.is_enabled == True
            )
        ).first()

        if not provider:
            return None

        return ModelProviderListItem(
            id=provider.id,
            provider_code=provider.provider_code,
            provider_name=provider.provider_name,
            base_url=provider.base_url,
            is_enabled=provider.is_enabled,
            is_default=provider.is_default,
            order=provider.order,
            created_at=provider.created_at,
            updated_at=provider.updated_at
        )

    def create_provider(self, request: CreateModelProviderRequest) -> ModelProviderListItem:
        """
        创建模型供应商

        Args:
            request: 创建请求

        Returns:
            新创建的供应商信息

        Raises:
            ValueError: 供应商代码已存在
        """
        # 检查代码是否已存在
        existing = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.provider_code == request.provider_code
        ).first()

        if existing:
            raise ValueError(f"供应商代码 '{request.provider_code}' 已存在")

        # 如果设置为默认，清除其他默认标记
        if request.is_default:
            self.db.query(ModelProviderModel).filter(
                ModelProviderModel.is_default == True
            ).update({"is_default": False})

        # 加密 API Key
        api_key_encrypted = self.encryption.encrypt(request.api_key)

        # 创建供应商
        provider = ModelProviderModel(
            provider_code=request.provider_code,
            provider_name=request.provider_name,
            api_key_encrypted=api_key_encrypted,
            base_url=request.base_url,
            is_enabled=request.is_enabled,
            is_default=request.is_default,
            order=request.order
        )

        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)

        logger.info(f"创建模型供应商: {request.provider_code}")

        return ModelProviderListItem(
            id=provider.id,
            provider_code=provider.provider_code,
            provider_name=provider.provider_name,
            base_url=provider.base_url,
            is_enabled=provider.is_enabled,
            is_default=provider.is_default,
            order=provider.order,
            created_at=provider.created_at,
            updated_at=provider.updated_at
        )

    def update_provider(self, provider_id: str, request: UpdateModelProviderRequest) -> ModelProviderListItem:
        """
        更新模型供应商

        Args:
            provider_id: 供应商ID
            request: 更新请求

        Returns:
            更新后的供应商信息

        Raises:
            ValueError: 供应商不存在
        """
        provider = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.id == provider_id
        ).first()

        if not provider:
            raise ValueError(f"供应商 ID '{provider_id}' 不存在")

        # 如果设置为默认，清除其他默认标记
        if request.is_default is True and not provider.is_default:
            self.db.query(ModelProviderModel).filter(
                and_(
                    ModelProviderModel.is_default == True,
                    ModelProviderModel.id != provider_id
                )
            ).update({"is_default": False})

        # 更新字段
        if request.provider_name is not None:
            provider.provider_name = request.provider_name

        # 只有当 api_key 非空时才更新（空字符串表示不修改）
        if request.api_key:
            provider.api_key_encrypted = self.encryption.encrypt(request.api_key)

        if request.base_url is not None:
            provider.base_url = request.base_url

        if request.is_enabled is not None:
            provider.is_enabled = request.is_enabled

        if request.is_default is not None:
            provider.is_default = request.is_default

        if request.order is not None:
            provider.order = request.order

        self.db.commit()
        self.db.refresh(provider)

        logger.info(f"更新模型供应商: {provider.provider_code}")

        return ModelProviderListItem(
            id=provider.id,
            provider_code=provider.provider_code,
            provider_name=provider.provider_name,
            base_url=provider.base_url,
            is_enabled=provider.is_enabled,
            is_default=provider.is_default,
            order=provider.order,
            created_at=provider.created_at,
            updated_at=provider.updated_at
        )

    def delete_provider(self, provider_id: str) -> None:
        """
        删除模型供应商

        Args:
            provider_id: 供应商ID

        Raises:
            ValueError: 供应商不存在
        """
        provider = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.id == provider_id
        ).first()

        if not provider:
            raise ValueError(f"供应商 ID '{provider_id}' 不存在")

        provider_code = provider.provider_code

        # 级联删除会自动删除关联的模型配置
        self.db.delete(provider)
        self.db.commit()

        logger.info(f"删除模型供应商: {provider_code}")

    def get_provider_api_key(self, provider_id: str) -> str:
        """
        获取供应商的 API Key（解密后）

        Args:
            provider_id: 供应商ID

        Returns:
            解密后的 API Key

        Raises:
            ValueError: 供应商不存在
        """
        provider = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.id == provider_id
        ).first()

        if not provider:
            raise ValueError(f"供应商 ID '{provider_id}' 不存在")

        return self.encryption.decrypt(provider.api_key_encrypted)

    # ==================== 模型配置 CRUD ====================

    def get_all_models(self, provider_id: Optional[str] = None, include_disabled: bool = False, capability: Optional[str] = None) -> List[ModelConfigListItem]:
        """
        获取所有模型配置

        Args:
            provider_id: 可选的供应商ID过滤
            include_disabled: 是否包含已禁用的模型
            capability: 可选的能力过滤（如 chat、vision、image_generation 等）

        Returns:
            模型配置列表
        """
        query = self.db.query(ModelConfigModel).join(ModelProviderModel)

        if provider_id:
            query = query.filter(ModelConfigModel.provider_id == provider_id)

        # 只返回启用供应商的模型
        query = query.filter(ModelProviderModel.is_enabled == True)

        if not include_disabled:
            query = query.filter(ModelConfigModel.is_enabled == True)

        # 按能力过滤（精确匹配逗号分隔的值）
        if capability:
            # 使用 LIKE 匹配，确保是完整的能力名称
            # 匹配模式：capability 在开头、中间或结尾，用逗号分隔
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    ModelConfigModel.capabilities == capability,  # 只有一个能力
                    ModelConfigModel.capabilities.like(f'{capability},%'),  # 能力在开头
                    ModelConfigModel.capabilities.like(f'%,{capability},%'),  # 能力在中间
                    ModelConfigModel.capabilities.like(f'%,{capability}')  # 能力在结尾
                )
            )

        models = query.order_by(ModelProviderModel.order, ModelConfigModel.model_name).all()

        return [
            ModelConfigListItem(
                id=m.id,
                provider_id=m.provider_id,
                provider_code=m.provider.provider_code,
                provider_name=m.provider.provider_name,
                model_code=m.model_code,
                model_name=m.model_name,
                capabilities=m.capabilities.split(',') if m.capabilities else [],
                is_enabled=m.is_enabled,
                created_at=m.created_at,
                updated_at=m.updated_at
            )
            for m in models
        ]

    def get_model_by_id(self, model_id: str) -> Optional[ModelConfigListItem]:
        """
        根据ID获取模型配置

        Args:
            model_id: 模型配置ID

        Returns:
            模型配置信息，如果不存在返回None
        """
        model = self.db.query(ModelConfigModel).filter(
            ModelConfigModel.id == model_id
        ).first()

        if not model:
            return None

        return ModelConfigListItem(
            id=model.id,
            provider_id=model.provider_id,
            provider_code=model.provider.provider_code,
            provider_name=model.provider.provider_name,
            model_code=model.model_code,
            model_name=model.model_name,
            capabilities=model.capabilities.split(',') if model.capabilities else [],
            is_enabled=model.is_enabled,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def create_model_config(self, request: CreateModelConfigRequest) -> ModelConfigListItem:
        """
        创建模型配置

        Args:
            request: 创建请求

        Returns:
            新创建的模型配置信息

        Raises:
            ValueError: 供应商不存在或模型代码已存在
        """
        # 检查供应商是否存在
        provider = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.id == request.provider_id
        ).first()

        if not provider:
            raise ValueError(f"供应商 ID '{request.provider_id}' 不存在")

        # 检查模型代码是否已存在
        existing = self.db.query(ModelConfigModel).filter(
            and_(
                ModelConfigModel.provider_id == request.provider_id,
                ModelConfigModel.model_code == request.model_code
            )
        ).first()

        if existing:
            raise ValueError(f"模型代码 '{request.model_code}' 在该供应商下已存在")

        # 创建模型配置
        model = ModelConfigModel(
            provider_id=request.provider_id,
            model_code=request.model_code,
            model_name=request.model_name,
            capabilities=request.capabilities,
            is_enabled=request.is_enabled
        )

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        logger.info(f"创建模型配置: {provider.provider_code}:{request.model_code}")

        return ModelConfigListItem(
            id=model.id,
            provider_id=model.provider_id,
            provider_code=model.provider.provider_code,
            provider_name=model.provider.provider_name,
            model_code=model.model_code,
            model_name=model.model_name,
            capabilities=model.capabilities.split(',') if model.capabilities else [],
            is_enabled=model.is_enabled,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def update_model_config(self, model_id: str, request: UpdateModelConfigRequest) -> ModelConfigListItem:
        """
        更新模型配置

        Args:
            model_id: 模型配置ID
            request: 更新请求

        Returns:
            更新后的模型配置信息

        Raises:
            ValueError: 模型配置不存在
        """
        model = self.db.query(ModelConfigModel).filter(
            ModelConfigModel.id == model_id
        ).first()

        if not model:
            raise ValueError(f"模型配置 ID '{model_id}' 不存在")

        # 更新字段
        if request.model_code is not None:
            model.model_code = request.model_code

        if request.model_name is not None:
            model.model_name = request.model_name

        if request.capabilities is not None:
            model.capabilities = request.capabilities

        if request.is_enabled is not None:
            model.is_enabled = request.is_enabled

        self.db.commit()
        self.db.refresh(model)

        logger.info(f"更新模型配置: {model.provider.provider_code}:{model.model_code}")

        return ModelConfigListItem(
            id=model.id,
            provider_id=model.provider_id,
            provider_code=model.provider.provider_code,
            provider_name=model.provider.provider_name,
            model_code=model.model_code,
            model_name=model.model_name,
            capabilities=model.capabilities.split(',') if model.capabilities else [],
            is_enabled=model.is_enabled,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def delete_model_config(self, model_id: str) -> None:
        """
        删除模型配置

        Args:
            model_id: 模型配置ID

        Raises:
            ValueError: 模型配置不存在
        """
        model = self.db.query(ModelConfigModel).filter(
            ModelConfigModel.id == model_id
        ).first()

        if not model:
            raise ValueError(f"模型配置 ID '{model_id}' 不存在")

        model_code = model.model_code

        self.db.delete(model)
        self.db.commit()

        logger.info(f"删除模型配置: {model_code}")

    def get_model_config(self, provider_code: str, model_code: str) -> Optional[ModelConfigModel]:
        """
        获取模型配置

        Args:
            provider_code: 供应商代码（如 'deepseek', 'openai', 'kimi'）
            model_code: 模型代码（如 'deepseek-chat', 'gpt-4', 'kimi-k2.5'）

        Returns:
            ModelConfigModel 或 None
        """
        return self.db.query(ModelConfigModel).join(
            ModelProviderModel,
            ModelConfigModel.provider_id == ModelProviderModel.id
        ).filter(
            ModelProviderModel.provider_code == provider_code,
            ModelConfigModel.model_code == model_code,
            ModelConfigModel.is_enabled == True
        ).first()
