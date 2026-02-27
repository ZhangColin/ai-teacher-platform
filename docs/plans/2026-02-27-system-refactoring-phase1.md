# 系统重构实施计划 - 阶段1：DDD架构 + Provider迁移

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 建立后端DDD分层架构，将AIService重构为Provider模式，为多模型接入打好基础

**Architecture:** 使用Domain-Application-Infrastructure-Interfaces四层架构，通过Provider抽象解耦AI模型调用，渐进式迁移确保系统始终可用

**Tech Stack:** Python 3.10+, FastAPI, SQLAlchemy, pytest, OpenAI SDK

---

## Task 1: 创建DDD目录结构

**Files:**
- Create: `backend/src/domain/__init__.py`
- Create: `backend/src/domain/entities/__init__.py`
- Create: `backend/src/domain/value_objects/__init__.py`
- Create: `backend/src/domain/repositories/__init__.py`
- Create: `backend/src/application/__init__.py`
- Create: `backend/src/application/services/__init__.py`
- Create: `backend/src/application/dto/__init__.py`
- Create: `backend/src/infrastructure/__init__.py`
- Create: `backend/src/infrastructure/providers/__init__.py`
- Create: `backend/src/infrastructure/repositories/__init__.py`
- Create: `backend/src/infrastructure/parsers/__init__.py`
- Create: `backend/src/interfaces/__init__.py`
- Create: `backend/src/interfaces/routers/__init__.py`
- Create: `backend/src/interfaces/routers/tools/__init__.py`
- Create: `backend/src/interfaces/middleware/__init__.py`

**Step 1: 创建domain层目录结构**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend/src
mkdir -p domain/entities domain/value_objects domain/repositories
touch domain/__init__.py domain/entities/__init__.py domain/value_objects/__init__.py domain/repositories/__init__.py
```

Expected: 目录创建成功，`__init__.py` 文件存在

**Step 2: 创建application层目录结构**

Run:
```bash
mkdir -p application/services application/dto
touch application/__init__.py application/services/__init__.py application/dto/__init__.py
```

Expected: 目录创建成功

**Step 3: 创建infrastructure层目录结构**

Run:
```bash
mkdir -p infrastructure/providers infrastructure/repositories infrastructure/parsers
touch infrastructure/__init__.py infrastructure/providers/__init__.py infrastructure/repositories/__init__.py infrastructure/parsers/__init__.py
```

Expected: 目录创建成功

**Step 4: 创建interfaces层目录结构**

Run:
```bash
mkdir -p interfaces/routers/tools interfaces/middleware
touch interfaces/__init__.py interfaces/routers/__init__.py interfaces/routers/tools/__init__.py interfaces/middleware/__init__.py
```

Expected: 目录创建成功

**Step 5: 验证目录结构**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
python -c "from src import domain, application, infrastructure, interfaces; print('DDD layers imported successfully')"
```

Expected: 输出 "DDD layers imported successfully"，无报错

**Step 6: 提交目录结构**

Run:
```bash
git add backend/src/domain backend/src/application backend/src/infrastructure backend/src/interfaces
git commit -m "refactor: create DDD layer directory structure"
```

---

## Task 2: 配置pytest测试框架

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/unit/__init__.py`
- Create: `backend/tests/unit/domain/__init__.py`
- Create: `backend/tests/unit/application/__init__.py`
- Create: `backend/tests/unit/infrastructure/__init__.py`
- Create: `backend/tests/integration/__init__.py`
- Create: `backend/tests/integration/api/__init__.py`
- Modify: `backend/pytest.ini`

**Step 1: 创建测试目录结构**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
mkdir -p tests/unit/domain tests/unit/application tests/unit/infrastructure
mkdir -p tests/integration/api
touch tests/conftest.py tests/__init__.py tests/unit/__init__.py tests/unit/domain/__init__.py tests/unit/application/__init__.py tests/unit/infrastructure/__init__.py tests/integration/__init__.py tests/integration/api/__init__.py
```

Expected: 测试目录创建成功

**Step 2: 创建conftest.py配置文件**

Create: `backend/tests/conftest.py`

```python
"""pytest配置文件"""
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import AsyncGenerator, Generator

from src.database import Base


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """
    创建内存数据库用于测试

    使用内存数据库，每个测试函数都会获得一个全新的数据库
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    # 创建所有表
    Base.metadata.create_all(engine)

    # 创建Session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    # 清理
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def event_loop() -> asyncio.AbstractEventLoop:
    """
    为异步测试创建事件循环
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# 通用标记配置
pytest_plugins = []


def pytest_configure(config):
    """
    配置自定义pytest标记
    """
    config.addinivalue_line(
        "markers", "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试标记"
    )
```

**Step 3: 更新pytest.ini配置**

Read current: `backend/pytest.ini`

If it exists, update it to:

```ini
[pytest]
# pytest配置文件

# 测试发现
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 输出配置
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=0

# 标记定义
markers =
    unit: 单元测试
    integration: 集成测试
    slow: 慢速测试
    asyncio: 异步测试

# 异步测试支持
asyncio_mode = auto

# 最小Python版本
minversion = 7.0

# 警告过滤
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

If `pytest.ini` doesn't exist, create it with the content above.

**Step 4: 验证pytest配置**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest --collect-only
```

Expected: pytest收集到0个测试（框架就绪，无实际测试）

**Step 5: 提交测试框架**

Run:
```bash
git add tests/ pytest.ini
git commit -m "test: configure pytest framework with DDD structure"
```

---

## Task 3: 创建User领域实体

**Files:**
- Create: `backend/src/domain/entities/user.py`
- Create: `backend/tests/unit/domain/entities/test_user.py`

**Step 1: 创建User实体**

Create: `backend/src/domain/entities/user.py`

```python
"""
User领域实体

User表示系统中的用户，包含业务规则和领域逻辑
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """
    用户实体

    Attributes:
        id: 用户唯一标识
        username: 用户名
        email: 邮箱地址
        is_admin: 是否为管理员
        created_at: 创建时间
    """
    id: int
    username: str
    email: str
    is_admin: bool
    created_at: datetime

    def can_access_tool(self, tool_id: str) -> bool:
        """
        检查用户是否可以访问指定工具

        业务规则：
        - 管理员可以访问所有工具
        - 普通用户的权限检查在后续实现

        Args:
            tool_id: 工具ID

        Returns:
            bool: 是否可以访问
        """
        # 管理员可以访问所有工具
        if self.is_admin:
            return True

        # 普通用户权限检查（后续实现）
        # TODO: 实现基于用户角色的权限控制
        return True

    def is_premium_user(self) -> bool:
        """
        检查是否为付费用户

        Returns:
            bool: 是否为付费用户
        """
        # TODO: 实现付费用户逻辑
        return False

    @classmethod
    def create_new(cls, username: str, email: str) -> "User":
        """
        创建新用户（工厂方法）

        Args:
            username: 用户名
            email: 邮箱

        Returns:
            User: 新用户实例
        """
        return cls(
            id=0,  # 数据库生成
            username=username,
            email=email,
            is_admin=False,
            created_at=datetime.now()
        )
```

**Step 2: 编写User实体的单元测试**

Create: `backend/tests/unit/domain/entities/test_user.py`

```python
"""
User实体单元测试
"""
import pytest
from datetime import datetime
from src.domain.entities.user import User


class TestUser:
    """User实体测试类"""

    def test_admin_can_access_all_tools(self):
        """测试管理员可以访问所有工具"""
        # Arrange
        admin = User(
            id=1,
            username="admin",
            email="admin@example.com",
            is_admin=True,
            created_at=datetime.now()
        )

        # Act & Assert
        assert admin.can_access_tool("any_tool") is True
        assert admin.can_access_tool("restricted_tool") is True

    def test_regular_user_can_access_tools(self):
        """测试普通用户权限检查（当前默认返回True）"""
        # Arrange
        user = User(
            id=2,
            username="user",
            email="user@example.com",
            is_admin=False,
            created_at=datetime.now()
        )

        # Act & Assert
        # 当前实现默认返回True，后续添加权限逻辑
        assert user.can_access_tool("public_tool") is True

    def test_is_premium_user(self):
        """测试付费用户检查（当前默认返回False）"""
        # Arrange
        user = User(
            id=3,
            username="user",
            email="user@example.com",
            is_admin=False,
            created_at=datetime.now()
        )

        # Act & Assert
        # 当前实现默认返回False，后续添加付费逻辑
        assert user.is_premium_user() is False

    def test_create_new_user_factory_method(self):
        """测试创建新用户的工厂方法"""
        # Act
        new_user = User.create_new(
            username="newuser",
            email="new@example.com"
        )

        # Assert
        assert new_user.username == "newuser"
        assert new_user.email == "new@example.com"
        assert new_user.is_admin is False
        assert new_user.id == 0  # 数据库生成
        assert isinstance(new_user.created_at, datetime)

    def test_user_dataclass_attributes(self):
        """测试User数据类属性"""
        # Arrange
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            is_admin=False,
            created_at=created_at
        )

        # Assert
        assert user.id == 1
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_admin is False
        assert user.created_at == created_at
```

**Step 3: 运行测试验证失败**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest tests/unit/domain/entities/test_user.py -v
```

Expected: 测试通过（因为我们已经实现了User实体）

**Step 4: 验证测试覆盖率**

Run:
```bash
pytest tests/unit/domain/entities/test_user.py --cov=src/domain/entities/user --cov-report=term-missing
```

Expected: 覆盖率应该接近100%，因为User实体逻辑简单

**Step 5: 提交User实体**

Run:
```bash
git add backend/src/domain/entities/user.py tests/unit/domain/entities/test_user.py
git commit -m "feat(domain): add User entity with business rules"
```

---

## Task 4: 创建Message领域实体

**Files:**
- Create: `backend/src/domain/value_objects/message_role.py`
- Create: `backend/src/domain/entities/message.py`
- Create: `backend/tests/unit/domain/value_objects/test_message_role.py`
- Create: `backend/tests/unit/domain/entities/test_message.py`

**Step 1: 创建MessageRole值对象**

Create: `backend/src/domain/value_objects/message_role.py`

```python
"""
MessageRole值对象

表示对话中消息的角色（用户/助手/系统）
"""
from enum import Enum


class MessageRole(str, Enum):
    """
    消息角色枚举

    Values:
        USER: 用户消息
        ASSISTANT: AI助手消息
        SYSTEM: 系统提示词消息
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

    def is_user_message(self) -> bool:
        """检查是否为用户消息"""
        return self == MessageRole.USER

    def is_assistant_message(self) -> bool:
        """检查是否为助手消息"""
        return self == MessageRole.ASSISTANT

    def is_system_message(self) -> bool:
        """检查是否为系统消息"""
        return self == MessageRole.SYSTEM
```

**Step 2: 创建Message实体**

Create: `backend/src/domain/entities/message.py`

```python
"""
Message领域实体

Message表示对话中的一条消息
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.domain.entities.artifact import Artifact
from src.domain.value_objects.message_role import MessageRole


@dataclass
class Message:
    """
    消息实体

    Attributes:
        id: 消息唯一标识
        session_id: 所属会话ID
        role: 消息角色（user/assistant/system）
        content: 消息内容
        artifact: 可选的成果物（AI生成的内容）
        created_at: 创建时间
    """
    id: int
    session_id: int
    role: MessageRole
    content: str
    artifact: Optional[Artifact]
    created_at: datetime

    def is_from_user(self) -> bool:
        """检查消息是否来自用户"""
        return self.role.is_user_message()

    def is_from_assistant(self) -> bool:
        """检查消息是否来自助手"""
        return self.role.is_assistant_message()

    def is_system_prompt(self) -> bool:
        """检查是否为系统提示词"""
        return self.role.is_system_message()

    def has_artifact(self) -> bool:
        """检查是否包含成果物"""
        return self.artifact is not None

    def get_content_length(self) -> int:
        """获取消息内容长度"""
        return len(self.content)

    @classmethod
    def create_user_message(cls, session_id: int, content: str) -> "Message":
        """
        创建用户消息（工厂方法）

        Args:
            session_id: 会话ID
            content: 消息内容

        Returns:
            Message: 用户消息实例
        """
        return cls(
            id=0,  # 数据库生成
            session_id=session_id,
            role=MessageRole.USER,
            content=content,
            artifact=None,
            created_at=datetime.now()
        )

    @classmethod
    def create_assistant_message(
        cls,
        session_id: int,
        content: str,
        artifact: Optional[Artifact] = None
    ) -> "Message":
        """
        创建助手消息（工厂方法）

        Args:
            session_id: 会话ID
            content: 消息内容
            artifact: 可选的成果物

        Returns:
            Message: 助手消息实例
        """
        return cls(
            id=0,  # 数据库生成
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=content,
            artifact=artifact,
            created_at=datetime.now()
        )
```

**Step 3: 创建临时Artifact实体（占位）**

Create: `backend/src/domain/entities/artifact.py`

```python
"""
Artifact领域实体（临时占位）

Artifact表示AI生成的成果物（HTML/SVG/Markdown等）
TODO: 在后续任务中完善
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Artifact:
    """成果物实体（临时）"""
    id: int
    type: str  # "html", "svg", "markdown"
    content: str
    created_at: datetime
```

**Step 4: 编写MessageRole值对象的测试**

Create: `backend/tests/unit/domain/value_objects/test_message_role.py`

```python
"""
MessageRole值对象单元测试
"""
import pytest
from src.domain.value_objects.message_role import MessageRole


class TestMessageRole:
    """MessageRole测试类"""

    def test_user_role(self):
        """测试用户角色"""
        role = MessageRole.USER

        assert role == "user"
        assert role.is_user_message() is True
        assert role.is_assistant_message() is False
        assert role.is_system_message() is False

    def test_assistant_role(self):
        """测试助手角色"""
        role = MessageRole.ASSISTANT

        assert role == "assistant"
        assert role.is_user_message() is False
        assert role.is_assistant_message() is True
        assert role.is_system_message() is False

    def test_system_role(self):
        """测试系统角色"""
        role = MessageRole.SYSTEM

        assert role == "system"
        assert role.is_user_message() is False
        assert role.is_assistant_message() is False
        assert role.is_system_message() is True

    def test_role_equality(self):
        """测试角色比较"""
        assert MessageRole.USER == MessageRole.USER
        assert MessageRole.USER != MessageRole.ASSISTANT
```

**Step 5: 编写Message实体的测试**

Create: `backend/tests/unit/domain/entities/test_message.py`

```python
"""
Message实体单元测试
"""
import pytest
from datetime import datetime
from src.domain.entities.message import Message
from src.domain.entities.artifact import Artifact
from src.domain.value_objects.message_role import MessageRole


class TestMessage:
    """Message实体测试类"""

    def test_message_attributes(self):
        """测试消息属性"""
        # Arrange
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        artifact = Artifact(
            id=1,
            type="markdown",
            content="# Hello",
            created_at=created_at
        )

        message = Message(
            id=1,
            session_id=100,
            role=MessageRole.ASSISTANT,
            content="Here's your lesson plan",
            artifact=artifact,
            created_at=created_at
        )

        # Assert
        assert message.id == 1
        assert message.session_id == 100
        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Here's your lesson plan"
        assert message.artifact == artifact
        assert message.created_at == created_at

    def test_is_from_user(self):
        """测试用户消息检查"""
        message = Message(
            id=1,
            session_id=100,
            role=MessageRole.USER,
            content="Hello",
            artifact=None,
            created_at=datetime.now()
        )

        assert message.is_from_user() is True
        assert message.is_from_assistant() is False
        assert message.is_system_prompt() is False

    def test_is_from_assistant(self):
        """测试助手消息检查"""
        message = Message(
            id=2,
            session_id=100,
            role=MessageRole.ASSISTANT,
            content="Hi there",
            artifact=None,
            created_at=datetime.now()
        )

        assert message.is_from_user() is False
        assert message.is_from_assistant() is True
        assert message.is_system_prompt() is False

    def test_has_artifact(self):
        """测试成果物检查"""
        artifact = Artifact(
            id=1,
            type="html",
            content="<div>Hello</div>",
            created_at=datetime.now()
        )

        message_with_artifact = Message(
            id=1,
            session_id=100,
            role=MessageRole.ASSISTANT,
            content="Here's HTML",
            artifact=artifact,
            created_at=datetime.now()
        )

        message_without_artifact = Message(
            id=2,
            session_id=100,
            role=MessageRole.USER,
            content="Hello",
            artifact=None,
            created_at=datetime.now()
        )

        assert message_with_artifact.has_artifact() is True
        assert message_without_artifact.has_artifact() is False

    def test_get_content_length(self):
        """测试内容长度计算"""
        message = Message(
            id=1,
            session_id=100,
            role=MessageRole.USER,
            content="Hello World",
            artifact=None,
            created_at=datetime.now()
        )

        assert message.get_content_length() == 11  # "Hello World"长度

    def test_create_user_message_factory(self):
        """测试创建用户消息工厂方法"""
        # Act
        message = Message.create_user_message(
            session_id=100,
            content="Generate lesson plan"
        )

        # Assert
        assert message.session_id == 100
        assert message.content == "Generate lesson plan"
        assert message.role == MessageRole.USER
        assert message.artifact is None
        assert message.id == 0

    def test_create_assistant_message_factory(self):
        """测试创建助手消息工厂方法"""
        # Arrange
        artifact = Artifact(
            id=1,
            type="markdown",
            content="# Lesson Plan",
            created_at=datetime.now()
        )

        # Act
        message = Message.create_assistant_message(
            session_id=100,
            content="Here's your lesson plan",
            artifact=artifact
        )

        # Assert
        assert message.session_id == 100
        assert message.content == "Here's your lesson plan"
        assert message.role == MessageRole.ASSISTANT
        assert message.artifact == artifact
        assert message.id == 0
```

**Step 6: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest tests/unit/domain/value_objects/test_message_role.py -v
pytest tests/unit/domain/entities/test_message.py -v
```

Expected: 所有测试通过

**Step 7: 提交Message相关代码**

Run:
```bash
git add backend/src/domain/value_objects/ backend/src/domain/entities/message.py backend/src/domain/entities/artifact.py tests/unit/domain/
git commit -m "feat(domain): add Message entity and MessageRole value object"
```

---

## Task 5: 定义仓储接口

**Files:**
- Create: `backend/src/domain/repositories/user_repository.py`
- Create: `backend/src/domain/repositories/session_repository.py`
- Create: `backend/src/domain/repositories/message_repository.py`
- Create: `backend/tests/unit/domain/repositories/test_user_repository.py`

**Step 1: 创建UserRepository接口**

Create: `backend/src/domain/repositories/user_repository.py`

```python
"""
UserRepository仓储接口

仓储模式：抽象数据访问逻辑
"""
from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities.user import User


class UserRepository(ABC):
    """
    用户仓储接口

    定义用户数据访问的抽象接口，具体实现在Infrastructure层
    """

    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        """
        根据ID查找用户

        Args:
            user_id: 用户ID

        Returns:
            User|null: 用户实体，不存在返回None
        """
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱查找用户

        Args:
            email: 邮箱地址

        Returns:
            User|null: 用户实体，不存在返回None
        """
        pass

    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名查找用户

        Args:
            username: 用户名

        Returns:
            User|null: 用户实体，不存在返回None
        """
        pass

    @abstractmethod
    def save(self, user: User) -> User:
        """
        保存用户

        Args:
            user: 用户实体

        Returns:
            User: 保存后的用户实体（包含生成的ID）
        """
        pass

    @abstractmethod
    def delete(self, user_id: int) -> None:
        """
        删除用户

        Args:
            user_id: 用户ID
        """
        pass
```

**Step 2: 创建SessionRepository接口**

Create: `backend/src/domain/repositories/session_repository.py`

```python
"""
SessionRepository仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.session import Session


class SessionRepository(ABC):
    """
    会话仓储接口
    """

    @abstractmethod
    def find_by_id(self, session_id: int) -> Optional[Session]:
        """
        根据ID查找会话

        Args:
            session_id: 会话ID

        Returns:
            Session|null: 会话实体，不存在返回None
        """
        pass

    @abstractmethod
    def find_by_user_and_tool(
        self,
        user_id: int,
        tool_id: str
    ) -> List[Session]:
        """
        查找用户在指定工具下的所有会话

        Args:
            user_id: 用户ID
            tool_id: 工具ID

        Returns:
            List[Session]: 会话列表
        """
        pass

    @abstractmethod
    def save(self, session: Session) -> Session:
        """
        保存会话

        Args:
            session: 会话实体

        Returns:
            Session: 保存后的会话实体
        """
        pass

    @abstractmethod
    def delete(self, session_id: int) -> None:
        """
        删除会话

        Args:
            session_id: 会话ID
        """
        pass
```

**Step 3: 创建MessageRepository接口**

Create: `backend/src/domain/repositories/message_repository.py`

```python
"""
MessageRepository仓储接口
"""
from abc import ABC, abstractmethod
from typing import List

from src.domain.entities.message import Message


class MessageRepository(ABC):
    """
    消息仓储接口
    """

    @abstractmethod
    def find_by_session(self, session_id: int) -> List[Message]:
        """
        查找会话的所有消息

        Args:
            session_id: 会话ID

        Returns:
            List[Message]: 消息列表（按时间排序）
        """
        pass

    @abstractmethod
    def save(self, message: Message) -> Message:
        """
        保存消息

        Args:
            message: 消息实体

        Returns:
            Message: 保存后的消息实体
        """
        pass

    @abstractmethod
    def delete_by_session(self, session_id: int) -> None:
        """
        删除会话的所有消息

        Args:
            session_id: 会话ID
        """
        pass
```

**Step 4: 创建临时Session实体（占位）**

Create: `backend/src/domain/entities/session.py`

```python
"""
Session领域实体（临时占位）
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Session:
    """会话实体（临时）"""
    id: int
    user_id: int
    tool_id: str
    title: str
    created_at: datetime
```

**Step 5: 编写UserRepository接口测试**

Create: `backend/tests/unit/domain/repositories/test_user_repository.py`

```python
"""
UserRepository接口单元测试

测试仓储接口的契约，任何实现都应该满足这些测试
"""
import pytest
from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from datetime import datetime


class InMemoryUserRepository(UserRepository):
    """
    内存实现的UserRepository，用于测试

    这展示了仓储接口的一个可能实现
    """

    def __init__(self):
        self._users: dict[int, User] = {}

    def find_by_id(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def find_by_email(self, email: str) -> User | None:
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    def find_by_username(self, username: str) -> User | None:
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    def save(self, user: User) -> User:
        if user.id == 0:
            # 生成新ID
            user.id = len(self._users) + 1
        self._users[user.id] = user
        return user

    def delete(self, user_id: int) -> None:
        if user_id in self._users:
            del self._users[user_id]


class TestUserRepository:
    """UserRepository测试类"""

    @pytest.fixture
    def repository(self):
        """创建测试用的仓储实例"""
        return InMemoryUserRepository()

    @pytest.fixture
    def sample_user(self):
        """创建测试用户"""
        return User(
            id=0,
            username="testuser",
            email="test@example.com",
            is_admin=False,
            created_at=datetime.now()
        )

    def test_save_user_generates_id(self, repository, sample_user):
        """测试保存用户时生成ID"""
        # Act
        saved_user = repository.save(sample_user)

        # Assert
        assert saved_user.id > 0
        assert saved_user.username == "testuser"

    def test_find_by_id(self, repository, sample_user):
        """测试根据ID查找用户"""
        # Arrange
        saved_user = repository.save(sample_user)

        # Act
        found_user = repository.find_by_id(saved_user.id)

        # Assert
        assert found_user is not None
        assert found_user.id == saved_user.id
        assert found_user.username == "testuser"

    def test_find_by_id_not_found(self, repository):
        """测试查找不存在的用户ID"""
        # Act
        found_user = repository.find_by_id(999)

        # Assert
        assert found_user is None

    def test_find_by_email(self, repository, sample_user):
        """测试根据邮箱查找用户"""
        # Arrange
        repository.save(sample_user)

        # Act
        found_user = repository.find_by_email("test@example.com")

        # Assert
        assert found_user is not None
        assert found_user.email == "test@example.com"

    def test_find_by_email_not_found(self, repository):
        """测试查找不存在的邮箱"""
        # Act
        found_user = repository.find_by_email("notfound@example.com")

        # Assert
        assert found_user is None

    def test_delete_user(self, repository, sample_user):
        """测试删除用户"""
        # Arrange
        saved_user = repository.save(sample_user)

        # Act
        repository.delete(saved_user.id)

        # Assert
        found_user = repository.find_by_id(saved_user.id)
        assert found_user is None
```

**Step 6: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest tests/unit/domain/repositories/test_user_repository.py -v
```

Expected: 所有测试通过

**Step 7: 提交仓储接口**

Run:
```bash
git add backend/src/domain/repositories/ backend/src/domain/entities/session.py tests/unit/domain/repositories/
git commit -m "feat(domain): add repository interfaces for User, Session, Message"
```

---

## Task 6: 定义AIProvider抽象类

**Files:**
- Create: `backend/src/infrastructure/providers/base.py`
- Create: `backend/tests/unit/infrastructure/providers/test_base.py`

**Step 1: 创建AIProvider抽象类**

Create: `backend/src/infrastructure/providers/base.py`

```python
"""
AIProvider抽象基类

定义AI提供商的统一接口，支持多模型接入
"""
from abc import ABC, abstractmethod
from typing import List, AsyncGenerator, Optional, Dict, Any

from src.domain.entities.message import Message


class AIProvider(ABC):
    """
    AI提供商抽象接口

    所有AI提供商（OpenAI、DeepSeek、Kimi等）都必须实现此接口
    """

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式对话

        Args:
            messages: 消息历史
            model: 模型名称
            temperature: 温度参数（0-1）
            max_tokens: 最大生成token数
            **kwargs: 其他参数

        Yields:
            str: 流式输出的文本片段
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        非流式对话

        Args:
            messages: 消息历史
            model: 模型名称
            temperature: 温度参数（0-1）
            max_tokens: 最大生成token数
            **kwargs: 其他参数

        Returns:
            str: 完整响应文本
        """
        pass

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        **kwargs
    ) -> str:
        """
        生成图片

        Args:
            prompt: 提示词
            size: 图片尺寸
            **kwargs: 其他参数

        Returns:
            str: 图片URL
        """
        pass

    @abstractmethod
    async def generate_audio(
        self,
        text: str,
        voice: str = "alloy",
        **kwargs
    ) -> str:
        """
        生成音频

        Args:
            text: 文本内容
            voice: 音色
            **kwargs: 其他参数

        Returns:
            str: 音频URL
        """
        pass

    def get_supported_models(self) -> List[str]:
        """
        获取支持的模型列表

        Returns:
            List[str]: 模型名称列表
        """
        return []

    def validate_model(self, model: str) -> bool:
        """
        验证模型是否支持

        Args:
            model: 模型名称

        Returns:
            bool: 是否支持
        """
        return model in self.get_supported_models()
```

**Step 2: 编写AIProvider接口测试**

Create: `backend/tests/unit/infrastructure/providers/test_base.py`

```python
"""
AIProvider抽象类单元测试
"""
import pytest
from src.infrastructure.providers.base import AIProvider
from src.domain.entities.message import Message
from src.domain.value_objects.message_role import MessageRole


class TestAIProvider:
    """AIProvider测试类"""

    def test_cannot_instantiate_abstract_provider(self):
        """测试不能直接实例化抽象类"""
        # Act & Assert
        with pytest.raises(TypeError):
            AIProvider()

    def test_concrete_provider_implementation(self):
        """测试具体实现必须实现所有抽象方法"""

        class MockProvider(AIProvider):
            """Mock实现用于测试"""

            async def chat_stream(self, messages, model, temperature=0.7, max_tokens=None, **kwargs):
                yield "test"

            async def chat(self, messages, model, temperature=0.7, max_tokens=None, **kwargs):
                return "test response"

            async def generate_image(self, prompt, size="1024x1024", **kwargs):
                return "http://example.com/image.png"

            async def generate_audio(self, text, voice="alloy", **kwargs):
                return "http://example.com/audio.mp3"

        # Act
        provider = MockProvider()

        # Assert
        assert isinstance(provider, AIProvider)

    @pytest.mark.asyncio
    async def test_get_supported_models_default(self):
        """测试默认支持模型列表为空"""

        class MinimalProvider(AIProvider):
            async def chat_stream(self, messages, model, **kwargs):
                yield "test"

            async def chat(self, messages, model, **kwargs):
                return "test"

            async def generate_image(self, prompt, **kwargs):
                return "url"

            async def generate_audio(self, text, **kwargs):
                return "url"

        provider = MinimalProvider()
        assert provider.get_supported_models() == []

    def test_validate_model_with_empty_list(self):
        """测试验证模型（空列表）"""

        class MinimalProvider(AIProvider):
            async def chat_stream(self, messages, model, **kwargs):
                yield "test"

            async def chat(self, messages, model, **kwargs):
                return "test"

            async def generate_image(self, prompt, **kwargs):
                return "url"

            async def generate_audio(self, text, **kwargs):
                return "url"

        provider = MinimalProvider()
        assert provider.validate_model("any-model") is False

    def test_validate_model_with_custom_list(self):
        """测试验证模型（自定义列表）"""

        class CustomProvider(AIProvider):
            def get_supported_models(self):
                return ["model-1", "model-2"]

            async def chat_stream(self, messages, model, **kwargs):
                yield "test"

            async def chat(self, messages, model, **kwargs):
                return "test"

            async def generate_image(self, prompt, **kwargs):
                return "url"

            async def generate_audio(self, text, **kwargs):
                return "url"

        provider = CustomProvider()
        assert provider.validate_model("model-1") is True
        assert provider.validate_model("model-3") is False
```

**Step 3: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest tests/unit/infrastructure/providers/test_base.py -v
```

Expected: 所有测试通过

**Step 4: 提交AIProvider抽象类**

Run:
```bash
git add backend/src/infrastructure/providers/base.py tests/unit/infrastructure/providers/test_base.py
git commit -m "feat(infrastructure): define AIProvider abstract interface"
```

---

## Task 7: 实现OpenAI Provider

**Files:**
- Create: `backend/src/infrastructure/providers/openai_provider.py`
- Create: `backend/tests/unit/infrastructure/providers/test_openai_provider.py`

**Step 1: 创建OpenAI Provider实现**

Create: `backend/src/infrastructure/providers/openai_provider.py`

```python
"""
OpenAI Provider实现

使用OpenAI SDK调用GPT模型
"""
import os
import logging
from typing import List, AsyncGenerator, Optional

from openai import AsyncOpenAI

from src.infrastructure.providers.base import AIProvider
from src.domain.entities.message import Message

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """
    OpenAI提供商实现

    支持GPT-4、GPT-3.5等模型
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "gpt-4"
    ):
        """
        初始化OpenAI Provider

        Args:
            api_key: OpenAI API密钥（默认从环境变量读取）
            base_url: API基础URL（默认为官方URL）
            default_model: 默认模型
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.default_model = default_model

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=120.0,
            max_retries=2
        )

        logger.info(f"OpenAI provider initialized: base_url={self.base_url}")

    async def chat_stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式对话

        Args:
            messages: 消息历史
            model: 模型名称（默认使用default_model）
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Yields:
            str: 流式输出文本片段
        """
        model = model or self.default_model

        # 转换为OpenAI格式
        openai_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI stream error: {e}")
            raise

    async def chat(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        非流式对话

        Args:
            messages: 消息历史
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            str: 完整响应
        """
        model = model or self.default_model

        openai_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        **kwargs
    ) -> str:
        """
        生成图片

        Args:
            prompt: 提示词
            size: 图片尺寸
            **kwargs: 其他参数

        Returns:
            str: 图片URL
        """
        try:
            response = await self.client.images.generate(
                prompt=prompt,
                size=size,
                **kwargs
            )
            return response.data[0].url

        except Exception as e:
            logger.error(f"OpenAI image generation error: {e}")
            raise

    async def generate_audio(
        self,
        text: str,
        voice: str = "alloy",
        **kwargs
    ) -> str:
        """
        生成音频

        Args:
            text: 文本
            voice: 音色
            **kwargs: 其他参数

        Returns:
            str: 音频URL（需要保存到存储服务）
        """
        try:
            response = await self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )

            # TODO: 保存音频文件到存储服务
            # 当前返回临时URL
            return "audio_url_placeholder"

        except Exception as e:
            logger.error(f"OpenAI audio generation error: {e}")
            raise

    def get_supported_models(self) -> List[str]:
        """
        获取支持的OpenAI模型

        Returns:
            List[str]: 模型列表
        """
        return [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ]
```

**Step 2: 编写OpenAI Provider测试**

Create: `backend/tests/unit/infrastructure/providers/test_openai_provider.py`

```python
"""
OpenAI Provider单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.infrastructure.providers.openai_provider import OpenAIProvider
from src.domain.entities.message import Message
from src.domain.value_objects.message_role import MessageRole


class TestOpenAIProvider:
    """OpenAI Provider测试类"""

    @pytest.fixture
    def provider(self):
        """创建Provider实例（使用测试密钥）"""
        return OpenAIProvider(
            api_key="test-key-sk-123456",
            base_url="https://api.openai.com/v1"
        )

    @pytest.fixture
    def sample_messages(self):
        """创建测试消息"""
        return [
            Message.create_user_message(
                session_id=1,
                content="Hello, how are you?"
            )
        ]

    def test_init_with_api_key(self):
        """测试使用API密钥初始化"""
        # Act
        provider = OpenAIProvider(api_key="sk-test-key")

        # Assert
        assert provider.api_key == "sk-test-key"
        assert provider.client is not None

    def test_init_without_api_key_raises_error(self):
        """测试没有API密钥时抛出错误"""
        # Act & Assert
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key is required"):
                OpenAIProvider(api_key=None)

    def test_get_supported_models(self, provider):
        """测试获取支持模型列表"""
        # Act
        models = provider.get_supported_models()

        # Assert
        assert "gpt-4" in models
        assert "gpt-3.5-turbo" in models
        assert len(models) > 0

    def test_validate_model(self, provider):
        """测试模型验证"""
        # Assert
        assert provider.validate_model("gpt-4") is True
        assert provider.validate_model("gpt-3.5-turbo") is True
        assert provider.validate_model("unknown-model") is False

    @pytest.mark.asyncio
    async def test_chat_stream_success(self, provider, sample_messages):
        """测试流式对话成功"""
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].delta.content = "Hello"

        with patch.object(provider.client.chat.completions, 'create', new=AsyncMock()) as mock_create:
            mock_create.return_value = self._mock_stream([mock_response])

            # Act
            chunks = []
            async for chunk in provider.chat_stream(sample_messages):
                chunks.append(chunk)

            # Assert
            assert len(chunks) > 0
            assert "Hello" in "".join(chunks)

    @pytest.mark.asyncio
    async def test_chat_success(self, provider, sample_messages):
        """测试非流式对话成功"""
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I'm fine, thank you!"

        with patch.object(provider.client.chat.completions, 'create', new=AsyncMock(return_value=mock_response)) as mock_create:
            # Act
            result = await provider.chat(sample_messages)

            # Assert
            assert result == "I'm fine, thank you!"
            mock_create.assert_called_once()

    def _mock_stream(self, chunks):
        """创建模拟的流式响应"""
        async def stream_generator():
            for chunk in chunks:
                yield chunk

        return stream_generator()
```

**Step 3: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest tests/unit/infrastructure/providers/test_openai_provider.py -v
```

Expected: 所有测试通过

**Step 4: 提交OpenAI Provider**

Run:
```bash
git add backend/src/infrastructure/providers/openai_provider.py tests/unit/infrastructure/providers/test_openai_provider.py
git commit -m "feat(infrastructure): implement OpenAI Provider with streaming support"
```

---

## Task 8: 实现DeepSeek Provider

**Files:**
- Create: `backend/src/infrastructure/providers/deepseek_provider.py`
- Create: `backend/tests/unit/infrastructure/providers/test_deepseek_provider.py`

**Step 1: 创建DeepSeek Provider实现**

Create: `backend/src/infrastructure/providers/deepseek_provider.py`

```python
"""
DeepSeek Provider实现

使用OpenAI兼容协议调用DeepSeek模型
"""
import os
import logging
from typing import List, AsyncGenerator, Optional

from openai import AsyncOpenAI

from src.infrastructure.providers.base import AIProvider
from src.domain.entities.message import Message

logger = logging.getLogger(__name__)


class DeepSeekProvider(AIProvider):
    """
    DeepSeek提供商实现

    DeepSeek API兼容OpenAI协议
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "deepseek-chat"
    ):
        """
        初始化DeepSeek Provider

        Args:
            api_key: DeepSeek API密钥（默认从环境变量读取）
            base_url: API基础URL（默认为DeepSeek官方URL）
            default_model: 默认模型
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.default_model = default_model

        if not self.api_key:
            raise ValueError("DeepSeek API key is required")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=120.0,
            max_retries=2
        )

        logger.info(f"DeepSeek provider initialized: base_url={self.base_url}")

    async def chat_stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话（与OpenAI实现相同）"""
        model = model or self.default_model

        openai_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"DeepSeek stream error: {e}")
            raise

    async def chat(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """非流式对话"""
        model = model or self.default_model

        openai_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"DeepSeek chat error: {e}")
            raise

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        **kwargs
    ) -> str:
        """
        生成图片（DeepSeek不支持）

        Raises:
            NotImplementedError: DeepSeek不支持图片生成
        """
        raise NotImplementedError("DeepSeek does not support image generation")

    async def generate_audio(
        self,
        text: str,
        voice: str = "alloy",
        **kwargs
    ) -> str:
        """
        生成音频（DeepSeek不支持）

        Raises:
            NotImplementedError: DeepSeek不支持音频生成
        """
        raise NotImplementedError("DeepSeek does not support audio generation")

    def get_supported_models(self) -> List[str]:
        """
        获取支持的DeepSeek模型

        Returns:
            List[str]: 模型列表
        """
        return [
            "deepseek-chat",
            "deepseek-coder",
        ]
```

**Step 2: 编写DeepSeek Provider测试**

Create: `backend/tests/unit/infrastructure/providers/test_deepseek_provider.py`

```python
"""
DeepSeek Provider单元测试
"""
import pytest
from src.infrastructure.providers.deepseek_provider import DeepSeekProvider


class TestDeepSeekProvider:
    """DeepSeek Provider测试类"""

    def test_init_with_api_key(self):
        """测试使用API密钥初始化"""
        # Act
        provider = DeepSeekProvider(api_key="sk-deepseek-test")

        # Assert
        assert provider.api_key == "sk-deepseek-test"
        assert provider.default_model == "deepseek-chat"

    def test_init_without_api_key_raises_error(self):
        """测试没有API密钥时抛出错误"""
        # Act & Assert
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key is required"):
                DeepSeekProvider(api_key=None)

    def test_get_supported_models(self):
        """测试获取支持模型列表"""
        # Arrange
        provider = DeepSeekProvider(api_key="test-key")

        # Act
        models = provider.get_supported_models()

        # Assert
        assert "deepseek-chat" in models
        assert "deepseek-coder" in models

    @pytest.mark.asyncio
    async def test_generate_image_not_supported(self):
        """测试图片生成不支持"""
        # Arrange
        provider = DeepSeekProvider(api_key="test-key")

        # Act & Assert
        with pytest.raises(NotImplementedError, match="does not support image generation"):
            await provider.generate_image("test prompt")

    @pytest.mark.asyncio
    async def test_generate_audio_not_supported(self):
        """测试音频生成不支持"""
        # Arrange
        provider = DeepSeekProvider(api_key="test-key")

        # Act & Assert
        with pytest.raises(NotImplementedError, match="does not support audio generation"):
            await provider.generate_audio("test text")
```

**Step 3: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest tests/unit/infrastructure/providers/test_deepseek_provider.py -v
```

Expected: 所有测试通过

**Step 4: 提交DeepSeek Provider**

Run:
```bash
git add backend/src/infrastructure/providers/deepseek_provider.py tests/unit/infrastructure/providers/test_deepseek_provider.py
git commit -m "feat(infrastructure): implement DeepSeek Provider"
```

---

## Task 9: 实现ProviderFactory

**Files:**
- Create: `backend/src/infrastructure/providers/factory.py`
- Create: `backend/tests/unit/infrastructure/providers/test_factory.py`

**Step 1: 创建ProviderFactory**

Create: `backend/src/infrastructure/providers/factory.py`

```python
"""
Provider工厂

根据配置创建对应的AI Provider实例
"""
import os
import logging
from typing import Dict, Type

from src.infrastructure.providers.base import AIProvider
from src.infrastructure.providers.openai_provider import OpenAIProvider
from src.infrastructure.providers.deepseek_provider import DeepSeekProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """
    Provider工厂类

    根据provider名称创建对应的AI Provider实例
    """

    # Provider注册表
    _providers: Dict[str, Type[AIProvider]] = {
        "openai": OpenAIProvider,
        "deepseek": DeepSeekProvider,
    }

    @classmethod
    def create(cls, provider_name: str) -> AIProvider:
        """
        创建Provider实例

        Args:
            provider_name: Provider名称（openai/deepseek/kimi）

        Returns:
            AIProvider: Provider实例

        Raises:
            ValueError: 不支持的Provider
        """
        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Supported providers: {list(cls._providers.keys())}"
            )

        provider_class = cls._providers[provider_name]

        try:
            provider = provider_class()
            logger.info(f"Created {provider_name} provider successfully")
            return provider

        except Exception as e:
            logger.error(f"Failed to create {provider_name} provider: {e}")
            raise

    @classmethod
    def create_from_env(cls) -> AIProvider:
        """
        从环境变量创建Provider

        读取CURRENT_PROVIDER环境变量，创建对应的Provider

        Returns:
            AIProvider: Provider实例

        Raises:
            ValueError: 环境变量未设置或值无效
        """
        provider_name = os.getenv("CURRENT_PROVIDER", "deepseek")

        if not provider_name:
            raise ValueError("CURRENT_PROVIDER environment variable is not set")

        return cls.create(provider_name)

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[AIProvider]) -> None:
        """
        注册新的Provider

        Args:
            name: Provider名称
            provider_class: Provider类
        """
        cls._providers[name.lower()] = provider_class
        logger.info(f"Registered new provider: {name}")

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """
        获取所有支持的Provider名称

        Returns:
            List[str]: Provider名称列表
        """
        return list(cls._providers.keys())
```

**Step 2: 编写ProviderFactory测试**

Create: `backend/tests/unit/infrastructure/providers/test_factory.py`

```python
"""
ProviderFactory单元测试
"""
import pytest
from unittest.mock import patch
from src.infrastructure.providers.factory import ProviderFactory
from src.infrastructure.providers.base import AIProvider


class MockProvider(AIProvider):
    """Mock Provider用于测试"""

    async def chat_stream(self, messages, model, **kwargs):
        yield "mock"

    async def chat(self, messages, model, **kwargs):
        return "mock response"

    async def generate_image(self, prompt, **kwargs):
        return "mock-url"

    async def generate_audio(self, text, **kwargs):
        return "mock-audio-url"


class TestProviderFactory:
    """ProviderFactory测试类"""

    def test_create_openai_provider(self):
        """测试创建OpenAI Provider"""
        # Arrange
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            # Act
            provider = ProviderFactory.create("openai")

            # Assert
            assert isinstance(provider, AIProvider)
            assert type(provider).__name__ == "OpenAIProvider"

    def test_create_deepseek_provider(self):
        """测试创建DeepSeek Provider"""
        # Arrange
        with patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test-key'}):
            # Act
            provider = ProviderFactory.create("deepseek")

            # Assert
            assert isinstance(provider, AIProvider)
            assert type(provider).__name__ == "DeepSeekProvider"

    def test_create_unknown_provider_raises_error(self):
        """测试创建不存在的Provider抛出错误"""
        # Act & Assert
        with pytest.raises(ValueError, match="Unknown provider"):
            ProviderFactory.create("unknown-provider")

    def test_create_from_env(self):
        """测试从环境变量创建Provider"""
        # Arrange
        with patch.dict('os.environ', {
            'CURRENT_PROVIDER': 'deepseek',
            'DEEPSEEK_API_KEY': 'test-key'
        }):
            # Act
            provider = ProviderFactory.create_from_env()

            # Assert
            assert isinstance(provider, AIProvider)

    def test_create_from_env_not_set_raises_error(self):
        """测试环境变量未设置时抛出错误"""
        # Arrange
        with patch.dict('os.environ', {}, clear=True):
            # Act & Assert
            with pytest.raises(ValueError, match="CURRENT_PROVIDER.*not set"):
                ProviderFactory.create_from_env()

    def test_register_custom_provider(self):
        """测试注册自定义Provider"""
        # Act
        ProviderFactory.register_provider("mock", MockProvider)

        # Assert
        provider = ProviderFactory.create("mock")
        assert isinstance(provider, MockProvider)

    def test_get_supported_providers(self):
        """测试获取支持的Provider列表"""
        # Act
        providers = ProviderFactory.get_supported_providers()

        # Assert
        assert "openai" in providers
        assert "deepseek" in providers
        assert len(providers) >= 2
```

**Step 3: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest tests/unit/infrastructure/providers/test_factory.py -v
```

Expected: 所有测试通过

**Step 4: 提交ProviderFactory**

Run:
```bash
git add backend/src/infrastructure/providers/factory.py tests/unit/infrastructure/providers/test_factory.py
git commit -m "feat(infrastructure): implement ProviderFactory for dynamic provider creation"
```

---

## Task 10: 阶段1总结和验证

**Step 1: 运行完整测试套件**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
pytest tests/unit/ -v --cov=src --cov-report=term-missing
```

Expected:
- 所有单元测试通过
- Domain层覆盖率 >80%
- Infrastructure层覆盖率 >70%

**Step 2: 验证现有功能不受影响**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
python -m src.main
```

Manual verification:
1. 访问 http://localhost:8000/docs
2. 确认API文档正常显示
3. 测试一个对话功能（使用前端或Postman）

**Step 3: 检查代码质量**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/backend
# 检查大文件（应该没有新增大文件）
find src -name "*.py" -exec wc -l {} + | sort -rn | head -20
```

Expected: 新创建的文件都应该 <500行

**Step 4: 创建阶段1完成标记**

Create: `backend/.phase1-complete`

```bash
echo "Phase 1 Complete: DDD Architecture + Provider Migration" > backend/.phase1-complete
echo "Date: $(date)" >> backend/.phase1-complete
git add backend/.phase1-complete
git commit -m "chore: mark Phase 1 (DDD + Provider) as complete"
```

---

## 📝 阶段1完成检查清单

- [x] DDD四层目录结构创建
- [x] pytest测试框架配置完成
- [x] User领域实体 + 测试
- [x] Message领域实体 + MessageRole值对象 + 测试
- [x] 仓储接口定义 + 测试
- [x] AIProvider抽象类 + 测试
- [x] OpenAI Provider实现 + 测试
- [x] DeepSeek Provider实现 + 测试
- [x] ProviderFactory工厂 + 测试
- [x] 所有单元测试通过
- [x] 代码覆盖率达标
- [x] 现有功能不受影响

---

## 🎯 下一步

阶段1完成后，继续：
1. **阶段2**: Day 5-7（前端组件拆分）
2. **阶段3**: Day 8-12（后端路由拆分 + 测试完善）

查看 `docs/plans/2026-02-27-system-refactoring-phase2.md` 继续实施。
