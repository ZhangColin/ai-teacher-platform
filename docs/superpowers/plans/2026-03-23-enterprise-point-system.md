# 企业积分系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建企业级积分管理系统，支持多企业独立运营、AI 消费自动扣费、积分充值和消费记录查询

**Architecture:**
- 数据层：新增 4 张表（enterprises, point_transactions, ai_consumptions, model_point_rates），修改 users 表
- 服务层：EnterpriseService（企业管理）、PointService（积分扣费/充值）
- 接口层：后台管理 API + 企业管理 API
- 前端：管理后台新增企业菜单，新增企业独立后台

**Tech Stack:** FastAPI, SQLAlchemy, Vue 3, Element Plus, Pytest

---

## 文件结构概览

### 后端新增文件
```
backend/src/
├── db_models.py                          # 修改：添加企业关联
├── services/
│   ├── enterprise_service.py            # 新增：企业管理服务
│   ├── point_service.py                 # 新增：积分管理服务
│   └── ai_service.py                    # 修改：集成扣费逻辑
├── interfaces/
│   ├── dependencies.py                  # 修改：添加企业管理员权限依赖
│   └── routers/
│       ├── admin/
│       │   └── enterprises.py           # 新增：企业管理 API
│       └── enterprise/                  # 新增目录
│           ├── __init__.py
│           ├── users.py                 # 新增：企业用户 API
│           ├── points.py                # 新增：积分 API
│           └── consumptions.py          # 新增：消费记录 API
└── models.py                             # 修改：添加企业相关 Pydantic 模型
```

### 后端测试文件
```
backend/tests/
├── unit/services/
│   ├── test_enterprise_service.py       # 新增
│   └── test_point_service.py            # 新增
└── integration/routers/
    ├── test_admin_enterprises.py        # 新增
    └── test_enterprise_*.py             # 新增
```

### 前端新增文件
```
frontend/src/
├── types/
│   └── index.ts                          # 修改：添加企业相关类型
├── services/
│   └── apiClient.ts                      # 修改：添加企业相关 API
├── layouts/
│   ├── AdminLayout.vue                   # 修改：添加企业管理菜单
│   └── EnterpriseLayout.vue              # 新增：企业后台布局
├── views/
│   └── admin/
│   │   └── AdminEnterprisesPage.vue      # 新增：企业管理页面
│   └── enterprise/                       # 新增目录
│       ├── EnterpriseDashboardPage.vue   # 新增
│       ├── EnterpriseUsersPage.vue       # 新增
│       ├── PointTransactionsPage.vue     # 新增
│       └── AIConsumptionsPage.vue        # 新增
└── router/index.ts                       # 修改：添加企业后台路由
```

---

## 阶段一：数据模型层（后端）

### Task 1: 扩展数据模型枚举和关系

**Files:**
- Modify: `backend/src/db_models.py`

- [ ] **Step 1: 添加枚举类型**

在 `db_models.py` 顶部添加：

```python
class EnterpriseStatus(enum.Enum):
    """企业状态枚举"""
    active = "active"
    suspended = "suspended"
    archived = "archived"


class PointTransactionType(enum.Enum):
    """积分交易类型枚举"""
    recharge = "recharge"
    gift = "gift"
    consume = "consume"
    refund = "refund"
    adjust = "adjust"


class PointSourceType(enum.Enum):
    """积分来源类型枚举"""
    online_payment = "online_payment"
    offline_payment = "offline_payment"
    admin_gift = "admin_gift"
    admin_adjust = "admin_adjust"
    ai_consume = "ai_consume"
```

- [ ] **Step 2: 添加 EnterpriseModel**

在 `db_models.py` 中添加（在 UserModel 之前）：

```python
class EnterpriseModel(Base):
    """企业数据库模型"""
    __tablename__ = "enterprises"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, comment='企业名称')
    code = Column(String(50), unique=True, nullable=False, index=True, comment='企业代码')
    status = Column(Enum(EnterpriseStatus), nullable=False, default=EnterpriseStatus.active, comment='企业状态')

    # 积分余额
    balance_gratis = Column(Integer, nullable=False, default=0, comment='赠送积分余额（非负）')
    balance_paid = Column(Integer, nullable=False, default=0, comment='充值积分余额（非负）')
    debt_points = Column(Integer, nullable=False, default=0, comment='负债积分（透支金额，非负）')

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    users = relationship("UserModel", back_populates="enterprise")
```

- [ ] **Step 3: 修改 UserModel 添加企业关联**

在 `UserModel` 类中添加字段：

```python
# 在 UserModel 类中，现有字段后添加
enterprise_id = Column(CHAR(36), ForeignKey("enterprises.id"), nullable=False, index=True, comment='所属企业ID')
is_enterprise_admin = Column(Boolean, nullable=False, default=False, index=True, comment='是否企业管理员')

# 在关系部分添加
enterprise = relationship("EnterpriseModel", back_populates="users")
```

- [ ] **Step 4: 添加 PointTransactionModel**

```python
class PointTransactionModel(Base):
    """积分交易记录数据库模型"""
    __tablename__ = "point_transactions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    enterprise_id = Column(CHAR(36), ForeignKey("enterprises.id"), nullable=False, index=True)
    operator_id = Column(CHAR(36), ForeignKey("users.user_id"), nullable=True, comment='操作人')

    type = Column(Enum(PointTransactionType), nullable=False, comment='交易类型')
    source_type = Column(Enum(PointSourceType), nullable=False, comment='来源类型')

    amount = Column(Integer, nullable=False, comment='积分金额（正数）')
    balance_before = Column(Integer, nullable=False, comment='变动前总积分')
    balance_after = Column(Integer, nullable=False, comment='变动后总积分')

    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)

    # 关系
    enterprise = relationship("EnterpriseModel")
```

- [ ] **Step 5: 添加 AIConsumptionModel**

```python
class AIConsumptionModel(Base):
    """AI消费记录数据库模型"""
    __tablename__ = "ai_consumptions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    enterprise_id = Column(CHAR(36), ForeignKey("enterprises.id"), nullable=False, index=True)
    user_id = Column(CHAR(36), ForeignKey("users.user_id"), nullable=False, index=True)
    session_id = Column(CHAR(36), ForeignKey("sessions.session_id"), nullable=False, index=True)
    message_id = Column(CHAR(36), ForeignKey("messages.message_id"), nullable=False, index=True)

    # 模型信息
    model_provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)

    # Token消耗
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)

    # 积分扣减
    gratis_points_used = Column(Integer, nullable=False, default=0)
    paid_points_used = Column(Integer, nullable=False, default=0)
    total_points = Column(Integer, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)

    # 联合索引
    __table_args__ = (
        Index("idx_ai_consumption_enterprise_date", "enterprise_id", "created_at"),
        Index("idx_ai_consumption_user_date", "user_id", "created_at"),
    )
```

- [ ] **Step 6: 添加 ModelPointRateModel**

在文件末尾添加：

```python
class ModelPointRateModel(Base):
    """模型积分汇率数据库模型"""
    __tablename__ = "model_point_rates"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_config_id = Column(CHAR(36), ForeignKey("model_configs.id", ondelete="CASCADE"),
                             nullable=False, unique=True, index=True)

    # 汇率配置
    tokens_per_point = Column(Integer, nullable=False, default=1000, comment='每积分对应token数')
    separate_io = Column(Boolean, nullable=False, default=False, comment='是否区分输入输出')
    tokens_per_point_input = Column(Integer, nullable=True)
    tokens_per_point_output = Column(Integer, nullable=True)

    is_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
```

- [ ] **Step 7: 为 ModelConfigModel 添加反向关系**

在 `ModelConfigModel` 类中添加：

```python
# 在 ModelConfigModel 类中添加
point_rate = relationship("ModelPointRateModel", uselist=False)
```

- [ ] **Step 8: 运行类型检查**

```bash
cd backend && python -m py_compile src/db_models.py
```

预期：无语法错误

- [ ] **Step 9: 创建数据库迁移**

```bash
cd backend && alembic revision --autogenerate -m "add_enterprise_point_system"
```

预期：生成迁移文件

- [ ] **Step 10: 提交**

```bash
git add backend/src/db_models.py
git commit -m "feat: 添加企业积分系统数据模型"
```

---

### Task 2: 创建 Pydantic 请求/响应模型

**Files:**
- Modify: `backend/src/models.py`

- [ ] **Step 1: 添加企业相关枚举**

在 `models.py` 中添加：

```python
class EnterpriseStatus(str, enum.Enum):
    """企业状态枚举"""
    active = "active"
    suspended = "suspended"
    archived = "archived"


class PointTransactionType(str, enum.Enum):
    """积分交易类型枚举"""
    recharge = "recharge"
    gift = "gift"
    consume = "consume"
    refund = "refund"
    adjust = "adjust"


class PointSourceType(str, enum.Enum):
    """积分来源类型枚举"""
    online_payment = "online_payment"
    offline_payment = "offline_payment"
    admin_gift = "admin_gift"
    admin_adjust = "admin_adjust"
```

- [ ] **Step 2: 添加企业相关模型**

```python
class EnterpriseInfo(BaseModel):
    """企业信息"""
    id: str
    name: str
    code: str
    status: EnterpriseStatus
    balance_gratis: int
    balance_paid: int
    debt_points: int
    total_points: int
    user_count: int = 0
    created_at: datetime


class CreateEnterpriseRequest(BaseModel):
    """创建企业请求"""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    initial_gratis: int = Field(0, ge=0)


class UpdateEnterpriseRequest(BaseModel):
    """更新企业请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[EnterpriseStatus] = None


class EnterpriseListResponse(BaseModel):
    """企业列表响应"""
    enterprises: List[EnterpriseInfo]
    total: int
    page: int
    page_size: int
```

- [ ] **Step 3: 添加积分相关模型**

```python
class PointBalanceResponse(BaseModel):
    """积分余额响应"""
    balance_gratis: int
    balance_paid: int
    debt_points: int
    total_points: int


class AddPointsRequest(BaseModel):
    """增加积分请求"""
    amount: int = Field(..., gt=0)
    source_type: PointSourceType
    remark: Optional[str] = None


class TransactionItem(BaseModel):
    """交易记录项"""
    id: str
    type: PointTransactionType
    source_type: PointSourceType
    amount: int
    balance_before: int
    balance_after: int
    remark: Optional[str]
    created_at: datetime


class TransactionListResponse(BaseModel):
    """交易记录列表响应"""
    transactions: List[TransactionItem]
    total: int
    page: int
```

- [ ] **Step 4: 添加消费记录相关模型**

```python
class ConsumptionItem(BaseModel):
    """消费记录项"""
    id: str
    user_id: str
    username: Optional[str]
    model_provider: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    gratis_points_used: int
    paid_points_used: int
    total_points: int
    created_at: datetime


class ConsumptionListResponse(BaseModel):
    """消费记录列表响应"""
    consumptions: List[ConsumptionItem]
    total: int
    page: int
```

- [ ] **Step 5: 添加汇率相关模型**

```python
class ModelPointRateItem(BaseModel):
    """模型汇率项"""
    id: str
    model_config_id: str
    provider_code: str
    model_code: str
    model_name: str
    tokens_per_point: int
    separate_io: bool
    tokens_per_point_input: Optional[int]
    tokens_per_point_output: Optional[int]
    is_enabled: bool


class CreatePointRateRequest(BaseModel):
    """创建汇率配置请求"""
    model_config_id: str
    tokens_per_point: int = Field(1000, gt=0)
    separate_io: bool = False
    tokens_per_point_input: Optional[int] = None
    tokens_per_point_output: Optional[int] = None


class UpdatePointRateRequest(BaseModel):
    """更新汇率配置请求"""
    tokens_per_point: Optional[int] = Field(None, gt=0)
    separate_io: Optional[bool] = None
    tokens_per_point_input: Optional[int] = None
    tokens_per_point_output: Optional[int] = None
    is_enabled: Optional[bool] = None
```

- [ ] **Step 6: 扩展 UserInfo 模型**

在 `UserInfo` 类中添加：

```python
# 在 UserInfo 类中添加
enterprise_id: Optional[str] = None
enterprise_name: Optional[str] = None
is_enterprise_admin: bool = False
```

- [ ] **Step 7: 运行类型检查**

```bash
cd backend && python -m py_compile src/models.py
```

- [ ] **Step 8: 提交**

```bash
git add backend/src/models.py
git commit -m "feat: 添加企业积分系统 Pydantic 模型"
```

---

### Task 2.5: 执行数据库迁移

**注意**: 在开始编写服务层代码之前，需要先执行数据库迁移，创建新表结构。

- [ ] **Step 1: 生成迁移文件**

```bash
cd backend && alembic revision --autogenerate -m "add_enterprise_point_system"
```

- [ ] **Step 2: 检查迁移文件**

查看生成的迁移文件，确认包含了所有新表和字段修改。

- [ ] **Step 3: 执行迁移**

```bash
cd backend && alembic upgrade head
```

- [ ] **Step 4: 验证表结构**

```bash
mysql -u root -p ai_teacher_db -e "SHOW TABLES LIKE '%enterprise%' OR SHOW TABLES LIKE '%point%' OR SHOW TABLES LIKE '%consumption%';"
```

预期输出：应该看到 `enterprises`, `point_transactions`, `ai_consumptions`, `model_point_rates` 四张表

- [ ] **Step 5: 创建默认企业（可选）**

```sql
INSERT INTO enterprises (id, name, code, status, balance_gratis, balance_paid, debt_points, created_at, updated_at)
VALUES ('default-ent-001', '默认企业', 'default', 'active', 10000, 0, 0, NOW(), NOW());
```

- [ ] **Step 6: 提交**

```bash
git add backend/alembic/versions/
git commit -m "feat: 执行企业积分系统数据库迁移"
```

---

## 阶段二：服务层（后端）

### Task 3: 创建 EnterpriseService

**Files:**
- Create: `backend/src/services/enterprise_service.py`
- Test: `backend/tests/unit/services/test_enterprise_service.py`

- [ ] **Step 1: 创建服务文件**

```bash
touch backend/src/services/enterprise_service.py
```

- [ ] **Step 2: 编写测试（先写测试）**

创建 `backend/tests/unit/services/test_enterprise_service.py`：

```python
# -*- coding: utf-8 -*-
"""测试 EnterpriseService"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from src.services.enterprise_service import EnterpriseService
from src.db_models import EnterpriseModel, EnterpriseStatus


@pytest.fixture
def db_session():
    """Mock 数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def enterprise_service(db_session):
    """创建服务实例"""
    return EnterpriseService(db_session)


class TestEnterpriseService:
    """测试 EnterpriseService"""

    def test_create_enterprise(self, enterprise_service, db_session):
        """测试创建企业"""
        # Arrange
        db_session.add.return_value = None
        db_session.commit.return_value = None
        db_session.refresh.return_value = None

        # Act
        result = enterprise_service.create_enterprise(
            name="测试企业",
            code="test_ent",
            initial_gratis=1000
        )

        # Assert
        assert result.name == "测试企业"
        assert result.code == "test_ent"
        assert result.balance_gratis == 1000

    def test_get_enterprise_by_id(self, enterprise_service):
        """测试根据ID获取企业"""
        # Arrange
        mock_enterprise = Mock(spec=EnterpriseModel)
        mock_enterprise.id = "ent_123"
        mock_enterprise.name = "测试企业"

        with patch.object(enterprise_service.db.query, 'filter', return_value=Mock(first=Mock(return_value=mock_enterprise))):
            # Act
            result = enterprise_service.get_enterprise_by_id("ent_123")

            # Assert
            assert result is not None
            assert result.id == "ent_123"

    def test_get_enterprise_by_code(self, enterprise_service):
        """测试根据代码获取企业"""
        # Arrange
        mock_enterprise = Mock(spec=EnterpriseModel)
        mock_enterprise.code = "test_ent"

        with patch.object(enterprise_service.db.query, 'filter', return_value=Mock(first=Mock(return_value=mock_enterprise))):
            # Act
            result = enterprise_service.get_enterprise_by_code("test_ent")

            # Assert
            assert result is not None
            assert result.code == "test_ent"
```

- [ ] **Step 3: 运行测试（预期失败）**

```bash
cd backend && pytest tests/unit/services/test_enterprise_service.py -v
```

预期：FAILED - ImportError: No module named 'enterprise_service'

- [ ] **Step 4: 实现服务**

编写 `backend/src/services/enterprise_service.py`：

```python
# -*- coding: utf-8 -*-
"""企业管理服务"""
import logging
import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from ..db_models import EnterpriseModel, UserModel, EnterpriseStatus

logger = logging.getLogger(__name__)


class EnterpriseService:
    """企业管理服务"""

    def __init__(self, db: Session):
        """
        初始化企业管理服务

        Args:
            db: SQLAlchemy 数据库会话
        """
        self.db = db

    def create_enterprise(
        self,
        name: str,
        code: str,
        initial_gratis: int = 0
    ) -> EnterpriseModel:
        """
        创建新企业

        Args:
            name: 企业名称
            code: 企业代码（唯一）
            initial_gratis: 初始赠送积分

        Returns:
            创建的企业模型

        Raises:
            ValueError: 企业代码已存在
        """
        # 检查代码是否重复
        existing = self.db.query(EnterpriseModel).filter(
            EnterpriseModel.code == code
        ).first()
        if existing:
            raise ValueError(f"企业代码 '{code}' 已存在")

        try:
            enterprise = EnterpriseModel(
                id=str(uuid.uuid4()),
                name=name,
                code=code,
                status=EnterpriseStatus.active,
                balance_gratis=initial_gratis,
                balance_paid=0,
                debt_points=0
            )

            self.db.add(enterprise)
            self.db.commit()
            self.db.refresh(enterprise)

            logger.info(f"创建企业成功: {name} ({code})")
            return enterprise

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建企业失败: {e}")
            raise

    def get_enterprise_by_id(self, enterprise_id: str) -> Optional[EnterpriseModel]:
        """根据ID获取企业"""
        return self.db.query(EnterpriseModel).filter(
            EnterpriseModel.id == enterprise_id
        ).first()

    def get_enterprise_by_code(self, code: str) -> Optional[EnterpriseModel]:
        """根据代码获取企业"""
        return self.db.query(EnterpriseModel).filter(
            EnterpriseModel.code == code
        ).first()

    def get_all_enterprises(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[EnterpriseStatus] = None
    ) -> Tuple[List[EnterpriseModel], int]:
        """
        获取企业列表（分页）

        Returns:
            (企业列表, 总数)
        """
        query = self.db.query(EnterpriseModel)

        if status:
            query = query.filter(EnterpriseModel.status == status)

        total = query.count()

        enterprises = query.order_by(desc(EnterpriseModel.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return enterprises, total

    def update_enterprise(
        self,
        enterprise_id: str,
        name: Optional[str] = None,
        status: Optional[EnterpriseStatus] = None
    ) -> Optional[EnterpriseModel]:
        """更新企业信息"""
        enterprise = self.get_enterprise_by_id(enterprise_id)
        if not enterprise:
            return None

        if name is not None:
            enterprise.name = name
        if status is not None:
            enterprise.status = status

        self.db.commit()
        self.db.refresh(enterprise)
        return enterprise

    def delete_enterprise(self, enterprise_id: str) -> bool:
        """
        删除企业

        注意：如果企业下有用户，无法删除
        """
        enterprise = self.get_enterprise_by_id(enterprise_id)
        if not enterprise:
            return False

        # 检查是否有用户
        user_count = self.db.query(UserModel).filter(
            UserModel.enterprise_id == enterprise_id
        ).count()

        if user_count > 0:
            raise ValueError(f"企业下还有 {user_count} 个用户，无法删除")

        try:
            self.db.delete(enterprise)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除企业失败: {e}")
            raise

    def get_user_enterprise(self, user_id: str) -> Optional[EnterpriseModel]:
        """获取用户所属企业"""
        user = self.db.query(UserModel).filter(
            UserModel.user_id == user_id
        ).first()

        if not user or not user.enterprise_id:
            return None

        return self.get_enterprise_by_id(user.enterprise_id)
```

- [ ] **Step 5: 运行测试**

```bash
cd backend && pytest tests/unit/services/test_enterprise_service.py -v
```

预期：PASS

- [ ] **Step 6: 提交**

```bash
git add backend/src/services/enterprise_service.py backend/tests/unit/services/test_enterprise_service.py
git commit -m "feat: 添加企业管理服务"
```

---

### Task 4: 创建 PointService

**Files:**
- Create: `backend/src/services/point_service.py`
- Test: `backend/tests/unit/services/test_point_service.py`

- [ ] **Step 1: 编写测试**

创建 `backend/tests/unit/services/test_point_service.py`：

```python
# -*- coding: utf-8 -*-
"""测试 PointService"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.point_service import PointService
from src.db_models import EnterpriseModel, PointSourceType, PointTransactionType
from src.models import AddPointsRequest


@pytest.fixture
def db_session():
    """Mock 数据库会话"""
    session = MagicMock()
    session.begin.return_value = MagicMock()
    session.commit.return_value = None
    session.rollback.return_value = None
    return session


@pytest.fixture
def enterprise():
    """Mock 企业"""
    ent = Mock(spec=EnterpriseModel)
    ent.id = "ent_123"
    ent.balance_gratis = 1000
    ent.balance_paid = 2000
    ent.debt_points = 0
    ent.total_points = 3000
    return ent


@pytest.fixture
def point_service(db_session):
    """创建服务实例"""
    return PointService(db_session)


class TestPointService:
    """测试 PointService"""

    def test_check_points_before_request_positive(self, point_service, enterprise):
        """测试积分检查 - 积分充足"""
        # Arrange
        with patch.object(point_service, '_get_user_enterprise', return_value=enterprise):
            # Act
            result = point_service.check_points_before_request("user_123")

            # Assert
            assert result is True

    def test_check_points_before_request_zero(self, point_service):
        """测试积分检查 - 积分为零"""
        # Arrange
        enterprise = Mock(spec=EnterpriseModel)
        enterprise.total_points = 0

        with patch.object(point_service, '_get_user_enterprise', return_value=enterprise):
            # Act
            result = point_service.check_points_before_request("user_123")

            # Assert
            assert result is False

    def test_calculate_points_from_tokens(self, point_service):
        """测试根据 token 计算积分"""
        # Arrange
        with patch.object(point_service, '_get_model_rate', return_value=None):
            # Act - 使用默认汇率 1000
            points = point_service.calculate_points_from_tokens(
                "deepseek", "deepseek-chat", 500, 500
            )

            # Assert - 1000 tokens / 1000 = 1 积分
            assert points == 1

    def test_add_points_to_paid_balance(self, point_service, enterprise):
        """测试增加积分 - 充值积分"""
        # Arrange
        enterprise.balance_paid = 2000
        enterprise.debt_points = 0

        with patch.object(point_service, '_get_enterprise_for_update', return_value=enterprise):
            # Act
            transaction = point_service.add_points(
                enterprise_id="ent_123",
                amount=500,
                source_type=PointSourceType.offline_payment,
                operator_id="admin_123",
                remark="线下充值"
            )

            # Assert
            assert transaction.amount == 500
            assert enterprise.balance_paid == 2500

    def test_add_points_to_gratis_balance(self, point_service, enterprise):
        """测试增加积分 - 赠送积分"""
        # Arrange
        with patch.object(point_service, '_get_enterprise_for_update', return_value=enterprise):
            # Act
            transaction = point_service.add_points(
                enterprise_id="ent_123",
                amount=500,
                source_type=PointSourceType.admin_gift,
                operator_id="admin_123"
            )

            # Assert
            assert enterprise.balance_gratis == 1500

    def test_add_points_pays_debt_first(self, point_service):
        """测试增加积分 - 优先抵扣负债"""
        # Arrange
        enterprise = Mock(spec=EnterpriseModel)
        enterprise.debt_points = 500
        enterprise.balance_gratis = 0
        enterprise.balance_paid = 0
        enterprise.total_points = -500

        with patch.object(point_service, '_get_enterprise_for_update', return_value=enterprise):
            # Act
            transaction = point_service.add_points(
                enterprise_id="ent_123",
                amount=1000,
                source_type=PointSourceType.offline_payment,
                operator_id="admin_123"
            )

            # Assert - 500 抵扣负债，500 加到余额
            assert enterprise.debt_points == 0
            assert enterprise.balance_paid == 500
```

- [ ] **Step 2: 运行测试（预期失败）**

```bash
cd backend && pytest tests/unit/services/test_point_service.py -v
```

预期：FAILED - ImportError

- [ ] **Step 3: 实现服务**

编写 `backend/src/services/point_service.py`：

```python
# -*- coding: utf-8 -*-
"""积分管理服务"""
import logging
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db_models import (
    EnterpriseModel, PointTransactionModel, AIConsumptionModel,
    ModelPointRateModel, ModelConfigModel, ModelProviderModel,
    PointTransactionType, PointSourceType
)
from ..models import AddPointsRequest

logger = logging.getLogger(__name__)


class PointService:
    """积分管理服务"""

    def __init__(self, db: Session):
        """
        初始化积分服务

        Args:
            db: SQLAlchemy 数据库会话
        """
        self.db = db

    def check_points_before_request(self, user_id: str) -> bool:
        """
        请求前检查积分是否足够

        Args:
            user_id: 用户ID

        Returns:
            True 表示可以发起请求，False 表示积分不足
        """
        enterprise = self._get_user_enterprise(user_id)
        if not enterprise:
            raise ValueError("用户未关联企业")

        return enterprise.total_points > 0

    def calculate_points_from_tokens(
        self,
        provider_code: str,
        model_code: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> int:
        """
        根据 token 计算积分

        Args:
            provider_code: 供应商代码
            model_code: 模型代码
            prompt_tokens: 输入 token 数
            completion_tokens: 输出 token 数

        Returns:
            消耗的积分数量
        """
        rate = self._get_model_rate(provider_code, model_code)
        if not rate:
            # 默认汇率
            tokens_per_point = 1000
        else:
            if rate.separate_io:
                # 区分输入输出（暂不实现，使用统一汇率）
                tokens_per_point = rate.tokens_per_point
            else:
                tokens_per_point = rate.tokens_per_point

        total_tokens = prompt_tokens + completion_tokens
        # 向上取整
        points = (total_tokens + tokens_per_point - 1) // tokens_per_point
        return max(1, points)  # 至少消耗1积分

    def add_points(
        self,
        enterprise_id: str,
        amount: int,
        source_type: PointSourceType,
        operator_id: str = None,
        remark: str = None
    ) -> PointTransactionModel:
        """
        增加积分（充值/赠送）

        优先抵扣负债，剩余部分增加余额

        Args:
            enterprise_id: 企业ID
            amount: 增加的积分数量
            source_type: 来源类型
            operator_id: 操作人ID
            remark: 备注

        Returns:
            创建的交易记录
        """
        try:
            with self.db.begin():
                # 1. 获取企业（加锁）
                enterprise = self._get_enterprise_for_update(enterprise_id)

                if not enterprise:
                    raise ValueError("企业不存在")

                balance_before = enterprise.total_points

                # 2. 优先抵扣负债
                if enterprise.debt_points > 0:
                    debt_to_clear = min(enterprise.debt_points, amount)
                    enterprise.debt_points -= debt_to_clear
                    remaining = amount - debt_to_clear
                else:
                    remaining = amount

                # 3. 剩余部分增加余额
                if remaining > 0:
                    if source_type == PointSourceType.admin_gift:
                        enterprise.balance_gratis += remaining
                    else:
                        enterprise.balance_paid += remaining

                # 4. 创建交易记录
                transaction = PointTransactionModel(
                    id=str(uuid.uuid4()),
                    enterprise_id=enterprise_id,
                    operator_id=operator_id,
                    type=PointTransactionType.recharge if source_type != PointSourceType.admin_gift else PointTransactionType.gift,
                    source_type=source_type,
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=enterprise.total_points,
                    remark=remark
                )

                self.db.add(transaction)
                self.db.flush()

                logger.info(
                    f"积分增加成功 - 企业:{enterprise_id}, 金额:{amount}, "
                    f"来源:{source_type}, 操作人:{operator_id}"
                )

                return transaction

        except Exception as e:
            self.db.rollback()
            logger.error(f"增加积分失败: {e}", exc_info=True)
            raise

    def deduct_points(
        self,
        enterprise_id: str,
        user_id: str,
        session_id: str,
        message_id: str,
        model_provider: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        points: int
    ) -> AIConsumptionModel:
        """
        扣减积分（事务）

        先扣赠送积分，再扣充值积分，不够则产生负债

        Args:
            enterprise_id: 企业ID
            user_id: 用户ID
            session_id: 会话ID
            message_id: 消息ID
            model_provider: 模型供应商
            model_name: 模型名称
            prompt_tokens: 输入token数
            completion_tokens: 输出token数
            points: 需扣减的积分

        Returns:
            创建的消费记录
        """
        try:
            with self.db.begin():
                # 1. 获取企业（加锁）
                enterprise = self._get_enterprise_for_update(enterprise_id)

                if not enterprise:
                    raise ValueError("企业不存在")

                # 2. 计算扣减分配
                gratis_to_deduct = min(enterprise.balance_gratis, points)
                paid_to_deduct = points - gratis_to_deduct

                # 3. 执行扣减
                enterprise.balance_gratis -= gratis_to_deduct

                if paid_to_deduct <= enterprise.balance_paid:
                    # 充值积分足够
                    enterprise.balance_paid -= paid_to_deduct
                    actual_paid_used = paid_to_deduct
                else:
                    # 充值积分不够，产生负债
                    remaining = paid_to_deduct - enterprise.balance_paid
                    enterprise.balance_paid = 0
                    enterprise.debt_points += remaining
                    actual_paid_used = enterprise.balance_paid + (paid_to_deduct - remaining)

                # 4. 创建消费记录
                consumption = AIConsumptionModel(
                    id=str(uuid.uuid4()),
                    enterprise_id=enterprise_id,
                    user_id=user_id,
                    session_id=session_id,
                    message_id=message_id,
                    model_provider=model_provider,
                    model_name=model_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    gratis_points_used=gratis_to_deduct,
                    paid_points_used=actual_paid_used,
                    total_points=points
                )

                self.db.add(consumption)
                self.db.flush()

                logger.info(
                    f"积分扣减成功 - 企业:{enterprise_id}, 用户:{user_id}, "
                    f"积分:{points} (赠送:{gratis_to_deduct}, 充值:{actual_paid_used})"
                )

                return consumption

        except Exception as e:
            self.db.rollback()
            logger.error(f"积分扣减失败: {e}", exc_info=True)
            raise

    def get_enterprise_balance(self, enterprise_id: str) -> Optional[dict]:
        """获取企业积分余额"""
        enterprise = self.db.query(EnterpriseModel).filter(
            EnterpriseModel.id == enterprise_id
        ).first()

        if not enterprise:
            return None

        return {
            "balance_gratis": enterprise.balance_gratis,
            "balance_paid": enterprise.balance_paid,
            "debt_points": enterprise.debt_points,
            "total_points": enterprise.total_points
        }

    def get_transactions(
        self,
        enterprise_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple:
        """获取交易记录列表"""
        query = self.db.query(PointTransactionModel).filter(
            PointTransactionModel.enterprise_id == enterprise_id
        )

        total = query.count()

        transactions = query.order_by(
            PointTransactionModel.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return transactions, total

    def get_consumptions(
        self,
        enterprise_id: str,
        page: int = 1,
        page_size: int = 20,
        user_id: str = None,
        start_date = None,
        end_date = None
    ) -> tuple:
        """获取消费记录列表"""
        query = self.db.query(AIConsumptionModel).filter(
            AIConsumptionModel.enterprise_id == enterprise_id
        )

        if user_id:
            query = query.filter(AIConsumptionModel.user_id == user_id)
        if start_date:
            query = query.filter(AIConsumptionModel.created_at >= start_date)
        if end_date:
            query = query.filter(AIConsumptionModel.created_at <= end_date)

        total = query.count()

        consumptions = query.order_by(
            AIConsumptionModel.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return consumptions, total

    # 私有方法

    def _get_user_enterprise(self, user_id: str) -> Optional[EnterpriseModel]:
        """获取用户所属企业"""
        from ..db_models import UserModel

        user = self.db.query(UserModel).filter(
            UserModel.user_id == user_id
        ).first()

        if not user or not user.enterprise_id:
            return None

        return self.db.query(EnterpriseModel).filter(
            EnterpriseModel.id == user.enterprise_id
        ).first()

    def _get_enterprise_for_update(self, enterprise_id: str) -> Optional[EnterpriseModel]:
        """获取企业（加锁）"""
        return self.db.query(EnterpriseModel).filter(
            EnterpriseModel.id == enterprise_id
        ).with_for_update().first()

    def _get_model_rate(self, provider_code: str, model_code: str) -> Optional[ModelPointRateModel]:
        """获取模型汇率配置"""
        return self.db.query(ModelPointRateModel).join(
            ModelConfigModel, ModelPointRateModel.model_config_id == ModelConfigModel.id
        ).join(
            ModelProviderModel, ModelConfigModel.provider_id == ModelProviderModel.id
        ).filter(
            ModelProviderModel.provider_code == provider_code,
            ModelConfigModel.model_code == model_code,
            ModelPointRateModel.is_enabled == True
        ).first()
```

- [ ] **Step 4: 运行测试**

```bash
cd backend && pytest tests/unit/services/test_point_service.py -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add backend/src/services/point_service.py backend/tests/unit/services/test_point_service.py
git commit -m "feat: 添加积分管理服务"
```

---

### Task 5: 修改 AIService 集成扣费

**Files:**
- Modify: `backend/src/services/ai_service.py`

- [ ] **Step 1: 在 chat_stream 方法末尾添加扣费逻辑**

找到 `chat_stream` 方法中 yield usage 信息的位置，在 yield 之前添加扣费逻辑：

```python
# 在流结束时 yield usage 信息之前（约第888行）
if usage_info:
    # 计算并扣减积分
    try:
        from .point_service import PointService
        point_service = PointService(self.db)

        # 计算积分
        points = point_service.calculate_points_from_tokens(
            provider_code=provider,
            model_code=model_name,
            prompt_tokens=usage_info['prompt_tokens'],
            completion_tokens=usage_info['completion_tokens']
        )

        # 获取当前用户信息（从上下文获取）
        # 注意：需要修改 chat_stream 方法签名接收 user_id, session_id, message_id
        # 这里先记录日志，实际扣费在接口层完成
        logger.info(f"AI调用完成 - 模型:{provider}:{model_name}, Tokens:{usage_info['total_tokens']}, 积分:{points}")

        # 将积分信息添加到 usage 中
        usage_info['points_deducted'] = points

    except Exception as e:
        logger.error(f"积分计算失败: {e}")
```

- [ ] **Step 2: 提交**

```bash
git add backend/src/services/ai_service.py
git commit -m "feat: AI 服务集成积分计算"
```

---

## 阶段三：接口层（后端）

### Task 6: 添加权限依赖

**Files:**
- Modify: `backend/src/interfaces/dependencies.py`

- [ ] **Step 1: 添加企业管理员权限依赖**

在 `dependencies.py` 中添加：

```python
async def require_enterprise_admin(
    current_user: Annotated[UserInfo, Depends(get_current_user)]
) -> UserInfo:
    """
    企业管理员权限验证

    Args:
        current_user: 当前登录用户

    Returns:
        UserInfo: 当前用户信息

    Raises:
        HTTPException: 用户不是企业管理员
    """
    if not current_user.is_enterprise_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要企业管理员权限"
        )

    return current_user
```

- [ ] **Step 2: 提交**

```bash
git add backend/src/interfaces/dependencies.py
git commit -m "feat: 添加企业管理员权限依赖"
```

---

### Task 7: 创建企业管理 API

**Files:**
- Create: `backend/src/interfaces/routers/admin/enterprises.py`
- Test: `backend/tests/integration/routers/test_admin_enterprises.py`

- [ ] **Step 1: 创建路由文件**

```bash
touch backend/src/interfaces/routers/admin/enterprises.py
```

- [ ] **Step 2: 编写企业管理 API**

```python
# -*- coding: utf-8 -*-
"""企业管理路由（后台管理员）"""
import logging
from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from src.models import (
    UserInfo,
    EnterpriseInfo,
    CreateEnterpriseRequest,
    UpdateEnterpriseRequest,
    EnterpriseListResponse,
    AddPointsRequest,
    TransactionListResponse,
)
from src.db_models import EnterpriseStatus, PointSourceType
from src.database import get_db
from src.interfaces.dependencies import require_admin
from src.services.enterprise_service import EnterpriseService
from src.services.point_service import PointService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/enterprises", tags=["管理员-企业管理"])


def _model_to_response(model) -> EnterpriseInfo:
    """将数据库模型转换为响应"""
    from src.services.enterprise_service import EnterpriseService
    # 计算用户数
    user_count = 0  # TODO: 实现用户数统计

    return EnterpriseInfo(
        id=str(model.id),
        name=model.name,
        code=model.code,
        status=model.status,
        balance_gratis=model.balance_gratis,
        balance_paid=model.balance_paid,
        debt_points=model.debt_points,
        total_points=model.total_points,
        user_count=user_count,
        created_at=model.created_at
    )


@router.get("", response_model=EnterpriseListResponse)
async def get_enterprises(
    page: int = 1,
    page_size: int = 20,
    status: Optional[EnterpriseStatus] = None,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取企业列表"""
    if page_size > 100:
        page_size = 100

    service = EnterpriseService(db)
    enterprises, total = service.get_all_enterprises(page, page_size, status)

    return EnterpriseListResponse(
        enterprises=[_model_to_response(e) for e in enterprises],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("", response_model=EnterpriseInfo, status_code=status.HTTP_201_CREATED)
async def create_enterprise(
    request: CreateEnterpriseRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建企业"""
    service = EnterpriseService(db)
    try:
        enterprise = service.create_enterprise(
            name=request.name,
            code=request.code,
            initial_gratis=request.initial_gratis
        )
        return _model_to_response(enterprise)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{enterprise_id}", response_model=EnterpriseInfo)
async def get_enterprise(
    enterprise_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取企业详情"""
    service = EnterpriseService(db)
    enterprise = service.get_enterprise_by_id(enterprise_id)
    if not enterprise:
        raise HTTPException(status_code=404, detail="企业不存在")
    return _model_to_response(enterprise)


@router.patch("/{enterprise_id}", response_model=EnterpriseInfo)
async def update_enterprise(
    enterprise_id: str,
    request: UpdateEnterpriseRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """更新企业信息"""
    service = EnterpriseService(db)
    enterprise = service.update_enterprise(
        enterprise_id,
        name=request.name,
        status=request.status
    )
    if not enterprise:
        raise HTTPException(status_code=404, detail="企业不存在")
    return _model_to_response(enterprise)


@router.delete("/{enterprise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_enterprise(
    enterprise_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除企业"""
    service = EnterpriseService(db)
    try:
        success = service.delete_enterprise(enterprise_id)
        if not success:
            raise HTTPException(status_code=404, detail="企业不存在")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{enterprise_id}/add-points")
async def add_points_to_enterprise(
    enterprise_id: str,
    request: AddPointsRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """手动增加积分（充值/赠送）"""
    point_service = PointService(db)
    try:
        transaction = point_service.add_points(
            enterprise_id=enterprise_id,
            amount=request.amount,
            source_type=request.source_type,
            operator_id=current_user.user_id,
            remark=request.remark
        )
        return {"message": "积分增加成功", "transaction_id": str(transaction.id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **Step 3: 注册路由**

修改 `backend/src/main.py`，添加路由：

```python
from src.interfaces.routers.admin import enterprises
app.include_router(enterprises.router)
```

- [ ] **Step 4: 提交**

```bash
git add backend/src/interfaces/routers/admin/enterprises.py backend/src/main.py
git commit -m "feat: 添加企业管理 API"
```

---

### Task 8: 创建企业后台 API

**Files:**
- Create: `backend/src/interfaces/routers/enterprise/__init__.py`
- Create: `backend/src/interfaces/routers/enterprise/users.py`
- Create: `backend/src/interfaces/routers/enterprise/points.py`
- Create: `backend/src/interfaces/routers/enterprise/consumptions.py`

- [ ] **Step 1: 创建企业路由目录和初始化文件**

```bash
mkdir -p backend/src/interfaces/routers/enterprise
touch backend/src/interfaces/routers/enterprise/__init__.py
```

编写 `__init__.py`：

```python
# -*- coding: utf-8 -*-
"""企业后台路由"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/enterprise", tags=["企业后台"])
```

- [ ] **Step 2: 创建积分 API**

创建 `backend/src/interfaces/routers/enterprise/points.py`：

```python
# -*- coding: utf-8 -*-
"""积分管理路由（企业后台）"""
import logging
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from src.models import UserInfo, PointBalanceResponse, TransactionListResponse
from src.database import get_db
from src.interfaces.dependencies import get_current_user, require_enterprise_admin
from src.services.point_service import PointService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/enterprise/points", tags=["企业-积分"])


@router.get("/balance", response_model=PointBalanceResponse)
async def get_balance(
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取企业积分余额"""
    point_service = PointService(db)
    balance = point_service.get_enterprise_balance(current_user.enterprise_id)

    if not balance:
        raise HTTPException(status_code=404, detail="企业不存在")

    return PointBalanceResponse(**balance)


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    page: int = 1,
    page_size: int = 20,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取积分交易记录"""
    if page_size > 100:
        page_size = 100

    point_service = PointService(db)
    transactions, total = point_service.get_transactions(
        current_user.enterprise_id, page, page_size
    )

    from src.models import TransactionItem
    items = [
        TransactionItem(
            id=str(t.id),
            type=t.type,
            source_type=t.source_type,
            amount=t.amount,
            balance_before=t.balance_before,
            balance_after=t.balance_after,
            remark=t.remark,
            created_at=t.created_at
        )
        for t in transactions
    ]

    return TransactionListResponse(
        transactions=items,
        total=total,
        page=page
    )
```

- [ ] **Step 3: 创建消费记录 API**

创建 `backend/src/interfaces/routers/enterprise/consumptions.py`：

```python
# -*- coding: utf-8 -*-
"""消费记录路由（企业后台）"""
import logging
from typing import Annotated, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from src.models import UserInfo, ConsumptionListResponse
from src.database import get_db
from src.interfaces.dependencies import require_enterprise_admin
from src.services.point_service import PointService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/enterprise/consumptions", tags=["企业-消费记录"])


@router.get("", response_model=ConsumptionListResponse)
async def get_consumptions(
    page: int = 1,
    page_size: int = 20,
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取 AI 消费记录"""
    if page_size > 100:
        page_size = 100

    point_service = PointService(db)
    consumptions, total = point_service.get_consumptions(
        current_user.enterprise_id, page, page_size, user_id, start_date, end_date
    )

    from src.models import ConsumptionItem
    items = [
        ConsumptionItem(
            id=str(c.id),
            user_id=c.user_id,
            username=None,  # TODO: 关联查询用户名
            model_provider=c.model_provider,
            model_name=c.model_name,
            prompt_tokens=c.prompt_tokens,
            completion_tokens=c.completion_tokens,
            total_tokens=c.total_tokens,
            gratis_points_used=c.gratis_points_used,
            paid_points_used=c.paid_points_used,
            total_points=c.total_points,
            created_at=c.created_at
        )
        for c in consumptions
    ]

    return ConsumptionListResponse(
        consumptions=items,
        total=total,
        page=page
    )
```

- [ ] **Step 4: 注册路由**

修改 `backend/src/main.py`，添加企业路由：

```python
from src.interfaces.routers import enterprise
app.include_router(enterprise.router)
```

- [ ] **Step 5: 提交**

```bash
git add backend/src/interfaces/routers/enterprise/ backend/src/main.py
git commit -m "feat: 添加企业后台 API"
```

---

### Task 8: 创建企业用户管理 API

**Files:**
- Create: `backend/src/interfaces/routers/enterprise/users.py`

- [ ] **Step 1: 创建用户管理 API**

创建 `backend/src/interfaces/routers/enterprise/users.py`：

```python
# -*- coding: utf-8 -*-
"""企业用户管理路由（企业后台）"""
import logging
from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from src.models import UserInfo
from src.database import get_db
from src.interfaces.dependencies import require_enterprise_admin
from src.services.user_service import UserService
from src.services.enterprise_service import EnterpriseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/enterprise/users", tags=["企业-用户管理"])


@router.get("")
async def get_users(
    page: int = 1,
    page_size: int = 20,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取企业用户列表"""
    if page_size > 100:
        page_size = 100

    from src.db_models import UserModel
    query = db.query(UserModel).filter(
        UserModel.enterprise_id == current_user.enterprise_id
    )

    total = query.count()

    from sqlalchemy import desc
    users = query.order_by(desc(UserModel.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    from src.models import UserListItem
    items = [
        UserListItem(
            user_id=u.user_id,
            username=u.username,
            nickname=u.nickname or u.username,
            email=u.email,
            phone=u.phone,
            avatar=u.avatar,
            is_admin=u.is_admin,
            created_at=u.created_at
        )
        for u in users
    ]

    return {"users": items, "total": total, "page": page}


@router.post("")
async def create_user(
    request: dict,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """创建企业用户"""
    user_service = UserService()
    try:
        user = user_service.create_user(
            username=request["username"],
            nickname=request.get("nickname"),
            email=request.get("email"),
            password=request["password"],
            phone=request.get("phone"),
            is_enterprise_admin=False
        )

        # 关联到当前企业
        from src.db_models import UserModel
        user_model = db.query(UserModel).filter(
            UserModel.user_id == user.user_id
        ).first()
        if user_model:
            user_model.enterprise_id = current_user.enterprise_id
            db.commit()

        return {"user_id": user.user_id, "message": "创建成功"}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Annotated[UserInfo, Depends(require_enterprise_admin)] = None,
    db: Session = Depends(get_db)
):
    """删除企业用户"""
    from src.db_models import UserModel
    user = db.query(UserModel).filter(
        UserModel.user_id == user_id,
        UserModel.enterprise_id == current_user.enterprise_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    try:
        db.delete(user)
        db.commit()
        return {"message": "删除成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 2: 注册路由**

修改 `backend/src/interfaces/routers/enterprise/__init__.py`：

```python
from fastapi import APIRouter
from . import users, points, consumptions

router = APIRouter(prefix="/api/v1/enterprise", tags=["企业后台"])
router.include_router(users.router)
router.include_router(points.router)
router.include_router(consumptions.router)
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/interfaces/routers/enterprise/users.py backend/src/interfaces/routers/enterprise/__init__.py
git commit -m "feat: 添加企业用户管理 API"
```

---

### Task 9: 修改 Chat 接口集成积分检查和扣费

**Files:**
- Modify: `backend/src/interfaces/routers/tools/chat.py`

- [ ] **Step 1: 在 AI 请求前检查积分**

找到聊天接口的 POST 方法，在调用 AI 服务前添加积分检查：

```python
# 在 chat_stream 方法开始处，获取用户信息后
from src.services.point_service import PointService

# 检查积分
point_service = PointService(db)
if not point_service.check_points_before_request(current_user.user_id):
    raise HTTPException(
        status_code=403,
        detail="积分不足，请联系企业管理员充值"
    )
```

- [ ] **Step 2: 在 AI 响应后扣减积分**

在流式结束后，记录消费信息：

```python
# 在流结束后，获取 usage_info 后
if usage_info:
    try:
        from src.services.point_service import PointService
        point_service = PointService(db)

        points = point_service.calculate_points_from_tokens(
            provider_code=usage_info.get('model_provider', ''),
            model_code=usage_info.get('model_name', ''),
            prompt_tokens=usage_info.get('prompt_tokens', 0),
            completion_tokens=usage_info.get('completion_tokens', 0)
        )

        # 扣减积分
        consumption = point_service.deduct_points(
            enterprise_id=current_user.enterprise_id,
            user_id=current_user.user_id,
            session_id=session_id,
            message_id=message_id,
            model_provider=usage_info.get('model_provider', ''),
            model_name=usage_info.get('model_name', ''),
            prompt_tokens=usage_info.get('prompt_tokens', 0),
            completion_tokens=usage_info.get('completion_tokens', 0),
            points=points
        )

        logger.info(f"积分扣减完成 - 消耗:{points}（赠送:{consumption.gratis_points_used}, 充值:{consumption.paid_points_used}）")

    except Exception as e:
        logger.error(f"积分扣减失败: {e}")
        # 不阻塞响应，但记录错误
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/interfaces/routers/tools/chat.py
git commit -m "feat: 集成积分检查和扣费到聊天接口"
```

---

## 阶段四：前端（Vue）

### Task 9: 添加前端类型定义

**Files:**
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: 添加企业相关类型**

在 `types/index.ts` 中添加：

```typescript
// 企业状态枚举
export type EnterpriseStatus = 'active' | 'suspended' | 'archived'

// 积分交易类型枚举
export type PointTransactionType = 'recharge' | 'gift' | 'consume' | 'refund' | 'adjust'

// 积分来源类型枚举
export type PointSourceType = 'online_payment' | 'offline_payment' | 'admin_gift' | 'admin_adjust'

// 企业信息
export interface EnterpriseInfo {
  id: string
  name: string
  code: string
  status: EnterpriseStatus
  balance_gratis: number
  balance_paid: number
  debt_points: number
  total_points: number
  user_count: number
  created_at: string
}

// 创建企业请求
export interface CreateEnterpriseRequest {
  name: string
  code: string
  initial_gratis?: number
}

// 积分余额响应
export interface PointBalanceResponse {
  balance_gratis: number
  balance_paid: number
  debt_points: number
  total_points: number
}

// 交易记录项
export interface TransactionItem {
  id: string
  type: PointTransactionType
  source_type: PointSourceType
  amount: number
  balance_before: number
  balance_after: number
  remark?: string
  created_at: string
}

// 消费记录项
export interface ConsumptionItem {
  id: string
  user_id: string
  username?: string
  model_provider: string
  model_name: string
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  gratis_points_used: number
  paid_points_used: number
  total_points: number
  created_at: string
}

// 扩展 UserInfo
export interface UserInfo {
  // ... 现有字段
  enterprise_id?: string
  enterprise_name?: string
  is_enterprise_admin?: boolean
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/types/index.ts
git commit -m "feat: 添加企业相关类型定义"
```

---

### Task 10: 添加前端 API 客户端方法

**Files:**
- Modify: `frontend/src/services/apiClient.ts`

- [ ] **Step 1: 添加企业相关 API 方法**

在 `apiClient.ts` 中添加：

```typescript
// ========== 企业管理 API（管理员） ==========

export async function getEnterpriseList(page = 1, pageSize = 20, status?: EnterpriseStatus) {
  const params: any = { page, page_size: pageSize }
  if (status) params.status = status
  const response = await api.get('/admin/enterprises', { params })
  return response.data as EnterpriseListResponse
}

export async function createEnterprise(data: CreateEnterpriseRequest) {
  const response = await api.post('/admin/enterprises', data)
  return response.data as EnterpriseInfo
}

export async function updateEnterprise(id: string, data: Partial<CreateEnterpriseRequest & { status?: EnterpriseStatus }>) {
  const response = await api.patch(`/admin/enterprises/${id}`, data)
  return response.data as EnterpriseInfo
}

export async function deleteEnterprise(id: string) {
  await api.delete(`/admin/enterprises/${id}`)
}

export async function addPointsToEnterprise(enterpriseId: string, amount: number, sourceType: PointSourceType, remark?: string) {
  const response = await api.post(`/admin/enterprises/${enterpriseId}/add-points`, {
    amount,
    source_type: sourceType,
    remark
  })
  return response.data
}

// ========== 企业后台 API ==========

export async function getPointBalance() {
  const response = await api.get('/enterprise/points/balance')
  return response.data as PointBalanceResponse
}

export async function getTransactions(page = 1, pageSize = 20) {
  const response = await api.get('/enterprise/points/transactions', {
    params: { page, page_size: pageSize }
  })
  return response.data as TransactionListResponse
}

export async function getConsumptions(page = 1, pageSize = 20, userId?: string) {
  const params: any = { page, page_size: pageSize }
  if (userId) params.user_id = userId
  const response = await api.get('/enterprise/consumptions', { params })
  return response.data as ConsumptionListResponse
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/services/apiClient.ts
git commit -m "feat: 添加企业相关 API 客户端方法"
```

---

### Task 11: 更新管理后台布局

**Files:**
- Modify: `frontend/src/layouts/AdminLayout.vue`

- [ ] **Step 1: 添加企业管理菜单项**

在侧边栏菜单中，用户管理菜单项之前添加：

```vue
<el-menu-item index="/admin/users">
  <el-icon><User /></el-icon>
  <span>用户管理</span>
</el-menu-item>

<!-- 新增：企业管理 -->
<el-sub-menu index="enterprise">
  <template #title>
    <el-icon><OfficeBuilding /></el-icon>
    <span>企业管理</span>
  </template>
  <el-menu-item index="/admin/enterprises">企业列表</el-menu-item>
</el-sub-menu>

<!-- 在 script 部分添加图标导入 -->
import { OfficeBuilding } from '@element-plus/icons-vue'
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/layouts/AdminLayout.vue
git commit -m "feat: 管理后台添加企业管理菜单"
```

---

### Task 12: 创建企业管理页面

**Files:**
- Create: `frontend/src/views/admin/AdminEnterprisesPage.vue`

- [ ] **Step 1: 创建页面文件**

```bash
touch frontend/src/views/admin/AdminEnterprisesPage.vue
```

- [ ] **Step 2: 编写页面组件**

参考 `AdminUsersPage.vue` 的结构，实现企业列表、创建、编辑、删除、充值功能：

```vue
<template>
  <div class="admin-enterprises-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>企业管理</h3>
          <el-button type="primary" @click="handleCreate">创建企业</el-button>
        </div>
      </template>

      <!-- 企业列表表格 -->
      <el-table :data="enterprises" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="企业名称" width="200" />
        <el-table-column prop="code" label="企业代码" width="150" />
        <el-table-column prop="total_points" label="总积分" width="120">
          <template #default="{ row }">
            {{ formatNumber(row.total_points) }}
          </template>
        </el-table-column>
        <el-table-column prop="balance_paid" label="充值积分" width="120">
          <template #default="{ row }">
            {{ formatNumber(row.balance_paid) }}
          </template>
        </el-table-column>
        <el-table-column prop="balance_gratis" label="赠送积分" width="120">
          <template #default="{ row }">
            {{ formatNumber(row.balance_gratis) }}
          </template>
        </el-table-column>
        <el-table-column prop="user_count" label="用户数" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleAddPoints(row)">充值/赠送</el-button>
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @current-change="loadEnterprises"
        @size-change="handleSizeChange"
        style="margin-top: 16px"
      />
    </el-card>

    <!-- 创建企业对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建企业" width="500px">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="100px">
        <el-form-item label="企业名称" prop="name">
          <el-input v-model="createForm.name" />
        </el-form-item>
        <el-form-item label="企业代码" prop="code">
          <el-input v-model="createForm.code" />
        </el-form-item>
        <el-form-item label="初始赠送积分">
          <el-input-number v-model="createForm.initial_gratis" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateSubmit" :loading="submitting">创建</el-button>
      </template>
    </el-dialog>

    <!-- 充值/赠送对话框 -->
    <el-dialog v-model="pointsDialogVisible" title="增加积分" width="450px">
      <el-form :model="pointsForm" :rules="pointsRules" ref="pointsFormRef" label-width="100px">
        <el-form-item label="积分数量" prop="amount">
          <el-input-number v-model="pointsForm.amount" :min="1" />
        </el-form-item>
        <el-form-item label="来源类型" prop="source_type">
          <el-radio-group v-model="pointsForm.source_type">
            <el-radio label="offline_payment">线下打款</el-radio>
            <el-radio label="admin_gift">后台赠送</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="pointsForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pointsDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePointsSubmit" :loading="submitting">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { ApiService, type EnterpriseInfo, type CreateEnterpriseRequest } from '../../services'

const enterprises = ref<EnterpriseInfo[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 创建企业
const createDialogVisible = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive<CreateEnterpriseRequest>({
  name: '',
  code: '',
  initial_gratis: 0
})

// 充值/赠送
const pointsDialogVisible = ref(false)
const pointsFormRef = ref<FormInstance>()
const currentEnterprise = ref<EnterpriseInfo | null>(null)
const pointsForm = reactive({
  amount: 1000,
  source_type: 'offline_payment' as const,
  remark: ''
})

const submitting = ref(false)

const createRules: FormRules = {
  name: [{ required: true, message: '请输入企业名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入企业代码', trigger: 'blur' }]
}

const pointsRules: FormRules = {
  amount: [{ required: true, message: '请输入积分数量', trigger: 'blur' }],
  source_type: [{ required: true, message: '请选择来源类型', trigger: 'change' }]
}

function formatNumber(n: number) {
  return n.toLocaleString()
}

function statusText(status: string) {
  const map = { active: '正常', suspended: '暂停', archived: '归档' }
  return map[status] || status
}

async function loadEnterprises() {
  loading.value = true
  try {
    const response = await ApiService.getEnterpriseList(currentPage.value, pageSize.value)
    enterprises.value = response.enterprises
    total.value = response.total
  } catch (error: any) {
    ElMessage.error(error.message || '加载企业列表失败')
  } finally {
    loading.value = false
  }
}

function handleSizeChange() {
  currentPage.value = 1
  loadEnterprises()
}

function handleCreate() {
  Object.assign(createForm, { name: '', code: '', initial_gratis: 0 })
  createFormRef.value?.clearValidate()
  createDialogVisible.value = true
}

async function handleCreateSubmit() {
  if (!createFormRef.value) return
  await createFormRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await ApiService.createEnterprise(createForm)
      ElMessage.success('创建企业成功')
      createDialogVisible.value = false
      loadEnterprises()
    } catch (error: any) {
      ElMessage.error(error.message || '创建企业失败')
    } finally {
      submitting.value = false
    }
  })
}

function handleAddPoints(enterprise: EnterpriseInfo) {
  currentEnterprise.value = enterprise
  Object.assign(pointsForm, { amount: 1000, source_type: 'offline_payment', remark: '' })
  pointsFormRef.value?.clearValidate()
  pointsDialogVisible.value = true
}

async function handlePointsSubmit() {
  if (!pointsFormRef.value || !currentEnterprise.value) return
  await pointsFormRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await ApiService.addPointsToEnterprise(
        currentEnterprise.value.id,
        pointsForm.amount,
        pointsForm.source_type,
        pointsForm.remark
      )
      ElMessage.success('积分增加成功')
      pointsDialogVisible.value = false
      loadEnterprises()
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

function handleEdit(enterprise: EnterpriseInfo) {
  ElMessage.info('编辑功能待实现')
}

async function handleDelete(enterprise: EnterpriseInfo) {
  try {
    await ElMessageBox.confirm(`确定要删除企业 "${enterprise.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await ApiService.deleteEnterprise(enterprise.id)
    ElMessage.success('删除企业成功')
    loadEnterprises()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除企业失败')
    }
  }
}

onMounted(() => {
  loadEnterprises()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header h3 {
  margin: 0;
}
</style>
```

- [ ] **Step 3: 添加路由**

修改 `frontend/src/router/index.ts`，添加路由：

```typescript
{
  path: '/admin/enterprises',
  component: () => import('../views/admin/AdminEnterprisesPage.vue'),
  meta: { requiresAuth: true, requiresAdmin: true }
}
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/admin/AdminEnterprisesPage.vue frontend/src/router/index.ts
git commit -m "feat: 添加企业管理页面"
```

---

### Task 13: 创建企业后台布局和 Dashboard

**Files:**
- Create: `frontend/src/layouts/EnterpriseLayout.vue`
- Create: `frontend/src/views/enterprise/EnterpriseDashboardPage.vue`

- [ ] **Step 1: 创建企业后台目录**

```bash
mkdir -p frontend/src/views/enterprise
```

- [ ] **Step 2: 创建企业后台布局**

创建 `frontend/src/layouts/EnterpriseLayout.vue`：

```vue
<template>
  <div class="enterprise-layout">
    <!-- 顶部栏 -->
    <el-header class="enterprise-header">
      <div class="header-left">
        <Logo />
        <span class="enterprise-badge">{{ userInfo?.enterprise_name || '企业后台' }}</span>
      </div>
      <div class="header-right">
        <el-button type="primary" link @click="goToHome">返回前台</el-button>
        <el-divider direction="vertical" />
        <span class="user-info">{{ userInfo?.nickname || userInfo?.username }}</span>
        <el-button type="primary" link @click="handleLogout">退出</el-button>
      </div>
    </el-header>

    <el-container class="enterprise-main-container">
      <!-- 侧边栏导航 -->
      <el-aside width="200px" class="enterprise-aside">
        <el-menu :default-active="currentRoute" class="enterprise-menu" router>
          <el-menu-item index="/enterprise">
            <el-icon><DataBoard /></el-icon>
            <span>概览</span>
          </el-menu-item>
          <el-menu-item index="/enterprise/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/enterprise/transactions">
            <el-icon><List /></el-icon>
            <span>充值记录</span>
          </el-menu-item>
          <el-menu-item index="/enterprise/consumptions">
            <el-icon><DataAnalysis /></el-icon>
            <span>消费记录</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="enterprise-content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataBoard, User, List, DataAnalysis } from '@element-plus/icons-vue'
import Logo from '../components/Logo.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const userInfo = computed(() => authStore.user)
const currentRoute = computed(() => route.path)

function goToHome() {
  router.push('/')
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.enterprise-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f0f2f5;
}

.enterprise-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background-color: rgba(255, 255, 255, 0.98);
  border-bottom: 1px solid #e8e8e8;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.enterprise-badge {
  padding: 4px 12px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  font-size: 13px;
  font-weight: 600;
  border-radius: 4px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.enterprise-main-container {
  flex: 1;
  overflow: hidden;
}

.enterprise-aside {
  background-color: #fff;
  border-right: 1px solid #e8e8e8;
}

.enterprise-content {
  padding: 24px;
  overflow-y: auto;
  background-color: #f0f2f5;
}
</style>
```

- [ ] **Step 3: 创建 Dashboard 页面**

创建 `frontend/src/views/enterprise/EnterpriseDashboardPage.vue`：

```vue
<template>
  <div class="enterprise-dashboard">
    <!-- 企业信息卡片 -->
    <el-card class="enterprise-info">
      <div class="info-header">
        <h2>{{ enterpriseName }}</h2>
        <el-tag type="success">正常</el-tag>
      </div>
      <div class="info-meta">
        <span>用户数：{{ userCount }}</span>
      </div>
    </el-card>

    <!-- 积分卡片组 -->
    <el-row :gutter="20" class="points-cards">
      <el-col :span="8">
        <el-card class="point-card total">
          <div class="label">总积分</div>
          <div class="value">{{ formatNumber(balance.total_points) }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="point-card paid">
          <div class="label">充值积分</div>
          <div class="value">{{ formatNumber(balance.balance_paid) }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="point-card gratis">
          <div class="label">赠送积分</div>
          <div class="value">{{ formatNumber(balance.balance_gratis) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作按钮区 -->
    <el-card class="actions">
      <el-button type="primary" size="large">在线充值</el-button>
      <el-button size="large" @click="$router.push('/enterprise/transactions')">充值记录</el-button>
      <el-button size="large" @click="$router.push('/enterprise/consumptions')">消费记录</el-button>
    </el-card>

    <!-- 最近消费记录 -->
    <el-card class="recent-consumptions">
      <template #header>
        <div class="card-header">
          <span>最近消费记录</span>
          <el-link type="primary" @click="$router.push('/enterprise/consumptions')">查看全部 →</el-link>
        </div>
      </template>
      <el-table :data="recentConsumptions" v-loading="loading">
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="model_name" label="模型" width="150" />
        <el-table-column prop="total_tokens" label="Token" width="100" />
        <el-table-column prop="total_points" label="积分" width="100" />
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../../stores/authStore'
import { ApiService, type ConsumptionItem } from '../../services'

const authStore = useAuthStore()

const enterpriseName = computed(() => authStore.user?.enterprise_name || '未知企业')
const userCount = ref(0)

const balance = ref({
  balance_gratis: 0,
  balance_paid: 0,
  debt_points: 0,
  total_points: 0
})

const recentConsumptions = ref<ConsumptionItem[]>([])
const loading = ref(false)

function formatNumber(n: number) {
  return n.toLocaleString()
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

async function loadBalance() {
  try {
    const data = await ApiService.getPointBalance()
    balance.value = data
  } catch (error) {
    console.error('加载积分余额失败', error)
  }
}

async function loadRecentConsumptions() {
  loading.value = true
  try {
    const data = await ApiService.getConsumptions(1, 10)
    recentConsumptions.value = data.consumptions
  } catch (error) {
    console.error('加载消费记录失败', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadBalance()
  loadRecentConsumptions()
})
</script>

<style scoped>
.enterprise-info {
  margin-bottom: 20px;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.info-header h2 {
  margin: 0;
}

.info-meta span {
  color: #666;
}

.points-cards {
  margin-bottom: 20px;
}

.point-card {
  text-align: center;
}

.point-card .label {
  color: #666;
  margin-bottom: 8px;
}

.point-card .value {
  font-size: 32px;
  font-weight: 600;
}

.point-card.total .value {
  color: #409eff;
}

.point-card.paid .value {
  color: #67c23a;
}

.point-card.gratis .value {
  color: #e6a23c;
}

.actions {
  margin-bottom: 20px;
  text-align: center;
}

.recent-consumptions .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

- [ ] **Step 4: 添加企业后台路由**

修改 `frontend/src/router/index.ts`，添加企业后台路由：

```typescript
{
  path: '/enterprise',
  component: () => import('../layouts/EnterpriseLayout.vue'),
  meta: { requiresAuth: true, requiresEnterpriseAdmin: true },
  children: [
    {
      path: '',
      component: () => import('../views/enterprise/EnterpriseDashboardPage.vue')
    },
    {
      path: 'users',
      component: () => import('../views/enterprise/EnterpriseUsersPage.vue')
    },
    {
      path: 'transactions',
      component: () => import('../views/enterprise/PointTransactionsPage.vue')
    },
    {
      path: 'consumptions',
      component: () => import('../views/enterprise/AIConsumptionsPage.vue')
    }
  ]
}
```

- [ ] **Step 5: 创建占位页面**

```bash
touch frontend/src/views/enterprise/EnterpriseUsersPage.vue
touch frontend/src/views/enterprise/PointTransactionsPage.vue
touch frontend/src/views/enterprise/AIConsumptionsPage.vue
```

- [ ] **Step 6: 提交**

```bash
git add frontend/src/layouts/EnterpriseLayout.vue frontend/src/views/enterprise/ frontend/src/router/index.ts
git commit -m "feat: 添加企业后台布局和 Dashboard"
```

---

## 阶段五：集成与测试

### Task 15: 运行测试验证

- [ ] **Step 1: 运行后端单元测试**

```bash
cd backend && pytest tests/unit/services/test_enterprise_service.py tests/unit/services/test_point_service.py -v
```

预期：PASS

- [ ] **Step 2: 运行后端集成测试**

```bash
cd backend && pytest tests/integration/routers/test_admin_enterprises.py -v
```

预期：PASS

- [ ] **Step 3: 前端类型检查**

```bash
cd frontend && npx vue-tsc --noEmit
```

预期：无类型错误

- [ ] **Step 4: 前端测试**

```bash
cd frontend && npm run test
```

预期：PASS

---

### Task 16: 添加前端路由守卫

**Files:**
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: 添加企业管理员权限检查**

在路由守卫中添加企业管理员检查：

```typescript
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  const isAuthenticated = authStore.isAuthenticated

  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
    return
  }

  if (to.meta.requiresAdmin && authStore.user?.is_admin !== true) {
    next('/')
    return
  }

  // 新增：企业管理员权限检查
  if (to.meta.requiresEnterpriseAdmin && authStore.user?.is_enterprise_admin !== true) {
    next('/')
    return
  }

  next()
})
```

- [ ] **Step 2: 更新路由 meta**

为 `/enterprise` 路由添加 `requiresEnterpriseAdmin: true`。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/router/index.ts
git commit -m "feat: 添加企业管理员路由守卫"
```

---

### Task 17: 手动测试验收

- [ ] **Step 1: 启动后端服务**

```bash
cd backend && python -m src.main
```

- [ ] **Step 2: 启动前端服务**

```bash
cd frontend && npm run dev
```

- [ ] **Step 3: 验收检查清单**

1. 后台管理员可以访问 `/admin/enterprises` 查看企业列表
2. 后台管理员可以创建新企业
3. 后台管理员可以给企业手动充值/赠送积分
4. 企业管理员可以访问 `/enterprise` 查看 Dashboard
5. Dashboard 显示正确的积分余额
6. 用户使用 AI 时自动扣减积分（日志验证）

---

## 验收标准

1. ✅ 后台管理员可以创建/编辑/删除企业
2. ✅ 后台管理员可以给企业手动充值/赠送积分
3. ✅ 企业管理员可以查看积分余额和充值记录
4. ✅ 企业管理员可以查看 AI 消费记录
5. ✅ 用户使用 AI 时自动扣减积分
6. ✅ 积分不足时无法发起 AI 请求
7. ✅ 汇率配置可以按模型单独设置

---

## 后续扩展（不在本计划范围）

- 在线支付接口（工商银行 + 微信/支付宝扫码）
- 积分明细导出功能
- 企业配额管理
- 消费预警通知
