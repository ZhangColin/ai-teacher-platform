# 模型供应商配置管理系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标:** 实现类似 Dify 的模型供应商配置管理系统，管理员通过后台配置 AI 模型供应商和模型，而不是依赖环境变量

**架构:** 采用"预定义 + 启用"模式 - 系统内置支持的供应商和模型列表，管理员配置 API Key 后才能使用；模型声明支持的能力（chat/image/audio/video），工具根据需要的能力选择模型

**技术栈:** FastAPI, SQLAlchemy, Vue 3, Element Plus, TypeScript

---

## Task 1: 创建数据库迁移文件

**Files:**
- Create: `backend/alembic/versions/xxx_add_model_providers.py` (文件名由 alembic 自动生成)

- [ ] **Step 1: 生成新的 Alembic 迁移文件**

```bash
cd backend && alembic revision -m "add_model_providers"
```

Expected: 生成新的迁移文件，文件名包含时间戳

- [ ] **Step 2: 编辑生成的迁移文件，添加表定义**

```python
# backend/alembic/versions/xxx_add_model_providers.py (使用实际生成的文件名)

from alembic import op
import sqlalchemy as sa

revision = '001'  # 替换为实际 revision id
down_revision = None  # 替换为实际父 revision id

def upgrade():
    # 创建 model_providers 表
    op.create_table(
        'model_providers',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('provider_code', sa.String(50), nullable=False, unique=True, comment='供应商代码（内置）'),
        sa.Column('provider_name', sa.String(100), nullable=False, comment='供应商名称'),
        sa.Column('api_key_encrypted', sa.Text(), nullable=False, comment='加密后的API密钥'),
        sa.Column('base_url', sa.String(500), nullable=True, comment='API地址'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True, comment='是否启用'),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False, comment='是否为默认供应商'),
        sa.Column('order', sa.Integer(), nullable=False, default=0, comment='排序顺序'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Index('idx_provider_code', 'provider_code'),
        sa.Index('idx_order', 'order')
    )

    # 创建 model_configs 表
    op.create_table(
        'model_configs',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('provider_id', sa.CHAR(36), nullable=False, comment='关联供应商'),
        sa.Column('model_code', sa.String(50), nullable=False, comment='模型代码（内置）'),
        sa.Column('model_name', sa.String(100), nullable=False, comment='模型名称'),
        sa.Column('capabilities', sa.String(50), nullable=False, comment='支持的能力，逗号分隔'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True, comment='是否启用'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['provider_id'], ['model_providers.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('provider_id', 'model_code', name='uk_provider_model'),
        sa.Index('idx_capabilities', 'capabilities')
    )

def downgrade():
    op.drop_table('model_configs')
    op.drop_table('model_providers')
```

- [ ] **Step 3: 运行迁移**

```bash
cd backend && alembic upgrade head
```

Expected: 表创建成功

- [ ] **Step 4: 验证表已创建**

```bash
mysql -u root -p ai_teacher_db -e "SHOW TABLES LIKE 'model_%';"
```

Expected: 显示 `model_configs`, `model_providers` 两张表

- [ ] **Step 5: 提交迁移**

```bash
git add backend/alembic/versions/xxx_add_model_providers.py
git commit -m "feat: 添加模型供应商配置数据库表"
```

---

## Task 2: 添加 ORM 数据模型

**Files:**
- Modify: `backend/src/db_models.py`

- [ ] **Step 1: 在 db_models.py 末尾添加 ORM 模型**

```python
# backend/src/db_models.py - 在文件末尾添加

class ModelProviderModel(Base):
    """模型供应商配置数据库模型"""
    __tablename__ = "model_providers"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_code = Column(String(50), unique=True, nullable=False, index=True, comment='供应商代码')
    provider_name = Column(String(100), nullable=False, comment='供应商名称')
    api_key_encrypted = Column(Text, nullable=False, comment='加密后的API密钥')
    base_url = Column(String(500), nullable=True, comment='API地址')
    is_enabled = Column(Boolean, nullable=False, default=True, comment='是否启用')
    is_default = Column(Boolean, nullable=False, default=False, comment='是否为默认供应商')
    order = Column(Integer, nullable=False, default=0, index=True, comment='排序')
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    models = relationship("ModelConfigModel", back_populates="provider", cascade="all, delete-orphan")


class ModelConfigModel(Base):
    """模型配置数据库模型"""
    __tablename__ = "model_configs"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(CHAR(36), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    model_code = Column(String(50), nullable=False, comment='模型代码')
    model_name = Column(String(100), nullable=False, comment='模型名称')
    capabilities = Column(String(50), nullable=False, comment='支持的能力，逗号分隔')
    is_enabled = Column(Boolean, nullable=False, default=True, comment='是否启用')
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    provider = relationship("ModelProviderModel", back_populates="models")

    # 联合唯一约束
    __table_args__ = (
        Index("uk_provider_model", "provider_id", "model_code", unique=True),
    )
```

- [ ] **Step 2: 运行测试验证模型导入正常**

```bash
cd backend && python3 -c "from src.db_models import ModelProviderModel, ModelConfigModel; print('Import success')"
```

Expected: `Import success`

- [ ] **Step 3: 提交**

```bash
git add backend/src/db_models.py
git commit -m "feat: 添加模型供应商配置 ORM 模型"
```

---

## Task 3: 创建内置模型定义

**Files:**
- Create: `backend/src/services/builtin_models.py`
- Create: `backend/tests/unit/test_builtin_models.py`

- [ ] **Step 1: 创建 builtin_models.py**

```python
# backend/src/services/builtin_models.py
"""内置支持的模型供应商和模型定义"""

# 内置供应商定义
BUILTIN_PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "default_base_url": "https://api.deepseek.com",
        "description": "DeepSeek AI 模型"
    },
    "openai": {
        "name": "OpenAI",
        "default_base_url": "https://api.openai.com/v1",
        "description": "OpenAI 模型"
    },
    "kimi": {
        "name": "Kimi (Moonshot)",
        "default_base_url": "https://api.moonshot.cn/v1",
        "description": "Moonshot AI 模型"
    },
    "glm": {
        "name": "智谱 AI",
        "default_base_url": "https://open.bigmodel.cn/api/paas/v4",
        "description": "智谱 AI 大模型"
    },
}

# 内置模型定义
BUILTIN_MODELS = {
    "deepseek": {
        "deepseek-chat": {
            "name": "DeepSeek Chat",
            "capabilities": ["chat"],
            "description": "DeepSeek 对话模型"
        },
        "deepseek-coder": {
            "name": "DeepSeek Coder",
            "capabilities": ["chat"],
            "description": "DeepSeek 代码模型"
        },
    },
    "openai": {
        "gpt-4": {
            "name": "GPT-4",
            "capabilities": ["chat"],
            "description": "OpenAI GPT-4"
        },
        "gpt-4o": {
            "name": "GPT-4o",
            "capabilities": ["chat", "image"],
            "description": "OpenAI GPT-4o"
        },
    },
    "kimi": {
        "moonshot-v1-8k": {
            "name": "Moonshot v1 8K",
            "capabilities": ["chat"],
            "description": "Kimi 对话模型"
        },
    },
    "glm": {
        "glm-4": {
            "name": "GLM-4",
            "capabilities": ["chat"],
            "description": "智谱 GLM-4"
        },
        "glm-4-voice": {
            "name": "GLM-4 Voice",
            "capabilities": ["audio"],
            "description": "智谱语音合成"
        },
        "cogview-4": {
            "name": "CogView-4",
            "capabilities": ["image"],
            "description": "智谱图像生成"
        },
        "cogvideox": {
            "name": "CogVideoX",
            "capabilities": ["video"],
            "description": "智谱视频生成"
        },
    },
}

# 能力类型定义
CAPABILITY_TYPES = {
    "chat": "文字对话",
    "image": "图片生成",
    "audio": "音频生成",
    "video": "视频生成",
}

# 所有能力的列表
ALL_CAPABILITIES = list(CAPABILITY_TYPES.keys())


def get_builtin_providers():
    """获取内置供应商列表"""
    return [
        {
            "code": code,
            "name": config["name"],
            "default_base_url": config["default_base_url"],
            "description": config.get("description", "")
        }
        for code, config in BUILTIN_PROVIDERS.items()
    ]


def get_builtin_models(provider_code: str = None):
    """获取内置模型列表"""
    if provider_code:
        models = BUILTIN_MODELS.get(provider_code, {})
        return [
            {
                "code": model_code,
                "name": config["name"],
                "capabilities": config["capabilities"],
                "description": config.get("description", "")
            }
            for model_code, config in models.items()
        ]

    # 返回所有模型
    result = []
    for provider_code, models in BUILTIN_MODELS.items():
        for model_code, config in models.items():
            result.append({
                "code": model_code,
                "provider_code": provider_code,
                "name": config["name"],
                "capabilities": config["capabilities"],
                "description": config.get("description", "")
            })
    return result


def validate_provider_code(provider_code: str) -> bool:
    """验证供应商代码是否有效"""
    return provider_code in BUILTIN_PROVIDERS


def validate_model_code(provider_code: str, model_code: str) -> bool:
    """验证模型代码是否有效"""
    if provider_code not in BUILTIN_MODELS:
        return False
    return model_code in BUILTIN_MODELS[provider_code]
```

- [ ] **Step 2: 创建单元测试**

```python
# backend/tests/unit/test_builtin_models.py
import pytest
from src.services.builtin_models import (
    get_builtin_providers,
    get_builtin_models,
    validate_provider_code,
    validate_model_code,
    BUILTIN_PROVIDERS,
    ALL_CAPABILITIES
)


def test_get_builtin_providers():
    """测试获取内置供应商列表"""
    providers = get_builtin_providers()
    assert len(providers) == 4
    assert any(p["code"] == "deepseek" for p in providers)
    assert any(p["code"] == "openai" for p in providers)


def test_get_builtin_models_all():
    """测试获取所有内置模型"""
    models = get_builtin_models()
    assert len(models) > 0
    assert any(m["code"] == "deepseek-chat" for m in models)


def test_get_builtin_models_by_provider():
    """测试按供应商获取模型"""
    models = get_builtin_models("deepseek")
    assert len(models) == 2
    assert any(m["code"] == "deepseek-chat" for m in models)


def test_validate_provider_code():
    """测试供应商代码验证"""
    assert validate_provider_code("deepseek") is True
    assert validate_provider_code("invalid") is False


def test_validate_model_code():
    """测试模型代码验证"""
    assert validate_model_code("deepseek", "deepseek-chat") is True
    assert validate_model_code("deepseek", "invalid") is False
    assert validate_model_code("invalid", "deepseek-chat") is False


def test_all_capabilities():
    """测试能力列表"""
    assert "chat" in ALL_CAPABILITIES
    assert "image" in ALL_CAPABILITIES
    assert "audio" in ALL_CAPABILITIES
    assert "video" in ALL_CAPABILITIES
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python3 -m pytest tests/unit/test_builtin_models.py -v
```

Expected: 全部通过

- [ ] **Step 4: 提交**

```bash
git add backend/src/services/builtin_models.py backend/tests/unit/test_builtin_models.py
git commit -m "feat: 添加内置模型定义和测试"
```

---

## Task 4: 创建加密服务

**Files:**
- Create: `backend/src/services/encryption_service.py`
- Create: `backend/tests/unit/test_encryption_service.py`
- Modify: `backend/.env.example`

- [ ] **Step 1: 创建加密服务**

```python
# backend/src/services/encryption_service.py
"""API Key 加密服务"""
import os
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class EncryptionService:
    """API Key 加密服务"""

    def __init__(self):
        """初始化加密服务"""
        key = os.getenv("API_KEY_ENCRYPTION_KEY")
        if not key:
            raise ValueError("API_KEY_ENCRYPTION_KEY 环境变量未设置")
        try:
            self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            raise ValueError(f"加密密钥格式错误: {e}")

    def encrypt(self, plaintext: str) -> str:
        """加密明文

        Args:
            plaintext: 明文字符串

        Returns:
            加密后的字符串（base64编码）
        """
        if not plaintext:
            return ""
        try:
            return self.cipher.encrypt(plaintext.encode()).decode()
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """解密密文

        Args:
            ciphertext: 加密后的字符串

        Returns:
            解密后的明文

        Raises:
            ValueError: 解密失败
        """
        if not ciphertext:
            return ""
        try:
            return self.cipher.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            raise ValueError("解密失败：密文已损坏或密钥错误")
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise


# 全局单例
_encryption_service = None


def get_encryption_service() -> EncryptionService:
    """获取加密服务单例"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
```

- [ ] **Step 2: 创建单元测试**

```python
# backend/tests/unit/test_encryption_service.py
import pytest
import os
from cryptography.fernet import Fernet
from src.services.encryption_service import EncryptionService, get_encryption_service


@pytest.fixture
def encryption_key():
    """生成测试用的加密密钥"""
    return Fernet.generate_key().decode()


@pytest.fixture
def encryption_service(monkeypatch, encryption_key):
    """创建加密服务实例"""
    monkeypatch.setenv("API_KEY_ENCRYPTION_KEY", encryption_key)
    return EncryptionService()


def test_encrypt_decrypt(encryption_service):
    """测试加密解密"""
    plaintext = "sk-test-api-key-12345"
    ciphertext = encryption_service.encrypt(plaintext)
    decrypted = encryption_service.decrypt(ciphertext)
    assert decrypted == plaintext
    assert ciphertext != plaintext


def test_encrypt_empty_string(encryption_service):
    """测试加密空字符串"""
    assert encryption_service.encrypt("") == ""


def test_decrypt_empty_string(encryption_service):
    """测试解密空字符串"""
    assert encryption_service.decrypt("") == ""


def test_decrypt_invalid_ciphertext(encryption_service):
    """测试解密无效密文"""
    with pytest.raises(ValueError, match="解密失败"):
        encryption_service.decrypt("invalid_ciphertext")


def test_no_encryption_key(monkeypatch):
    """测试没有设置加密密钥"""
    monkeypatch.delenv("API_KEY_ENCRYPTION_KEY", raising=False)
    with pytest.raises(ValueError, match="API_KEY_ENCRYPTION_KEY 环境变量未设置"):
        EncryptionService()


def test_invalid_encryption_key(monkeypatch):
    """测试无效的加密密钥"""
    monkeypatch.setenv("API_KEY_ENCRYPTION_KEY", "invalid_key")
    with pytest.raises(ValueError, match="加密密钥格式错误"):
        EncryptionService()


def test_singleton(monkeypatch, encryption_key):
    """测试单例模式"""
    monkeypatch.setenv("API_KEY_ENCRYPTION_KEY", encryption_key)
    service1 = get_encryption_service()
    service2 = get_encryption_service()
    assert service1 is service2
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python3 -m pytest tests/unit/test_encryption_service.py -v
```

Expected: 全部通过

- [ ] **Step 4: 更新 .env.example**

```bash
# 在 backend/.env.example 末尾添加
echo "" >> backend/.env.example
echo "# API Key 加密密钥（使用 python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" 生成）" >> backend/.env.example
echo "API_KEY_ENCRYPTION_KEY=your-encryption-key-here" >> backend/.env.example
```

- [ ] **Step 5: 提交**

```bash
git add backend/src/services/encryption_service.py backend/tests/unit/test_encryption_service.py backend/.env.example
git commit -m "feat: 添加 API Key 加密服务"
```

---

## Task 5: 创建模型配置服务

**Files:**
- Create: `backend/src/services/model_provider_service.py`
- Create: `backend/tests/unit/test_model_provider_service.py`
- Modify: `backend/src/models.py` (添加 Pydantic 模型)

- [ ] **Step 1: 在 models.py 中添加 Pydantic 模型**

在 `backend/src/models.py` 末尾添加：

```python
# backend/src/models.py - 在文件末尾添加

from typing import List, Optional
from pydantic import BaseModel, Field


# ==================== 模型供应商配置相关模型 ====================

class BuiltinProviderInfo(BaseModel):
    """内置供应商信息"""
    code: str = Field(..., description="供应商代码")
    name: str = Field(..., description="供应商名称")
    default_base_url: str = Field(..., description="默认API地址")
    description: str = Field("", description="描述")


class BuiltinModelInfo(BaseModel):
    """内置模型信息"""
    code: str = Field(..., description="模型代码")
    provider_code: Optional[str] = Field(None, description="供应商代码")
    name: str = Field(..., description="模型名称")
    capabilities: List[str] = Field(..., description="支持的能力列表")
    description: str = Field("", description="描述")


class ModelProviderResponse(BaseModel):
    """模型供应商响应"""
    id: str
    provider_code: str
    provider_name: str
    base_url: str
    is_enabled: bool
    is_default: bool
    order: int
    model_count: int = Field(0, description="模型数量")
    created_at: str
    updated_at: str


class CreateModelProviderRequest(BaseModel):
    """创建模型供应商请求"""
    provider_code: str = Field(..., description="供应商代码（内置）")
    api_key: str = Field(..., min_length=1, description="API密钥")
    base_url: Optional[str] = Field(None, description="API地址（可选，使用默认值）")
    is_enabled: bool = Field(True, description="是否启用")
    order: int = Field(0, description="排序")


class UpdateModelProviderRequest(BaseModel):
    """更新模型供应商请求"""
    api_key: Optional[str] = Field(None, description="API密钥")
    base_url: Optional[str] = Field(None, description="API地址")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    order: Optional[int] = Field(None, description="排序")


class ModelConfigResponse(BaseModel):
    """模型配置响应"""
    id: str
    provider_id: str
    provider_code: str
    provider_name: str
    model_code: str
    model_name: str
    capabilities: List[str]
    is_enabled: bool
    created_at: str
    updated_at: str


class CreateModelConfigRequest(BaseModel):
    """创建模型配置请求"""
    model_code: str = Field(..., description="模型代码（内置）")
    capabilities: List[str] = Field(..., min_items=1, description="支持的能力列表")
    is_enabled: bool = Field(True, description="是否启用")


class UpdateModelConfigRequest(BaseModel):
    """更新模型配置请求"""
    capabilities: Optional[List[str]] = Field(None, min_items=1, description="支持的能力列表")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class TestConnectionRequest(BaseModel):
    """测试连接请求"""
    api_key: str = Field(..., description="API密钥")
    base_url: str = Field(..., description="API地址")


class TestConnectionResponse(BaseModel):
    """测试连接响应"""
    success: bool
    message: str


class AvailableModelInfo(BaseModel):
    """可用模型信息"""
    id: str = Field(..., description="模型配置ID")
    model_code: str = Field(..., description="模型代码")
    model_name: str = Field(..., description="模型名称")
    provider_code: str = Field(..., description="供应商代码")
    provider_name: str = Field(..., description="供应商名称")
    capabilities: List[str] = Field(..., description="支持的能力")


class AvailableModelsResponse(BaseModel):
    """可用模型列表响应"""
    models: List[AvailableModelInfo]
```

- [ ] **Step 2: 创建模型配置服务**

```python
# backend/src/services/model_provider_service.py
"""模型供应商配置服务"""
import logging
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from src.db_models import ModelProviderModel, ModelConfigModel
from src.services.builtin_models import (
    get_builtin_providers,
    get_builtin_models,
    validate_provider_code,
    validate_model_code,
    BUILTIN_PROVIDERS,
    CAPABILITY_TYPES
)
from src.services.encryption_service import get_encryption_service
from src.models import (
    ModelProviderResponse,
    ModelConfigResponse,
    AvailableModelInfo,
    CreateModelProviderRequest,
    UpdateModelProviderRequest,
    CreateModelConfigRequest,
    UpdateModelConfigRequest,
)

logger = logging.getLogger(__name__)


class ModelProviderService:
    """模型供应商配置服务"""

    def __init__(self, db: Session):
        self.db = db
        self.encryption = get_encryption_service()

    def get_builtin_providers(self) -> List[dict]:
        """获取内置供应商列表"""
        return get_builtin_providers()

    def get_builtin_models(self, provider_code: str = None) -> List[dict]:
        """获取内置模型列表"""
        return get_builtin_models(provider_code)

    def get_providers(self, is_enabled: bool = None) -> List[ModelProviderResponse]:
        """获取已配置的供应商列表"""
        query = self.db.query(ModelProviderModel)
        if is_enabled is not None:
            query = query.filter(ModelProviderModel.is_enabled == is_enabled)
        providers = query.order_by(ModelProviderModel.order).all()

        result = []
        for p in providers:
            # 统计模型数量
            model_count = self.db.query(ModelConfigModel).filter(
                ModelConfigModel.provider_id == p.id
            ).count()

            result.append(ModelProviderResponse(
                id=p.id,
                provider_code=p.provider_code,
                provider_name=p.provider_name,
                base_url=p.base_url or "",
                is_enabled=p.is_enabled,
                is_default=p.is_default,
                order=p.order,
                model_count=model_count,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat()
            ))
        return result

    def get_provider(self, provider_id: str) -> Optional[ModelProviderResponse]:
        """获取单个供应商配置"""
        p = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.id == provider_id
        ).first()
        if not p:
            return None

        model_count = self.db.query(ModelConfigModel).filter(
            ModelConfigModel.provider_id == p.id
        ).count()

        return ModelProviderResponse(
            id=p.id,
            provider_code=p.provider_code,
            provider_name=p.provider_name,
            base_url=p.base_url or "",
            is_enabled=p.is_enabled,
            is_default=p.is_default,
            order=p.order,
            model_count=model_count,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat()
        )

    def get_provider_by_code(self, provider_code: str) -> Optional[ModelProviderModel]:
        """根据供应商代码获取配置"""
        return self.db.query(ModelProviderModel).filter(
            ModelProviderModel.provider_code == provider_code,
            ModelProviderModel.is_enabled == True
        ).first()

    def create_provider(self, request: CreateModelProviderRequest) -> ModelProviderResponse:
        """创建供应商配置"""
        # 验证供应商代码
        if not validate_provider_code(request.provider_code):
            raise ValueError(f"无效的供应商代码: {request.provider_code}")

        # 检查是否已存在
        existing = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.provider_code == request.provider_code
        ).first()
        if existing:
            raise ValueError(f"供应商 {request.provider_code} 已配置")

        # 获取内置配置
        builtin = BUILTIN_PROVIDERS[request.provider_code]
        base_url = request.base_url or builtin["default_base_url"]

        # 加密 API Key
        api_key_encrypted = self.encryption.encrypt(request.api_key)

        provider = ModelProviderModel(
            id=str(uuid.uuid4()),
            provider_code=request.provider_code,
            provider_name=builtin["name"],
            api_key_encrypted=api_key_encrypted,
            base_url=base_url,
            is_enabled=request.is_enabled,
            order=request.order
        )

        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)

        return self.get_provider(provider.id)

    def update_provider(self, provider_id: str, request: UpdateModelProviderRequest) -> ModelProviderResponse:
        """更新供应商配置"""
        provider = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.id == provider_id
        ).first()
        if not provider:
            raise ValueError("供应商不存在")

        if request.api_key is not None:
            provider.api_key_encrypted = self.encryption.encrypt(request.api_key)
        if request.base_url is not None:
            provider.base_url = request.base_url
        if request.is_enabled is not None:
            provider.is_enabled = request.is_enabled
        if request.order is not None:
            provider.order = request.order

        self.db.commit()
        self.db.refresh(provider)

        return self.get_provider(provider_id)

    def delete_provider(self, provider_id: str) -> bool:
        """删除供应商配置"""
        provider = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.id == provider_id
        ).first()
        if not provider:
            return False

        self.db.delete(provider)
        self.db.commit()
        return True

    def set_default_provider(self, provider_id: str) -> ModelProviderResponse:
        """设置默认供应商"""
        # 取消所有默认
        self.db.query(ModelProviderModel).filter(
            ModelProviderModel.is_default == True
        ).update({"is_default": False})

        # 设置新的默认
        provider = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.id == provider_id
        ).first()
        if not provider:
            raise ValueError("供应商不存在")

        provider.is_default = True
        self.db.commit()
        self.db.refresh(provider)

        return self.get_provider(provider_id)

    def get_provider_models(self, provider_id: str) -> List[ModelConfigResponse]:
        """获取供应商下的模型配置"""
        provider = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.id == provider_id
        ).first()
        if not provider:
            raise ValueError("供应商不存在")

        configs = self.db.query(ModelConfigModel).filter(
            ModelConfigModel.provider_id == provider_id
        ).order_by(ModelConfigModel.created_at).all()

        result = []
        for c in configs:
            capabilities_list = c.capabilities.split(",") if c.capabilities else []
            result.append(ModelConfigResponse(
                id=c.id,
                provider_id=c.provider_id,
                provider_code=provider.provider_code,
                provider_name=provider.provider_name,
                model_code=c.model_code,
                model_name=c.model_name,
                capabilities=capabilities_list,
                is_enabled=c.is_enabled,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat()
            ))
        return result

    def create_model_config(self, provider_id: str, request: CreateModelConfigRequest) -> ModelConfigResponse:
        """创建模型配置"""
        provider = self.db.query(ModelProviderModel).filter(
            ModelProviderModel.id == provider_id
        ).first()
        if not provider:
            raise ValueError("供应商不存在")

        # 验证模型代码
        if not validate_model_code(provider.provider_code, request.model_code):
            raise ValueError(f"无效的模型代码: {request.model_code}")

        # 检查是否已存在
        existing = self.db.query(ModelConfigModel).filter(
            ModelConfigModel.provider_id == provider_id,
            ModelConfigModel.model_code == request.model_code
        ).first()
        if existing:
            raise ValueError(f"模型 {request.model_code} 已配置")

        # 获取内置配置
        builtin_models = get_builtin_models(provider.provider_code)
        builtin = next((m for m in builtin_models if m["code"] == request.model_code), None)
        if not builtin:
            raise ValueError(f"模型 {request.model_code} 不在内置列表中")

        # 验证能力
        for cap in request.capabilities:
            if cap not in CAPABILITY_TYPES:
                raise ValueError(f"无效的能力类型: {cap}")

        config = ModelConfigModel(
            id=str(uuid.uuid4()),
            provider_id=provider_id,
            model_code=request.model_code,
            model_name=builtin["name"],
            capabilities=",".join(request.capabilities),
            is_enabled=request.is_enabled
        )

        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        return self.get_provider_models(provider_id)[-1]

    def update_model_config(self, config_id: str, request: UpdateModelConfigRequest) -> ModelConfigResponse:
        """更新模型配置"""
        config = self.db.query(ModelConfigModel).filter(
            ModelConfigModel.id == config_id
        ).first()
        if not config:
            raise ValueError("模型配置不存在")

        if request.capabilities is not None:
            # 验证能力
            for cap in request.capabilities:
                if cap not in CAPABILITY_TYPES:
                    raise ValueError(f"无效的能力类型: {cap}")
            config.capabilities = ",".join(request.capabilities)

        if request.is_enabled is not None:
            config.is_enabled = request.is_enabled

        self.db.commit()
        self.db.refresh(config)

        return self.get_model_config(config_id)

    def delete_model_config(self, config_id: str) -> bool:
        """删除模型配置"""
        config = self.db.query(ModelConfigModel).filter(
            ModelConfigModel.id == config_id
        ).first()
        if not config:
            return False

        self.db.delete(config)
        self.db.commit()
        return True

    def get_model_config(self, config_id: str) -> ModelConfigResponse:
        """获取单个模型配置"""
        config = self.db.query(ModelConfigModel).filter(
            ModelConfigModel.id == config_id
        ).first()
        if not config:
            return None

        provider = config.provider
        capabilities_list = config.capabilities.split(",") if config.capabilities else []

        return ModelConfigResponse(
            id=config.id,
            provider_id=config.provider_id,
            provider_code=provider.provider_code,
            provider_name=provider.provider_name,
            model_code=config.model_code,
            model_name=config.model_name,
            capabilities=capabilities_list,
            is_enabled=config.is_enabled,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat()
        )

    def get_available_models(self, capability: str = None) -> List[AvailableModelInfo]:
        """获取可用的模型列表

        Args:
            capability: 能力类型过滤（chat/image/audio/video）
        """
        query = self.db.query(ModelConfigModel).join(
            ModelProviderModel,
            ModelConfigModel.provider_id == ModelProviderModel.id
        ).filter(
            ModelProviderModel.is_enabled == True,
            ModelConfigModel.is_enabled == True
        )

        models = query.all()

        result = []
        for m in models:
            capabilities_list = m.capabilities.split(",") if m.capabilities else []

            # 能力过滤
            if capability and capability not in capabilities_list:
                continue

            result.append(AvailableModelInfo(
                id=m.id,
                model_code=m.model_code,
                model_name=m.model_name,
                provider_code=m.provider.provider_code,
                provider_name=m.provider.provider_name,
                capabilities=capabilities_list
            ))

        return result

    def get_model_config_by_code(self, provider_code: str, model_code: str) -> Optional[ModelConfigModel]:
        """根据供应商和模型代码获取配置"""
        return self.db.query(ModelConfigModel).join(
            ModelProviderModel,
            ModelConfigModel.provider_id == ModelProviderModel.id
        ).filter(
            ModelProviderModel.provider_code == provider_code,
            ModelConfigModel.model_code == model_code,
            ModelProviderModel.is_enabled == True,
            ModelConfigModel.is_enabled == True
        ).first()
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python3 -c "from src.services.model_provider_service import ModelProviderService; print('Import success')"
```

Expected: `Import success`

- [ ] **Step 4: 提交**

```bash
git add backend/src/models.py backend/src/services/model_provider_service.py
git commit -m "feat: 添加模型配置服务和 Pydantic 模型"
```

---

## Task 6: 创建管理 API 路由

**Files:**
- Create: `backend/src/interfaces/routers/admin/model_providers.py`
- Modify: `backend/src/main.py`
- Modify: `backend/src/interfaces/dependencies.py`

- [ ] **Step 1: 创建管理 API 路由文件**

```python
# backend/src/interfaces/routers/admin/model_providers.py
# -*- coding: utf-8 -*-
"""模型供应商配置管理 API"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from src.interfaces.dependencies import get_db, require_admin
from src.interfaces.auth import UserInfo
from src.services.model_provider_service import ModelProviderService
from src.models import (
    BuiltinProviderInfo,
    BuiltinModelInfo,
    ModelProviderResponse,
    ModelConfigResponse,
    CreateModelProviderRequest,
    UpdateModelProviderRequest,
    CreateModelConfigRequest,
    UpdateModelConfigRequest,
    AvailableModelsResponse,
    AvailableModelInfo,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin/models", tags=["模型配置管理"])


# ==================== 内置定义 API ====================

@router.get("/builtin-providers", response_model=list[BuiltinProviderInfo])
async def get_builtin_providers():
    """获取内置供应商列表"""
    from src.services.builtin_models import get_builtin_providers
    providers = get_builtin_providers()
    return [BuiltinProviderInfo(**p) for p in providers]


@router.get("/builtin-models", response_model=list[BuiltinModelInfo])
async def get_builtin_models(provider_code: str = None):
    """获取内置模型列表"""
    from src.services.builtin_models import get_builtin_models
    models = get_builtin_models(provider_code)
    return [BuiltinModelInfo(**m) for m in models]


# ==================== 供应商管理 API ====================

@router.get("/providers")
async def get_providers(
    is_enabled: bool = None,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None
):
    """获取已配置的供应商列表"""
    from src.database import get_db
    db = next(get_db())
    try:
        service = ModelProviderService(db)
        providers = service.get_providers(is_enabled)
        return {"providers": providers}
    finally:
        db.close()


@router.post("/providers", response_model=ModelProviderResponse)
async def create_provider(
    request: CreateModelProviderRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None
):
    """创建供应商配置"""
    from src.database import get_db
    db = next(get_db())
    try:
        service = ModelProviderService(db)
        return service.create_provider(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.get("/providers/{provider_id}", response_model=ModelProviderResponse)
async def get_provider(
    provider_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None
):
    """获取单个供应商配置"""
    from src.database import get_db
    db = next(get_db())
    try:
        service = ModelProviderService(db)
        result = service.get_provider(provider_id)
        if not result:
            raise HTTPException(status_code=404, detail="供应商不存在")
        return result
    finally:
        db.close()


@router.put("/providers/{provider_id}", response_model=ModelProviderResponse)
async def update_provider(
    provider_id: str,
    request: UpdateModelProviderRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None
):
    """更新供应商配置"""
    from src.database import get_db
    db = next(get_db())
    try:
        service = ModelProviderService(db)
        return service.update_provider(provider_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None
):
    """删除供应商配置"""
    from src.database import get_db
    db = next(get_db())
    try:
        service = ModelProviderService(db)
        success = service.delete_provider(provider_id)
        if not success:
            raise HTTPException(status_code=404, detail="供应商不存在")
        return {"success": True}
    finally:
        db.close()


@router.post("/providers/{provider_id}/test")
async def test_provider_connection(
    provider_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None
):
    """测试供应商连接"""
    from src.database import get_db
    from src.services.ai_service import AIService
    db = next(get_db())
    try:
        service = ModelProviderService(db)
        provider = service.get_provider_by_code(service.get_provider(provider_id).provider_code)

        # 简单测试：尝试调用模型列表或发送一个简单请求
        # 这里简化处理，实际可以调用供应商的 API 进行测试
        return {"success": True, "message": "连接测试功能待实现"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


@router.put("/providers/{provider_id}/set-default", response_model=ModelProviderResponse)
async def set_default_provider(
    provider_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None
):
    """设置默认供应商"""
    from src.database import get_db
    db = next(get_db())
    try:
        service = ModelProviderService(db)
        return service.set_default_provider(provider_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


# ==================== 模型配置管理 API ====================

@router.get("/providers/{provider_id}/models")
async def get_provider_models(
    provider_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None
):
    """获取供应商下的模型配置"""
    from src.database import get_db
    db = next(get_db())
    try:
        service = ModelProviderService(db)
        models = service.get_provider_models(provider_id)
        return {"models": models}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.post("/providers/{provider_id}/models", response_model=ModelConfigResponse)
async def create_model_config(
    provider_id: str,
    request: CreateModelConfigRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None
):
    """为供应商添加模型配置"""
    from src.database import get_db
    db = next(get_db())
    try:
        service = ModelProviderService(db)
        return service.create_model_config(provider_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.put("/models/{config_id}", response_model=ModelConfigResponse)
async def update_model_config(
    config_id: str,
    request: UpdateModelConfigRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None
):
    """更新模型配置"""
    from src.database import get_db
    db = next(get_db())
    try:
        service = ModelProviderService(db)
        return service.update_model_config(config_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.delete("/models/{config_id}")
async def delete_model_config(
    config_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None
):
    """删除模型配置"""
    from src.database import get_db
    db = next(get_db())
    try:
        service = ModelProviderService(db)
        success = service.delete_model_config(config_id)
        if not success:
            raise HTTPException(status_code=404, detail="模型配置不存在")
        return {"success": True}
    finally:
        db.close()
```

- [ ] **Step 2: 在 main.py 中注册路由**

在 `backend/src/main.py` 的路由注册部分添加：

```python
# backend/src/main.py - 在路由注册部分添加

from src.interfaces.routers.admin import model_providers as new_admin_model_providers_router

# 在管理路由部分添加
app.include_router(new_admin_model_providers_router.router)
```

- [ ] **Step 3: 测试 API 可访问**

```bash
cd backend && python3 -c "
from src.main import app
routes = [r.path for r in app.routes if '/admin/models' in r.path]
for r in routes:
    print(r)
"
```

Expected: 显示新增的 API 路由

- [ ] **Step 4: 提交**

```bash
git add backend/src/interfaces/routers/admin/model_providers.py backend/src/main.py
git commit -m \"feat: 添加模型供应商配置管理 API\"
```

---

## Task 7: 更新公开 API 路由

**Files:**
- Modify: `backend/src/interfaces/routers/models.py`
- Modify: `backend/src/main.py`

**说明：** 替换现有的 `models.py` 路由文件，保留 `GET /models` 端点并添加新的 `GET /models/available` 端点

- [ ] **Step 1: 更新 models.py 添加新端点**

在现有的 `backend/src/interfaces/routers/models.py` 文件中添加新端点：

```python
# backend/src/interfaces/routers/models.py - 在文件中添加

@router.get("/available")
async def get_available_models(
    capability: str = Query(None, description="能力类型过滤（chat/image/audio/video）"),
    db: Session = Depends(get_db)
):
    """获取可用的模型列表

    工具在选择模型时调用此接口，根据需要的能力筛选可用模型
    """
    try:
        from src.services.model_provider_service import ModelProviderService
        from src.models import AvailableModelsResponse

        service = ModelProviderService(db)
        models = service.get_available_models(capability)
        return AvailableModelsResponse(models=models)
    except Exception as e:
        logger.error(f"获取可用模型失败: {e}")
        return {"models": []}
```

- [ ] **Step 2: 验证 main.py 中的路由注册**

确认 `main.py` 中已有以下导入（不需要修改）：

```python
# backend/src/main.py - 确认已有此导入
from src.interfaces.routers import models as new_models_router
```

路由注册保持不变：

```python
app.include_router(new_models_router.router, prefix="/api/v1")
```

- [ ] **Step 3: 测试 API**

```bash
# 启动服务器
cd backend && python3 -m src.main &

# 测试 API
curl -s http://localhost:8000/api/v1/models/available | python3 -m json.tool
```

Expected: 返回模型列表（初始为空）

- [ ] **Step 4: 停止服务器并提交**

```bash
# 停止服务器
pkill -f "python3 -m src.main"

git add backend/src/interfaces/routers/models_public.py backend/src/main.py
git commit -m "feat: 添加模型配置公开 API"
```

---

## Task 8: 添加依赖注入

**Files:**
- Modify: `backend/src/interfaces/dependencies.py`

- [ ] **Step 1: 添加 get_model_provider_service 依赖**

```python
# backend/src/interfaces/dependencies.py - 在 __all__ 中添加

__all__ = [
    # ... 现有导出 ...
    "get_model_provider_service",  # 新增
]

# 在文件末尾添加：

def get_model_provider_service():
    """获取模型配置服务实例"""
    from src.services.model_provider_service import ModelProviderService
    db = next(get_db())
    try:
        yield ModelProviderService(db)
    finally:
        db.close()
```

- [ ] **Step 2: 提交**

```bash
git add backend/src/interfaces/dependencies.py
git commit -m "feat: 添加模型配置服务依赖注入"
```

---

## Task 9: 修改 AIService 从数据库读取配置

**Files:**
- Modify: `backend/src/services/ai_service.py`

- [ ] **Step 1: 修改 _get_ai_client 方法**

```python
# backend/src/services/ai_service.py - 修改 _get_ai_client 方法

    def _get_ai_client(self, model_config: Optional[str] = None) -> Tuple[Optional[OpenAI], str]:
        """
        根据配置获取 OpenAI 兼容的客户端实例和模型名称。

        Args:
            model_config: 模型配置字符串，格式：provider:model_name（如 "deepseek:deepseek-coder"）
                         如果为 None，使用默认配置

        Returns:
            (client, model_name) 元组
        """
        from src.database import SessionLocal
        from src.services.model_provider_service import ModelProviderService
        from src.services.encryption_service import get_encryption_service

        # 解析 model_config
        if model_config and ":" in model_config:
            provider_code, model_name = model_config.split(":", 1)
            provider_code = provider_code.lower()
            logger.info(f"使用工具指定的模型配置: {provider_code}:{model_name}")
        else:
            # 使用默认供应商
            db = SessionLocal()
            try:
                service = ModelProviderService(db)
                # 获取默认供应商
                providers = service.get_providers(is_enabled=True)
                default_provider = next((p for p in providers if p.is_default), None)
                if not default_provider and providers:
                    default_provider = providers[0]

                if not default_provider:
                    logger.warning("未找到已配置的供应商，将使用 Mock 模式")
                    return None, "mock-model"

                provider_code = default_provider.provider_code
                # 获取该供应商的第一个启用的模型
                models = service.get_provider_models(default_provider.id)
                enabled_models = [m for m in models if m.is_enabled]
                if not enabled_models:
                    logger.warning(f"供应商 {provider_code} 没有启用的模型")
                    return None, "mock-model"

                model_name = enabled_models[0].model_code
                logger.info(f"使用系统默认配置: {provider_code}:{model_name}")
            finally:
                db.close()

        # 从数据库获取供应商配置
        db = SessionLocal()
        try:
            service = ModelProviderService(db)
            provider = service.get_provider_by_code(provider_code)

            if not provider or not provider.is_enabled:
                logger.warning(f"供应商 [{provider_code}] 未配置或未启用，将使用 Mock 模式")
                return None, "mock-model"

            # 解密 API Key
            encryption = get_encryption_service()
            try:
                api_key = encryption.decrypt(provider.api_key_encrypted)
            except Exception as e:
                logger.error(f"解密 API Key 失败: {e}")
                return None, "mock-model"

            base_url = provider.base_url

        finally:
            db.close()

        # 创建客户端
        timeout_seconds = float(os.getenv("AI_REQUEST_TIMEOUT", "120"))

        try:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout_seconds,
                max_retries=2
            )

            logger.info(f"AI 客户端初始化成功 - 服务商: {provider_code}, 模型: {model_name}, 超时: {timeout_seconds}秒")
            return client, model_name
        except Exception as e:
            logger.error(f"创建 AI 客户端失败: {e}")
            return None, "mock-model"
```

- [ ] **Step 2: 提交**

```bash
git add backend/src/services/ai_service.py
git commit -m "refactor: AIService 从数据库读取模型配置"
```

---

## Task 10: 前端类型定义

**Files:**
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: 添加模型配置相关类型**

在 `frontend/src/types/index.ts` 末尾添加：

```typescript
// frontend/src/types/index.ts - 在文件末尾添加

// ==================== 模型供应商配置相关类型 ====================

/** 内置供应商信息 */
export interface BuiltinProviderInfo {
  code: string
  name: string
  default_base_url: string
  description: string
}

/** 内置模型信息 */
export interface BuiltinModelInfo {
  code: string
  provider_code?: string
  name: string
  capabilities: string[]
  description: string
}

/** 模型供应商响应 */
export interface ModelProviderResponse {
  id: string
  provider_code: string
  provider_name: string
  base_url: string
  is_enabled: boolean
  is_default: boolean
  order: number
  model_count: number
  created_at: string
  updated_at: string
}

/** 创建模型供应商请求 */
export interface CreateModelProviderRequest {
  provider_code: string
  api_key: string
  base_url?: string
  is_enabled?: boolean
  order?: number
}

/** 更新模型供应商请求 */
export interface UpdateModelProviderRequest {
  api_key?: string
  base_url?: string
  is_enabled?: boolean
  order?: number
}

/** 模型配置响应 */
export interface ModelConfigResponse {
  id: string
  provider_id: string
  provider_code: string
  provider_name: string
  model_code: string
  model_name: string
  capabilities: string[]
  is_enabled: boolean
  created_at: string
  updated_at: string
}

/** 创建模型配置请求 */
export interface CreateModelConfigRequest {
  model_code: string
  capabilities: string[]
  is_enabled?: boolean
}

/** 更新模型配置请求 */
export interface UpdateModelConfigRequest {
  capabilities?: string[]
  is_enabled?: boolean
}

/** 可用模型信息 */
export interface AvailableModelInfo {
  id: string
  model_code: string
  model_name: string
  provider_code: string
  provider_name: string
  capabilities: string[]
}

/** 可用模型列表响应 */
export interface AvailableModelsResponse {
  models: AvailableModelInfo[]
}

/** 能力类型 */
export type CapabilityType = 'chat' | 'image' | 'audio' | 'video'

/** 能力类型显示名称 */
export const CAPABILITY_NAMES: Record<CapabilityType, string> = {
  chat: '文字对话',
  image: '图片生成',
  audio: '音频生成',
  video: '视频生成',
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/types/index.ts
git commit -m "feat: 添加模型配置相关类型定义"
```

---

## Task 11: 前端 API 客户端方法

**Files:**
- Modify: `frontend/src/services/apiClient.ts`

- [ ] **Step 1: 添加模型配置相关 API 方法**

在 `frontend/src/services/apiClient.ts` 的 ApiService 类中添加：

```typescript
// frontend/src/services/apiClient.ts - 在 ApiService 类中添加

  // ==================== 模型供应商配置 API ====================

  /** 获取内置供应商列表 */
  static async getBuiltinProviders(): Promise<BuiltinProviderInfo[]> {
    const response = await this.get<BuiltinProviderInfo[]>('/admin/models/builtin-providers')
    return response
  }

  /** 获取内置模型列表 */
  static async getBuiltinModels(providerCode?: string): Promise<BuiltinModelInfo[]> {
    const params = providerCode ? `?provider_code=${providerCode}` : ''
    const response = await this.get<BuiltinModelInfo[]>(`/admin/models/builtin-models${params}`)
    return response
  }

  /** 获取已配置的供应商列表 */
  static async getModelProviders(isEnabled?: boolean): Promise<{ providers: ModelProviderResponse[] }> {
    const params = isEnabled !== undefined ? `?is_enabled=${isEnabled}` : ''
    const response = await this.get<{ providers: ModelProviderResponse[] }>(`/admin/models/providers${params}`)
    return response
  }

  /** 获取单个供应商配置 */
  static async getModelProvider(providerId: string): Promise<ModelProviderResponse> {
    const response = await this.get<ModelProviderResponse>(`/admin/models/providers/${providerId}`)
    return response
  }

  /** 创建供应商配置 */
  static async createModelProvider(data: CreateModelProviderRequest): Promise<ModelProviderResponse> {
    const response = await this.post<ModelProviderResponse>('/admin/models/providers', data)
    return response
  }

  /** 更新供应商配置 */
  static async updateModelProvider(providerId: string, data: UpdateModelProviderRequest): Promise<ModelProviderResponse> {
    const response = await this.put<ModelProviderResponse>(`/admin/models/providers/${providerId}`, data)
    return response
  }

  /** 删除供应商配置 */
  static async deleteModelProvider(providerId: string): Promise<void> {
    await this.delete(`/admin/models/providers/${providerId}`)
  }

  /** 测试供应商连接 */
  static async testModelProvider(providerId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.post<{ success: boolean; message: string }>(`/admin/models/providers/${providerId}/test`, {})
    return response
  }

  /** 设置默认供应商 */
  static async setDefaultModelProvider(providerId: string): Promise<ModelProviderResponse> {
    const response = await this.put<ModelProviderResponse>(`/admin/models/providers/${providerId}/set-default`, {})
    return response
  }

  /** 获取供应商下的模型配置 */
  static async getProviderModels(providerId: string): Promise<{ models: ModelConfigResponse[] }> {
    const response = await this.get<{ models: ModelConfigResponse[] }>(`/admin/models/providers/${providerId}/models`)
    return response
  }

  /** 创建模型配置 */
  static async createModelConfig(providerId: string, data: CreateModelConfigRequest): Promise<ModelConfigResponse> {
    const response = await this.post<ModelConfigResponse>(`/admin/models/providers/${providerId}/models`, data)
    return response
  }

  /** 更新模型配置 */
  static async updateModelConfig(configId: string, data: UpdateModelConfigRequest): Promise<ModelConfigResponse> {
    const response = await this.put<ModelConfigResponse>(`/admin/models/models/${configId}`, data)
    return response
  }

  /** 删除模型配置 */
  static async deleteModelConfig(configId: string): Promise<void> {
    await this.delete(`/admin/models/models/${configId}`)
  }

  /** 获取可用模型列表 */
  static async getAvailableModels(capability?: string): Promise<AvailableModelsResponse> {
    const params = capability ? `?capability=${capability}` : ''
    const response = await this.get<AvailableModelsResponse>(`/models/available${params}`)
    return response
  }
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/services/apiClient.ts
git commit -m "feat: 添加模型配置 API 客户端方法"
```

---

## Task 12: 创建前端管理页面

**Files:**
- Create: `frontend/src/views/admin/AdminModelProvidersPage.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/layouts/AdminLayout.vue`

- [ ] **Step 1: 创建管理页面组件**

```vue
<!-- frontend/src/views/admin/AdminModelProvidersPage.vue -->
<template>
  <div class="admin-model-providers-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>模型供应商配置</h3>
          <el-button type="primary" @click="handleCreateProvider">新建供应商</el-button>
        </div>
      </template>

      <!-- 供应商列表 -->
      <el-table :data="providers" v-loading="loading" row-key="id">
        <el-table-column prop="order" label="排序" width="80" />
        <el-table-column prop="provider_name" label="供应商名称" width="200" />
        <el-table-column prop="provider_code" label="代码" width="150" />
        <el-table-column label="API Key" width="200">
          <template #default="{ row }">
            {{ maskApiKey(row.api_key) }}
          </template>
        </el-table-column>
        <el-table-column prop="base_url" label="API 地址" min-width="250" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
            <el-tag :type="row.is_enabled ? 'success' : 'info'" size="small">
              {{ row.is_enabled ? '已启用' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model_count" label="模型数" width="80" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleViewModels(row)">模型</el-button>
            <el-button size="small" @click="handleEditProvider(row)">编辑</el-button>
            <el-button size="small" @click="handleSetDefault(row)" v-if="!row.is_default">设为默认</el-button>
            <el-button size="small" type="danger" @click="handleDeleteProvider(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑供应商对话框 -->
    <el-dialog
      v-model="providerDialogVisible"
      :title="isEditingProvider ? '编辑供应商' : '新建供应商'"
      width="600px"
    >
      <el-form ref="providerFormRef" :model="providerForm" :rules="providerRules" label-width="120px">
        <el-form-item label="供应商" prop="provider_code">
          <el-select
            v-model="providerForm.provider_code"
            placeholder="请选择供应商"
            :disabled="isEditingProvider"
            style="width: 100%"
          >
            <el-option
              v-for="provider in builtinProviders"
              :key="provider.code"
              :label="provider.name"
              :value="provider.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input v-model="providerForm.api_key" type="password" show-password placeholder="请输入 API Key" />
        </el-form-item>
        <el-form-item label="API 地址">
          <el-input v-model="providerForm.base_url" placeholder="留空使用默认地址" />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="providerForm.is_enabled" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="providerForm.order" :min="0" :max="999" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="providerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitProvider" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 模型列表对话框 -->
    <el-dialog
      v-model="modelsDialogVisible"
      :title="`${currentProvider?.provider_name} - 模型列表`"
      width="800px"
    >
      <div class="mb-4">
        <el-button type="primary" size="small" @click="handleAddModel">添加模型</el-button>
      </div>
      <el-table :data="models" v-loading="loadingModels">
        <el-table-column prop="model_name" label="模型名称" />
        <el-table-column prop="model_code" label="代码" />
        <el-table-column label="能力">
          <template #default="{ row }">
            <el-tag v-for="cap in row.capabilities" :key="cap" size="small" class="mr-1">
              {{ CAPABILITY_NAMES[cap as CapabilityType] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_enabled ? 'success' : 'info'" size="small">
              {{ row.is_enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="handleEditModel(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDeleteModel(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 添加/编辑模型对话框 -->
    <el-dialog
      v-model="modelDialogVisible"
      :title="isEditingModel ? '编辑模型' : '添加模型'"
      width="500px"
    >
      <el-form ref="modelFormRef" :model="modelForm" :rules="modelRules" label-width="100px">
        <el-form-item label="模型" prop="model_code">
          <el-select
            v-model="modelForm.model_code"
            placeholder="请选择模型"
            :disabled="isEditingModel"
            style="width: 100%"
          >
            <el-option
              v-for="model in availableBuiltinModels"
              :key="model.code"
              :label="model.name"
              :value="model.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="支持的能力" prop="capabilities">
          <el-checkbox-group v-model="modelForm.capabilities">
            <el-checkbox label="chat">文字对话</el-checkbox>
            <el-checkbox label="image">图片生成</el-checkbox>
            <el-checkbox label="audio">音频生成</el-checkbox>
            <el-checkbox label="video">视频生成</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="modelForm.is_enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="modelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitModel" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { ApiService } from '../../services/apiClient'
import type {
  ModelProviderResponse,
  ModelConfigResponse,
  CreateModelProviderRequest,
  UpdateModelProviderRequest,
  CreateModelConfigRequest,
  BuiltinProviderInfo,
  BuiltinModelInfo,
  CapabilityType,
} from '../../types'
import { CAPABILITY_NAMES } from '../../types'

// 数据
const providers = ref<ModelProviderResponse[]>([])
const builtinProviders = ref<BuiltinProviderInfo[]>([])
const builtinModels = ref<BuiltinModelInfo[]>([])
const models = ref<ModelConfigResponse[]>([])
const loading = ref(false)
const loadingModels = ref(false)
const submitting = ref(false)

// 对话框状态
const providerDialogVisible = ref(false)
const modelsDialogVisible = ref(false)
const modelDialogVisible = ref(false)
const isEditingProvider = ref(false)
const isEditingModel = ref(false)
const currentProvider = ref<ModelProviderResponse>()

// 表单
const providerFormRef = ref<FormInstance>()
const providerForm = reactive<CreateModelProviderRequest & { id?: string }>({
  provider_code: '',
  api_key: '',
  base_url: '',
  is_enabled: true,
  order: 0,
})

const modelFormRef = ref<FormInstance>()
const modelForm = reactive<CreateModelConfigRequest & { id?: string }>({
  model_code: '',
  capabilities: [],
  is_enabled: true,
})

// 验证规则
const providerRules: FormRules = {
  provider_code: [{ required: true, message: '请选择供应商', trigger: 'change' }],
  api_key: [{ required: true, message: '请输入 API Key', trigger: 'blur' }],
}

const modelRules: FormRules = {
  model_code: [{ required: true, message: '请选择模型', trigger: 'change' }],
  capabilities: [{ type: 'array', min: 1, message: '请至少选择一个能力', trigger: 'change' }],
}

// 可用的内置模型（根据选中的供应商过滤）
const availableBuiltinModels = computed(() => {
  if (!currentProvider.value) return []
  return builtinModels.value.filter(m => m.provider_code === currentProvider.value?.provider_code)
})

// 加载数据
async function loadProviders() {
  loading.value = true
  try {
    const response = await ApiService.getModelProviders()
    providers.value = response.providers
  } catch (error: any) {
    ElMessage.error(error.message || '加载供应商列表失败')
  } finally {
    loading.value = false
  }
}

async function loadBuiltinProviders() {
  try {
    builtinProviders.value = await ApiService.getBuiltinProviders()
  } catch (error: any) {
    ElMessage.error(error.message || '加载内置供应商失败')
  }
}

async function loadBuiltinModels() {
  try {
    builtinModels.value = await ApiService.getBuiltinModels()
  } catch (error: any) {
    ElMessage.error(error.message || '加载内置模型失败')
  }
}

async function loadModels(providerId: string) {
  loadingModels.value = true
  try {
    const response = await ApiService.getProviderModels(providerId)
    models.value = response.models
  } catch (error: any) {
    ElMessage.error(error.message || '加载模型列表失败')
  } finally {
    loadingModels.value = false
  }
}

// 供应商操作
function handleCreateProvider() {
  isEditingProvider.value = false
  Object.assign(providerForm, {
    provider_code: '',
    api_key: '',
    base_url: '',
    is_enabled: true,
    order: providers.value.length,
  })
  providerFormRef.value?.clearValidate()
  providerDialogVisible.value = true
}

function handleEditProvider(provider: ModelProviderResponse) {
  isEditingProvider.value = true
  currentProvider.value = provider
  Object.assign(providerForm, {
    id: provider.id,
    provider_code: provider.provider_code,
    api_key: '', // 不回填 API Key
    base_url: provider.base_url,
    is_enabled: provider.is_enabled,
    order: provider.order,
  })
  providerFormRef.value?.clearValidate()
  providerDialogVisible.value = true
}

async function handleSubmitProvider() {
  if (!providerFormRef.value) return

  await providerFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEditingProvider.value && providerForm.id) {
        await ApiService.updateModelProvider(providerForm.id, {
          api_key: providerForm.api_key || undefined,
          base_url: providerForm.base_url,
          is_enabled: providerForm.is_enabled,
          order: providerForm.order,
        })
        ElMessage.success('更新成功')
      } else {
        await ApiService.createModelProvider(providerForm as CreateModelProviderRequest)
        ElMessage.success('创建成功')
      }
      providerDialogVisible.value = false
      loadProviders()
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

async function handleDeleteProvider(provider: ModelProviderResponse) {
  try {
    await ElMessageBox.confirm(
      `确定要删除供应商 "${provider.provider_name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await ApiService.deleteModelProvider(provider.id)
    ElMessage.success('删除成功')
    loadProviders()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

async function handleSetDefault(provider: ModelProviderResponse) {
  try {
    await ApiService.setDefaultModelProvider(provider.id)
    ElMessage.success('设置成功')
    loadProviders()
  } catch (error: any) {
    ElMessage.error(error.message || '设置失败')
  }
}

// 模型操作
function handleViewModels(provider: ModelProviderResponse) {
  currentProvider.value = provider
  loadModels(provider.id)
  modelsDialogVisible.value = true
}

function handleAddModel() {
  isEditingModel.value = false
  Object.assign(modelForm, {
    model_code: '',
    capabilities: [],
    is_enabled: true,
  })
  modelFormRef.value?.clearValidate()
  modelDialogVisible.value = true
}

function handleEditModel(model: ModelConfigResponse) {
  isEditingModel.value = true
  Object.assign(modelForm, {
    id: model.id,
    model_code: model.model_code,
    capabilities: [...model.capabilities],
    is_enabled: model.is_enabled,
  })
  modelFormRef.value?.clearValidate()
  modelDialogVisible.value = true
}

async function handleSubmitModel() {
  if (!modelFormRef.value || !currentProvider.value) return

  await modelFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEditingModel.value && modelForm.id) {
        await ApiService.updateModelConfig(modelForm.id, {
          capabilities: modelForm.capabilities,
          is_enabled: modelForm.is_enabled,
        })
        ElMessage.success('更新成功')
      } else {
        await ApiService.createModelConfig(currentProvider.value!.id, modelForm as CreateModelConfigRequest)
        ElMessage.success('添加成功')
      }
      modelDialogVisible.value = false
      if (currentProvider.value) {
        loadModels(currentProvider.value.id)
      }
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

async function handleDeleteModel(model: ModelConfigResponse) {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 "${model.model_name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await ApiService.deleteModelConfig(model.id)
    ElMessage.success('删除成功')
    if (currentProvider.value) {
      loadModels(currentProvider.value.id)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 工具函数
function maskApiKey(key?: string): string {
  if (!key) return '***'
  if (key.length <= 8) return '***'
  return key.slice(0, 8) + '***'
}

// 初始化
onMounted(() => {
  loadProviders()
  loadBuiltinProviders()
  loadBuiltinModels()
})
</script>

<style scoped>
.admin-model-providers-page {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.mr-1 {
  margin-right: 4px;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>
```

- [ ] **Step 2: 添加路由配置**

在 `frontend/src/router/index.ts` 的管理路由部分添加：

```typescript
// frontend/src/router/index.ts - 在管理路由部分添加

{
  path: 'model-providers',
  name: 'AdminModelProviders',
  component: () => import('@/views/admin/AdminModelProvidersPage.vue'),
  meta: { requiresAuth: true, requiresAdmin: true, title: '模型供应商' }
}
```

- [ ] **Step 3: 在 AdminLayout 中添加导航菜单**

在 `frontend/src/layouts/AdminLayout.vue` 的配置管理菜单下添加：

```vue
<!-- frontend/src/layouts/AdminLayout.vue - 在配置管理菜单下添加 -->
<el-menu-item index="/admin/model-providers">
  <el-icon><Key /></el-icon>
  <span>模型供应商</span>
</el-menu-item>
```

**注意：** 需要在 `<script setup>` 部分导入 `Key` 图标：

```typescript
import { Key } from '@element-plus/icons-vue'
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/admin/AdminModelProvidersPage.vue frontend/src/router/index.ts frontend/src/layouts/AdminLayout.vue
git commit -m "feat: 添加模型供应商配置管理页面"
```

---

## Task 13: 修改 AI 工具配置页面

**Files:**
- Modify: `frontend/src/views/admin/AdminAIToolsPage.vue`

- [ ] **Step 1: 修改模型选择为下拉框**

在 `AdminAIToolsPage.vue` 中，找到模型输入框部分并替换：

```vue
<!-- frontend/src/views/admin/AdminAIToolsPage.vue - 替换模型选择部分 -->

<el-form-item label="AI模型">
  <el-select
    v-model="form.model"
    placeholder="请选择AI模型（留空使用默认）"
    clearable
    filterable
    style="width: 100%"
    :loading="loadingModels"
  >
    <el-option-group label="文字对话">
      <el-option
        v-for="model in chatModels"
        :key="model.id"
        :label="`${model.provider_name} - ${model.model_name}`"
        :value="`${model.provider_code}:${model.model_code}`"
      />
    </el-option-group>
    <el-option-group label="图片生成" v-if="form.content_type === 'multimodal' && form.media_type === 'image'">
      <el-option
        v-for="model in imageModels"
        :key="model.id"
        :label="`${model.provider_name} - ${model.model_name}`"
        :value="`${model.provider_code}:${model.model_code}`"
      />
    </el-option-group>
    <el-option-group label="音频生成" v-if="form.content_type === 'multimodal' && form.media_type === 'audio'">
      <el-option
        v-for="model in audioModels"
        :key="model.id"
        :label="`${model.provider_name} - ${model.model_name}`"
        :value="`${model.provider_code}:${model.model_code}`"
      />
    </el-option-group>
    <el-option-group label="视频生成" v-if="form.content_type === 'multimodal' && form.media_type === 'video'">
      <el-option
        v-for="model in videoModels"
        :key="model.id"
        :label="`${model.provider_name} - ${model.model_name}`"
        :value="`${model.provider_code}:${model.model_code}`"
      />
    </el-option-group>
  </el-select>
</el-form-item>
```

- [ ] **Step 2: 添加模型数据加载逻辑**

在 script setup 部分添加：

```typescript
// frontend/src/views/admin/AdminAIToolsPage.vue - 在 script setup 中添加

import { ref, computed } from 'vue'
import type { AvailableModelInfo } from '../../types'

// 可用模型
const availableModels = ref<AvailableModelInfo[]>([])
const loadingModels = ref(false)

// 根据能力类型过滤模型
const chatModels = computed(() => {
  return availableModels.value.filter(m => m.capabilities.includes('chat'))
})

const imageModels = computed(() => {
  return availableModels.value.filter(m => m.capabilities.includes('image'))
})

const audioModels = computed(() => {
  return availableModels.value.filter(m => m.capabilities.includes('audio'))
})

const videoModels = computed(() => {
  return availableModels.value.filter(m => m.capabilities.includes('video'))
})

// 加载可用模型
async function loadAvailableModels() {
  loadingModels.value = true
  try {
    const response = await ApiService.getAvailableModels()
    availableModels.value = response.models
  } catch (error: any) {
    console.error('加载可用模型失败:', error)
  } finally {
    loadingModels.value = false
  }
}

// 在 onMounted 中调用
onMounted(() => {
  loadToolsets()
  loadCategories()
  loadTools()
  loadAvailableModels() // 新增
})
```

- [ ] **Step 3: 处理现有模型值格式**

编辑工具时，需要处理现有的 `provider:model_name` 格式：

```typescript
// frontend/src/views/admin/AdminAIToolsPage.vue - 在 handleEdit 函数中

function handleEdit(tool: AdminAIToolListItem) {
  isEditing.value = true
  Object.assign(form, {
    // ... 其他字段
    model: tool.model || '', // 保持原有格式
    // ...
  })
  // ...
}
```

- [ ] **Step 4: 验证修改**

```bash
cd frontend && npm run dev
```

访问 http://localhost:5173/admin/ai-tools，确认模型选择下拉框正常显示。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/admin/AdminAIToolsPage.vue
git commit -m "feat: AI工具配置模型选择改为下拉框"
```

---

## Task 14: 集成测试

**Files:**
- Create: `frontend/tests/e2e/model-providers.spec.ts`

- [ ] **Step 1: 创建 E2E 测试**

```typescript
// frontend/tests/e2e/model-providers.spec.ts
import { test, expect } from '@playwright/test'

test.describe('模型供应商配置管理', () => {
  test.beforeEach(async ({ page }) => {
    // 登录管理员账号
    await page.goto('http://localhost:5173/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/')
  })

  test('显示模型供应商配置页面', async ({ page }) => {
    await page.goto('http://localhost:5173/admin/model-providers')
    await expect(page.locator('h3')).toContainText('模型供应商配置')
  })

  test('新建供应商', async ({ page }) => {
    await page.goto('http://localhost:5173/admin/model-providers')

    // 点击新建按钮
    await page.click('button:has-text("新建供应商")')

    // 选择供应商
    await page.selectOption('select[placeholder*="请选择供应商"]', 'deepseek')

    // 输入 API Key
    await page.fill('input[type="password"]', 'sk-test-api-key')

    // 提交
    await page.click('button:has-text("确定")')

    // 等待成功消息
    await expect(page.locator('.el-message--success')).toBeVisible()
  })

  test('为供应商添加模型', async ({ page }) => {
    await page.goto('http://localhost:5173/admin/model-providers')

    // 点击模型按钮（假设已有供应商）
    const modelButton = page.locator('button:has-text("模型")').first()
    if (await modelButton.isVisible()) {
      await modelButton.click()

      // 点击添加模型
      await page.click('button:has-text("添加模型")')

      // 选择模型
      await page.selectOption('select[placeholder*="请选择模型"]', 'deepseek-chat')

      // 选择能力
      await page.check('input[type="checkbox"][value="chat"]')

      // 提交
      await page.click('button:has-text("确定")')

      // 等待成功消息
      await expect(page.locator('.el-message--success')).toBeVisible()
    }
  })
})
```

- [ ] **Step 2: 运行测试**

```bash
cd frontend && npm run test:e2e tests/e2e/model-providers.spec.ts --project=chromium
```

Expected: 测试通过

- [ ] **Step 3: 提交**

```bash
git add frontend/tests/e2e/model-providers.spec.ts
git commit -m "test: 添加模型供应商配置 E2E 测试"
```

---

## Task 15: 验证和文档

**Files:**
- Modify: `README.md`
- Modify: `backend/.env.example`

- [ ] **Step 1: 更新 README.md**

在 `README.md` 中添加模型配置说明：

```markdown
## 模型供应商配置

系统支持通过后台配置 AI 模型供应商：

1. 登录管理员账号
2. 进入「管理后台 > 配置管理 > 模型供应商」
3. 点击「新建供应商」，选择内置供应商类型
4. 填入 API Key（可选修改 API 地址）
5. 为供应商添加模型，选择支持的能力
6. 在 AI 工具配置中即可选择已配置的模型

### 支持的供应商

- DeepSeek
- OpenAI
- Kimi (Moonshot)
- 智谱 AI

### 能力类型

- 文字对话 (chat)
- 图片生成 (image)
- 音频生成 (audio)
- 视频生成 (video)
```

- [ ] **Step 2: 生成加密密钥说明**

在 `backend/.env.example` 中添加：

```bash
# API Key 加密密钥（首次部署时必须设置）
# 使用以下命令生成：
# python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
API_KEY_ENCRYPTION_KEY=
```

- [ ] **Step 3: 运行所有测试**

```bash
# 后端测试
cd backend && python3 -m pytest tests/unit/ tests/integration/ -v

# 前端 E2E 测试
cd frontend && npm run test:e2e
```

Expected: 所有测试通过

- [ ] **Step 4: 最终提交**

```bash
git add README.md backend/.env.example
git commit -m "docs: 更新模型供应商配置说明"
```

---

## 完成检查清单

实施完成后，验证以下功能：

- [ ] 数据库表已创建（model_providers, model_configs）
- [ ] 内置供应商和模型定义正确
- [ ] API Key 加密存储正常
- [ ] 管理员可以创建/编辑/删除供应商
- [ ] 管理员可以为供应商添加/编辑/删除模型
- [ ] 可以设置默认供应商
- [ ] AI 工具配置可以从下拉框选择模型
- [ ] AIService 从数据库读取配置正常工作
- [ ] 所有单元测试通过
- [ ] 所有 E2E 测试通过
